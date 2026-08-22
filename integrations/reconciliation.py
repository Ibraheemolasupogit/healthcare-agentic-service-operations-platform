"""Deterministic reconciliation checks for integration delivery evidence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ReconciliationCase:
    """One reconciliation finding."""

    check_id: str
    severity: str
    canonical_case_id: str
    correlation_id: str
    finding: str
    recommended_action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "severity": self.severity,
            "canonical_case_id": self.canonical_case_id,
            "correlation_id": self.correlation_id,
            "finding": self.finding,
            "recommended_action": self.recommended_action,
        }


def reconcile_deliveries(
    *,
    delivery_traces: tuple[dict[str, Any], ...],
    crm_record_map: dict[str, str],
) -> tuple[ReconciliationCase, ...]:
    """Detect compact integration consistency issues from synthetic traces."""
    findings: list[ReconciliationCase] = []
    external_to_case: dict[str, str] = {}
    for trace in delivery_traces:
        envelope = trace["envelope"]
        delivery = trace["delivery"]
        case_id = envelope["canonical_case_id"]
        correlation_id = envelope["correlation_id"]
        external_id = crm_record_map.get(case_id)
        if delivery["state"] in {"dead_lettered", "failed", "retry_pending"}:
            findings.append(
                ReconciliationCase(
                    "undelivered-envelope",
                    "error",
                    case_id,
                    correlation_id,
                    f"Delivery state is {delivery['state']}",
                    "Send to manual review and retry after root cause is corrected.",
                )
            )
        if delivery["state"] == "delivered" and not external_id:
            findings.append(
                ReconciliationCase(
                    "crm-representation-missing",
                    "warning",
                    case_id,
                    correlation_id,
                    "Delivery succeeded but no CRM representation is mapped.",
                    "Run downstream CRM lookup before declaring synchronisation complete.",
                )
            )
        if external_id:
            previous = external_to_case.get(external_id)
            if previous and previous != case_id:
                findings.append(
                    ReconciliationCase(
                        "duplicate-external-record-mapping",
                        "error",
                        case_id,
                        correlation_id,
                        f"External record {external_id} is mapped to {previous} and {case_id}.",
                        "Quarantine mapping and resolve canonical/external identity conflict.",
                    )
                )
            external_to_case[external_id] = case_id
        if delivery["correlation_id"] != correlation_id:
            findings.append(
                ReconciliationCase(
                    "correlation-mismatch",
                    "error",
                    case_id,
                    correlation_id,
                    "Envelope and delivery correlation ids differ.",
                    "Preserve original correlation id across retry and provider hops.",
                )
            )
    return tuple(findings)


__all__ = ["ReconciliationCase", "reconcile_deliveries"]
