"""Lightweight analytical data-quality checks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from analytics.fabric.silver import SilverModel
from business_process import CaseStage, Priority, ServiceCategory


@dataclass(frozen=True, slots=True)
class DataQualityIssue:
    """One data-quality issue."""

    check_id: str
    severity: str
    entity: str
    record_id: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "severity": self.severity,
            "entity": self.entity,
            "record_id": self.record_id,
            "message": self.message,
        }


def _valid_timestamp(value: str) -> bool:
    try:
        datetime.fromisoformat(value)
        return True
    except ValueError:
        return False


def run_data_quality_checks(silver: SilverModel) -> tuple[DataQualityIssue, ...]:
    """Run deterministic data-quality checks over conformed analytics entities."""
    issues: list[DataQualityIssue] = []
    case_ids: set[str] = set()
    valid_categories = {category.value for category in ServiceCategory}
    valid_priorities = {priority.value for priority in Priority}
    valid_statuses = {stage.value for stage in CaseStage}
    known_queues = {queue["queue"] for queue in silver.queues}

    for case in silver.service_cases:
        case_id = str(case.get("case_id") or "")
        if not case_id:
            issues.append(
                DataQualityIssue("required-case-id", "error", "service_case", "", "Missing case_id")
            )
            continue
        if case_id in case_ids:
            issues.append(
                DataQualityIssue(
                    "duplicate-case-id", "error", "service_case", case_id, "Duplicate case_id"
                )
            )
        case_ids.add(case_id)
        if case["category"] not in valid_categories:
            issues.append(
                DataQualityIssue(
                    "valid-category", "error", "service_case", case_id, "Unknown category"
                )
            )
        if case["priority"] not in valid_priorities:
            issues.append(
                DataQualityIssue(
                    "valid-priority", "error", "service_case", case_id, "Unknown priority"
                )
            )
        if case["status"] not in valid_statuses:
            issues.append(
                DataQualityIssue("valid-status", "error", "service_case", case_id, "Unknown status")
            )
        if case["queue"] not in known_queues:
            issues.append(
                DataQualityIssue("known-queue", "error", "service_case", case_id, "Unknown queue")
            )
        if not _valid_timestamp(case["created_at"]) or not _valid_timestamp(case["updated_at"]):
            issues.append(
                DataQualityIssue(
                    "valid-timestamp", "error", "service_case", case_id, "Bad timestamp"
                )
            )
        if case["resolution_minutes"] is not None and case["resolution_minutes"] < 0:
            issues.append(
                DataQualityIssue(
                    "non-negative-duration",
                    "error",
                    "service_case",
                    case_id,
                    "Negative resolution duration",
                )
            )

    for event in silver.lifecycle_events:
        case_id = str(event.get("case_id") or "")
        if case_id not in case_ids:
            issues.append(
                DataQualityIssue(
                    "event-case-integrity",
                    "error",
                    "lifecycle_event",
                    case_id,
                    "Event references unknown case",
                )
            )
        if not event.get("timestamp") or not _valid_timestamp(event["timestamp"]):
            issues.append(
                DataQualityIssue(
                    "event-timestamp", "error", "lifecycle_event", case_id, "Missing/bad timestamp"
                )
            )

    for execution in silver.automation_executions:
        if not execution.get("correlation_id"):
            issues.append(
                DataQualityIssue(
                    "automation-correlation",
                    "error",
                    "automation_execution",
                    execution["flow_id"],
                    "Missing correlation id",
                )
            )

    for interaction in silver.agent_interactions:
        if not interaction.get("correlation_id"):
            issues.append(
                DataQualityIssue(
                    "agent-correlation",
                    "error",
                    "agent_interaction",
                    interaction["tool_name"],
                    "Missing correlation id",
                )
            )

    for approval in silver.approval_decisions:
        if approval["case_id"] not in case_ids:
            issues.append(
                DataQualityIssue(
                    "approval-case-integrity",
                    "error",
                    "approval_decision",
                    approval["approval_id"],
                    "Approval references unknown case",
                )
            )
        if not approval.get("correlation_id"):
            issues.append(
                DataQualityIssue(
                    "approval-correlation",
                    "error",
                    "approval_decision",
                    approval["approval_id"],
                    "Missing correlation id",
                )
            )

    for delivery in silver.integration_deliveries:
        if not delivery.get("correlation_id"):
            issues.append(
                DataQualityIssue(
                    "integration-correlation",
                    "error",
                    "integration_delivery",
                    delivery["envelope_id"],
                    "Missing correlation id",
                )
            )
        if not delivery.get("idempotency_key"):
            issues.append(
                DataQualityIssue(
                    "integration-idempotency",
                    "error",
                    "integration_delivery",
                    delivery["envelope_id"],
                    "Missing idempotency key",
                )
            )
    return tuple(issues)


__all__ = ["DataQualityIssue", "run_data_quality_checks"]
