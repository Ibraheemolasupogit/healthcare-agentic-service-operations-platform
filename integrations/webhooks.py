"""Local/reference webhook/API processor around `IntegrationEnvelope`."""

from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import UTC, datetime

from integrations.delivery import DeliveryRecord, DeliveryState
from integrations.envelope import IntegrationEnvelope, IntegrationOperation, envelope_to_dict
from integrations.idempotency import IdempotencyStore, derive_idempotency_key
from integrations.retry import NonRetryableTransportError, RetryPolicy
from integrations.security import IntegrationPrincipal, authorize_envelope
from integrations.transport import OutboundTransport

SUPPORTED_SCHEMA_VERSION = "1.0"
ALLOWED_OPERATIONS = frozenset(operation.value for operation in IntegrationOperation)
_ENVELOPE_NAMESPACE = uuid.uuid5(
    uuid.NAMESPACE_DNS, "integration-envelope.healthcare-agentic-service-operations-platform"
)


def deterministic_envelope_id(envelope: IntegrationEnvelope) -> str:
    """Return a stable envelope id when a caller does not provide one."""
    seed = "|".join(
        [
            envelope.source_system.value,
            envelope.source_record_id,
            envelope.canonical_case_id,
            envelope.correlation_id,
            envelope.operation.value,
        ]
    )
    return str(uuid.uuid5(_ENVELOPE_NAMESPACE, seed))


def validate_envelope(envelope: IntegrationEnvelope) -> None:
    """Validate envelope shape only; do not validate canonical business rules."""
    if envelope.schema_version != SUPPORTED_SCHEMA_VERSION:
        raise NonRetryableTransportError(f"unsupported schema_version {envelope.schema_version}")
    if envelope.operation.value not in ALLOWED_OPERATIONS:
        raise NonRetryableTransportError(f"unsupported operation {envelope.operation.value}")
    for field_name in ("source_record_id", "canonical_case_id", "correlation_id"):
        if not getattr(envelope, field_name):
            raise NonRetryableTransportError(f"missing {field_name}")


class WebhookProcessor:
    """Validate, deduplicate, dispatch, retry, and observe one envelope."""

    def __init__(
        self,
        *,
        idempotency_store: IdempotencyStore,
        transport: OutboundTransport,
        retry_policy: RetryPolicy | None = None,
        now: datetime | None = None,
    ) -> None:
        self.idempotency_store = idempotency_store
        self.transport = transport
        self.retry_policy = retry_policy or RetryPolicy()
        self.now = now or datetime.now(UTC)

    def process(
        self, envelope: IntegrationEnvelope, *, principal: IntegrationPrincipal
    ) -> DeliveryRecord:
        """Process one inbound delivery without making live external calls."""
        envelope = self._normalise(envelope)
        idempotency_key = envelope.idempotency_key or derive_idempotency_key(
            source_system=envelope.source_system.value,
            source_record_id=envelope.source_record_id,
            operation=envelope.operation.value,
            target_system=envelope.target_system.value if envelope.target_system else "canonical",
        )
        envelope = replace(envelope, idempotency_key=idempotency_key)
        duplicate = self.idempotency_store.completed_duplicate(idempotency_key)
        if duplicate is not None:
            return self._record(
                envelope,
                state=DeliveryState.DUPLICATE,
                attempts=0,
                outcome=f"duplicate suppressed; original={duplicate.envelope_id}",
            )

        try:
            validate_envelope(envelope)
            authorize_envelope(envelope, principal)
        except (NonRetryableTransportError, PermissionError) as exc:
            delivery = self._record(
                envelope,
                state=DeliveryState.FAILED,
                attempts=0,
                outcome="non-retryable validation/auth failure",
                error=str(exc),
                retryable=False,
            )
            self.idempotency_store.record(delivery)
            return delivery

        attempt = 1
        while True:
            try:
                receipt = self.transport.send(envelope, attempt=attempt)
            except Exception as exc:
                if self.retry_policy.should_retry(attempt=attempt, error=exc):
                    attempt += 1
                    continue
                state = (
                    DeliveryState.DEAD_LETTERED
                    if isinstance(exc, Exception) and attempt >= self.retry_policy.max_attempts
                    else DeliveryState.FAILED
                )
                delivery = self._record(
                    envelope,
                    state=state,
                    attempts=attempt,
                    outcome="delivery failed; manual review required"
                    if state is DeliveryState.DEAD_LETTERED
                    else "delivery failed",
                    error=str(exc),
                    retryable=False,
                    manual_review_required=state is DeliveryState.DEAD_LETTERED,
                )
                self.idempotency_store.record(delivery)
                return delivery

            delivery = self._record(
                envelope,
                state=DeliveryState.DELIVERED,
                attempts=attempt,
                outcome=f"delivered via local stub transport; receipt={receipt}",
            )
            self.idempotency_store.record(delivery)
            return delivery

    def _normalise(self, envelope: IntegrationEnvelope) -> IntegrationEnvelope:
        if envelope.envelope_id and envelope.idempotency_key:
            return envelope
        return replace(
            envelope,
            envelope_id=envelope.envelope_id or deterministic_envelope_id(envelope),
            trace=envelope.trace or {"traceparent": self._traceparent(envelope.correlation_id)},
        )

    @staticmethod
    def _traceparent(correlation_id: str) -> str:
        trace_id = correlation_id.replace("-", "")[:32]
        return f"00-{trace_id}-0000000000000001-01"

    def _record(
        self,
        envelope: IntegrationEnvelope,
        *,
        state: DeliveryState,
        attempts: int,
        outcome: str,
        error: str | None = None,
        retryable: bool = False,
        manual_review_required: bool = False,
    ) -> DeliveryRecord:
        target = envelope.target_system.value if envelope.target_system else "canonical"
        next_backoff = (
            self.retry_policy.backoff_seconds(attempts)
            if state is DeliveryState.RETRY_PENDING
            else None
        )
        return DeliveryRecord(
            envelope_id=envelope.envelope_id or deterministic_envelope_id(envelope),
            idempotency_key=envelope.idempotency_key
            or derive_idempotency_key(
                source_system=envelope.source_system.value,
                source_record_id=envelope.source_record_id,
                operation=envelope.operation.value,
                target_system=target,
            ),
            correlation_id=envelope.correlation_id,
            source_system=envelope.source_system.value,
            target_system=target,
            operation=envelope.operation.value,
            state=state,
            attempts=attempts,
            created_at=self.now,
            updated_at=self.now,
            outcome=outcome,
            error=error,
            retryable=retryable,
            next_backoff_seconds=next_backoff,
            manual_review_required=manual_review_required,
        )


def envelope_trace_event(
    envelope: IntegrationEnvelope, delivery: DeliveryRecord
) -> dict[str, object]:
    """Build one structured observability event for evidence and analytics."""
    return {
        "event_type": "integration_delivery",
        "envelope": envelope_to_dict(envelope),
        "delivery": delivery.to_dict(),
        "synthetic": True,
        "note": "Deterministic reference event; not live webhook or monitoring telemetry.",
    }


__all__ = [
    "ALLOWED_OPERATIONS",
    "SUPPORTED_SCHEMA_VERSION",
    "WebhookProcessor",
    "deterministic_envelope_id",
    "envelope_trace_event",
    "validate_envelope",
]
