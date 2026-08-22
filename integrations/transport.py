"""Provider-neutral outbound transport stubs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from integrations.envelope import IntegrationEnvelope
from integrations.retry import NonRetryableTransportError, RetryableTransportError


class OutboundTransport(Protocol):
    """Minimal outbound transport boundary for future CRM/Power Platform providers."""

    def send(self, envelope: IntegrationEnvelope, *, attempt: int) -> str:
        """Send one envelope and return a provider-neutral receipt id."""


@dataclass(slots=True)
class StubOutboundTransport:
    """Deterministic local transport; makes no network calls."""

    failures_before_success: dict[str, int] = field(default_factory=dict)
    non_retryable_keys: frozenset[str] = frozenset()
    receipts: list[str] = field(default_factory=list)

    def send(self, envelope: IntegrationEnvelope, *, attempt: int) -> str:
        key = envelope.idempotency_key or envelope.source_record_id
        if key in self.non_retryable_keys:
            raise NonRetryableTransportError(f"non-retryable transport rejection for {key}")
        failures = self.failures_before_success.get(key, 0)
        if attempt <= failures:
            raise RetryableTransportError(f"transient transport failure for {key}")
        receipt = f"stub-receipt:{envelope.correlation_id}:{attempt}"
        self.receipts.append(receipt)
        return receipt


__all__ = ["OutboundTransport", "StubOutboundTransport"]
