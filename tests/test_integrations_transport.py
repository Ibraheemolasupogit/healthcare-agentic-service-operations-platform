"""Tests for Milestone 7 integration transport, reliability, and observability."""

import json
from datetime import UTC, datetime

import pytest

from integrations.delivery import DeliveryState, is_valid_delivery_transition
from integrations.envelope import IntegrationEnvelope, IntegrationOperation, SourceSystem
from integrations.evidence import build_synthetic_integration_evidence, generate_all
from integrations.idempotency import IdempotencyStore, derive_idempotency_key
from integrations.observability import build_integration_metrics
from integrations.retry import NonRetryableTransportError, RetryPolicy
from integrations.security import IntegrationPrincipal
from integrations.transport import StubOutboundTransport
from integrations.webhooks import WebhookProcessor, deterministic_envelope_id, validate_envelope

_NOW = datetime(2026, 1, 12, 15, 0, tzinfo=UTC)


def _principal(source_system: SourceSystem = SourceSystem.EXTERNAL) -> IntegrationPrincipal:
    return IntegrationPrincipal(
        principal_id="external-reference-principal",
        source_system=source_system.value,
        audience="healthcare-service-operations-integrations",
        environment="test",
        scopes=frozenset({"integration:deliver"}),
    )


def _envelope(**overrides) -> IntegrationEnvelope:
    defaults = dict(
        source_system=SourceSystem.EXTERNAL,
        source_record_id="EXT-1001",
        canonical_case_id="SR-DS-1001",
        correlation_id="corr-transport-1",
        schema_version="1.0",
        timestamp=_NOW,
        operation=IntegrationOperation.CREATE,
        target_system=SourceSystem.CANONICAL,
        idempotency_key="external:EXT-1001:create:business_process",
    )
    defaults.update(overrides)
    return IntegrationEnvelope(**defaults)


def test_envelope_validation_accepts_supported_schema_and_version():
    validate_envelope(_envelope())


def test_envelope_validation_rejects_unknown_schema_version():
    with pytest.raises(NonRetryableTransportError, match="unsupported schema_version"):
        validate_envelope(_envelope(schema_version="0.9"))


def test_deterministic_envelope_id_and_idempotency_key_are_stable():
    envelope = _envelope(envelope_id=None)
    assert deterministic_envelope_id(envelope) == deterministic_envelope_id(envelope)
    assert (
        derive_idempotency_key(
            source_system="external",
            source_record_id="EXT-1001",
            operation="create",
            target_system="business_process",
        )
        == "external:EXT-1001:create:business_process"
    )


def test_webhook_processor_delivers_first_request_and_suppresses_duplicate():
    store = IdempotencyStore()
    transport = StubOutboundTransport()
    processor = WebhookProcessor(idempotency_store=store, transport=transport, now=_NOW)
    envelope = _envelope()

    first = processor.process(envelope, principal=_principal())
    second = processor.process(envelope, principal=_principal())

    assert first.state is DeliveryState.DELIVERED
    assert first.attempts == 1
    assert second.state is DeliveryState.DUPLICATE
    assert second.attempts == 0
    assert len(transport.receipts) == 1


def test_retry_policy_retries_transient_failure_without_sleeping():
    key = "external:EXT-1001:create:business_process"
    transport = StubOutboundTransport(failures_before_success={key: 1})
    processor = WebhookProcessor(
        idempotency_store=IdempotencyStore(),
        transport=transport,
        retry_policy=RetryPolicy(max_attempts=3, base_delay_seconds=10),
        now=_NOW,
    )

    delivery = processor.process(_envelope(idempotency_key=key), principal=_principal())

    assert delivery.state is DeliveryState.DELIVERED
    assert delivery.attempts == 2
    assert RetryPolicy(base_delay_seconds=10).backoff_seconds(2) == 20


def test_exhausted_retries_dead_letters_for_manual_review():
    key = "external:EXT-1001:create:business_process"
    transport = StubOutboundTransport(failures_before_success={key: 5})
    processor = WebhookProcessor(
        idempotency_store=IdempotencyStore(),
        transport=transport,
        retry_policy=RetryPolicy(max_attempts=3),
        now=_NOW,
    )

    delivery = processor.process(_envelope(idempotency_key=key), principal=_principal())

    assert delivery.state is DeliveryState.DEAD_LETTERED
    assert delivery.attempts == 3
    assert delivery.manual_review_required is True


def test_failed_delivery_can_be_retried_when_underlying_transport_recovers():
    key = "external:EXT-1001:create:business_process"
    store = IdempotencyStore()
    failing = WebhookProcessor(
        idempotency_store=store,
        transport=StubOutboundTransport(failures_before_success={key: 5}),
        retry_policy=RetryPolicy(max_attempts=1),
        now=_NOW,
    )
    recovered = WebhookProcessor(
        idempotency_store=store,
        transport=StubOutboundTransport(),
        retry_policy=RetryPolicy(max_attempts=3),
        now=_NOW,
    )

    failed = failing.process(_envelope(idempotency_key=key), principal=_principal())
    retried = recovered.process(_envelope(idempotency_key=key), principal=_principal())

    assert failed.state is DeliveryState.DEAD_LETTERED
    assert retried.state is DeliveryState.DELIVERED


def test_authorization_requires_matching_source_audience_and_scope():
    bad_principal = IntegrationPrincipal(
        principal_id="bad",
        source_system="salesforce",
        audience="healthcare-service-operations-integrations",
        environment="test",
        scopes=frozenset({"integration:deliver"}),
    )
    processor = WebhookProcessor(
        idempotency_store=IdempotencyStore(), transport=StubOutboundTransport(), now=_NOW
    )

    delivery = processor.process(_envelope(), principal=bad_principal)

    assert delivery.state is DeliveryState.FAILED
    assert "does not match envelope" in (delivery.error or "")


def test_delivery_state_transitions_are_not_canonical_lifecycle_transitions():
    assert is_valid_delivery_transition(DeliveryState.RECEIVED, DeliveryState.VALIDATED)
    assert is_valid_delivery_transition(DeliveryState.RETRY_PENDING, DeliveryState.DEAD_LETTERED)
    assert not is_valid_delivery_transition(DeliveryState.DELIVERED, DeliveryState.PROCESSING)


def test_synthetic_evidence_covers_required_scenarios_and_metrics():
    evidence = build_synthetic_integration_evidence()
    scenarios = {trace["scenario"] for trace in evidence["traces"]}
    assert {
        "successful inbound delivery",
        "duplicate webhook",
        "transient outbound failure followed by successful retry",
        "non-retryable validation failure",
        "exhausted retries to dead-letter",
        "reconciliation detecting downstream inconsistency",
    } <= scenarios
    metrics = build_integration_metrics(tuple(evidence["traces"]))
    assert metrics["envelopes_received"] == 6
    assert metrics["duplicate_count"] == 1
    assert metrics["dead_letter_count"] == 1


def test_generate_all_writes_deterministic_integration_evidence(tmp_path):
    first = generate_all(data_dir=tmp_path / "a" / "data", reports_dir=tmp_path / "a" / "reports")
    second = generate_all(data_dir=tmp_path / "b" / "data", reports_dir=tmp_path / "b" / "reports")
    assert set(first) == {
        "integration_envelopes.json",
        "integration_delivery_traces.json",
        "reconciliation_cases.json",
        "integration_operations_summary.json",
        "reconciliation_report.md",
    }
    for name, path in first.items():
        assert path.is_file()
        if path.suffix == ".json":
            json.loads(path.read_text(encoding="utf-8"))
        assert path.read_text(encoding="utf-8") == second[name].read_text(encoding="utf-8")
