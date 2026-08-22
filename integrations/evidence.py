"""Deterministic Milestone 7 integration transport evidence."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from integrations.delivery import DeliveryRecord, DeliveryState
from integrations.envelope import (
    IntegrationEnvelope,
    IntegrationOperation,
    SourceSystem,
    envelope_to_dict,
    new_correlation_id,
)
from integrations.idempotency import IdempotencyStore
from integrations.observability import build_integration_metrics
from integrations.reconciliation import reconcile_deliveries
from integrations.retry import RetryPolicy
from integrations.security import IntegrationPrincipal
from integrations.transport import StubOutboundTransport
from integrations.webhooks import WebhookProcessor, envelope_trace_event

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = REPO_ROOT / "data" / "synthetic"
DEFAULT_REPORTS_DIR = REPO_ROOT / "reports"
_NOW = datetime(2026, 1, 12, 15, 0, tzinfo=UTC)


def _principal(source_system: SourceSystem) -> IntegrationPrincipal:
    return IntegrationPrincipal(
        principal_id=f"{source_system.value}-reference-principal",
        source_system=source_system.value,
        audience="healthcare-service-operations-integrations",
        environment="test",
        scopes=frozenset({"integration:deliver"}),
    )


def _envelope(
    *,
    source_system: SourceSystem,
    source_record_id: str,
    canonical_case_id: str,
    operation: IntegrationOperation,
    target_system: SourceSystem,
    schema_version: str = "1.0",
) -> IntegrationEnvelope:
    correlation_id = new_correlation_id(f"m7:{source_system.value}:{source_record_id}")
    return IntegrationEnvelope(
        source_system=source_system,
        source_record_id=source_record_id,
        canonical_case_id=canonical_case_id,
        correlation_id=correlation_id,
        schema_version=schema_version,
        timestamp=_NOW,
        operation=operation,
        target_system=target_system,
        causation_id="synthetic-m7-scenario",
        idempotency_key=f"{source_system.value}:{source_record_id}:{operation.value}:{target_system.value}",
    )


def build_synthetic_integration_evidence() -> dict[str, Any]:
    """Build deterministic integration transport scenarios."""
    policy = RetryPolicy(max_attempts=3, base_delay_seconds=30, max_delay_seconds=120)
    store = IdempotencyStore()
    transient_key = "power_platform:FLOW-RUN-1003:automation_event:dynamics365"
    dead_letter_key = "salesforce:500DEAD:sync:dynamics365"
    transport = StubOutboundTransport(
        failures_before_success={transient_key: 1, dead_letter_key: 5}
    )
    processor = WebhookProcessor(
        idempotency_store=store,
        transport=transport,
        retry_policy=policy,
        now=_NOW,
    )

    scenarios = [
        (
            "successful inbound delivery",
            _envelope(
                source_system=SourceSystem.EXTERNAL,
                source_record_id="EXT-1001",
                canonical_case_id="SR-DS-1001",
                operation=IntegrationOperation.CREATE,
                target_system=SourceSystem.CANONICAL,
            ),
            _principal(SourceSystem.EXTERNAL),
        ),
        (
            "duplicate webhook",
            _envelope(
                source_system=SourceSystem.EXTERNAL,
                source_record_id="EXT-1001",
                canonical_case_id="SR-DS-1001",
                operation=IntegrationOperation.CREATE,
                target_system=SourceSystem.CANONICAL,
            ),
            _principal(SourceSystem.EXTERNAL),
        ),
        (
            "transient outbound failure followed by successful retry",
            _envelope(
                source_system=SourceSystem.POWER_PLATFORM,
                source_record_id="FLOW-RUN-1003",
                canonical_case_id="SR-FA-1003",
                operation=IntegrationOperation.AUTOMATION_EVENT,
                target_system=SourceSystem.DYNAMICS_365,
            ),
            _principal(SourceSystem.POWER_PLATFORM),
        ),
        (
            "non-retryable validation failure",
            _envelope(
                source_system=SourceSystem.SALESFORCE,
                source_record_id="500BAD",
                canonical_case_id="SR-AI-1004",
                operation=IntegrationOperation.SYNC,
                target_system=SourceSystem.DYNAMICS_365,
                schema_version="0.9",
            ),
            _principal(SourceSystem.SALESFORCE),
        ),
        (
            "exhausted retries to dead-letter",
            _envelope(
                source_system=SourceSystem.SALESFORCE,
                source_record_id="500DEAD",
                canonical_case_id="SR-DR-1006",
                operation=IntegrationOperation.SYNC,
                target_system=SourceSystem.DYNAMICS_365,
            ),
            _principal(SourceSystem.SALESFORCE),
        ),
    ]

    traces: list[dict[str, Any]] = []
    envelopes: list[dict[str, Any]] = []
    for scenario_name, envelope, principal in scenarios:
        delivery = processor.process(envelope, principal=principal)
        traces.append(
            {
                **envelope_trace_event(envelope, delivery),
                "scenario": scenario_name,
                "retry_policy": {
                    "max_attempts": policy.max_attempts,
                    "base_delay_seconds": policy.base_delay_seconds,
                    "max_delay_seconds": policy.max_delay_seconds,
                },
            }
        )
        envelopes.append(envelope_to_dict(envelope))

    manual_mismatch = DeliveryRecord(
        envelope_id="synthetic-correlation-mismatch",
        idempotency_key="dynamics365:INC-MISMATCH:sync:salesforce",
        correlation_id="wrong-correlation-id",
        source_system="dynamics365",
        target_system="salesforce",
        operation="sync",
        state=DeliveryState.DELIVERED,
        attempts=1,
        created_at=_NOW,
        updated_at=_NOW,
        outcome="synthetic reconciliation-only inconsistency",
    )
    mismatch_envelope = _envelope(
        source_system=SourceSystem.DYNAMICS_365,
        source_record_id="INC-MISMATCH",
        canonical_case_id="SR-CE-1002",
        operation=IntegrationOperation.SYNC,
        target_system=SourceSystem.SALESFORCE,
    )
    traces.append(
        {
            **envelope_trace_event(mismatch_envelope, manual_mismatch),
            "scenario": "reconciliation detecting downstream inconsistency",
            "retry_policy": {
                "max_attempts": policy.max_attempts,
                "base_delay_seconds": policy.base_delay_seconds,
                "max_delay_seconds": policy.max_delay_seconds,
            },
        }
    )
    envelopes.append(envelope_to_dict(mismatch_envelope))

    reconciliation_cases = reconcile_deliveries(
        delivery_traces=tuple(traces),
        crm_record_map={
            "SR-DS-1001": "incident-sr-ds-1001",
            "SR-FA-1003": "incident-sr-fa-1003",
            "SR-CE-1002": "case-duplicate-001",
            "SR-DR-1006": "case-duplicate-001",
        },
    )
    summary = {
        "generated_from": "integrations.evidence (deterministic, synthetic)",
        "transport_scope": "local/reference only; no live webhook, API, broker, or SaaS call",
        "integration_metrics": build_integration_metrics(tuple(traces)),
        "scenario_count": len(traces),
        "reconciliation_finding_count": len(reconciliation_cases),
        "security_model": {
            "authentication": "conceptual service-to-service identity",
            "authorization": "audience/source/scope checks; no secrets or token issuance",
            "required_scope": "integration:deliver",
        },
        "note": (
            "Synthetic/reference integration transport evidence only. Not live Dynamics, "
            "Salesforce, Power Platform, Azure, or external SaaS telemetry."
        ),
    }
    return {
        "envelopes": envelopes,
        "traces": traces,
        "reconciliation_cases": [case.to_dict() for case in reconciliation_cases],
        "summary": summary,
    }


def build_reconciliation_report(reconciliation_cases: list[dict[str, Any]]) -> str:
    """Build concise Markdown reconciliation evidence."""
    lines = [
        "# Integration Reconciliation Report",
        "",
        "Synthetic/reference evidence only. This is not a live reconciliation job.",
        "",
        "| Check | Severity | Case | Correlation | Finding | Recommended action |",
        "|---|---|---|---|---|---|",
    ]
    for case in reconciliation_cases:
        lines.append(
            "| {check_id} | {severity} | {canonical_case_id} | {correlation_id} | "
            "{finding} | {recommended_action} |".format(**case)
        )
    lines.append("")
    lines.append(
        "The reconciliation layer detects delivery and representation inconsistencies only; "
        "it does not update canonical service state."
    )
    return "\n".join(lines) + "\n"


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def generate_all(
    *, data_dir: Path = DEFAULT_DATA_DIR, reports_dir: Path = DEFAULT_REPORTS_DIR
) -> dict[str, Path]:
    """Generate Milestone 7 deterministic integration evidence."""
    evidence = build_synthetic_integration_evidence()
    outputs: dict[Path, Any] = {
        data_dir / "integration_envelopes.json": evidence["envelopes"],
        data_dir / "integration_delivery_traces.json": evidence["traces"],
        data_dir / "reconciliation_cases.json": evidence["reconciliation_cases"],
        reports_dir / "integration_operations_summary.json": evidence["summary"],
    }
    for path, payload in outputs.items():
        _write_json(path, payload)
    reconciliation_report = reports_dir / "reconciliation_report.md"
    reconciliation_report.write_text(
        build_reconciliation_report(evidence["reconciliation_cases"]), encoding="utf-8"
    )
    outputs[reconciliation_report] = evidence["reconciliation_cases"]
    return {path.name: path for path in outputs}


if __name__ == "__main__":  # pragma: no cover
    for name, path in generate_all().items():
        print(f"wrote {name} -> {path}")


__all__ = [
    "build_reconciliation_report",
    "build_synthetic_integration_evidence",
    "generate_all",
]
