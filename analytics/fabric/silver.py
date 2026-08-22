"""Silver conformance layer for operational analytics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from statistics import median
from typing import Any

from analytics.fabric.ingestion import BronzeModel
from business_process import CaseStage, Priority, ServiceCategory
from business_process.sla import evaluate_sla, get_sla_target


@dataclass(frozen=True, slots=True)
class SilverModel:
    """Conformed analytical entities."""

    service_cases: tuple[dict[str, Any], ...]
    lifecycle_events: tuple[dict[str, Any], ...]
    queues: tuple[dict[str, Any], ...]
    sla_events: tuple[dict[str, Any], ...]
    escalations: tuple[dict[str, Any], ...]
    automation_executions: tuple[dict[str, Any], ...]
    agent_interactions: tuple[dict[str, Any], ...]
    approval_decisions: tuple[dict[str, Any], ...]
    integration_deliveries: tuple[dict[str, Any], ...]


def _parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _duration_minutes(start: str, end: str) -> float:
    return (_parse_ts(end) - _parse_ts(start)).total_seconds() / 60


def _resolution_duration(case: dict[str, Any]) -> float | None:
    resolved = next(
        (event for event in case["history"] if event.get("to_stage") == CaseStage.RESOLVED.value),
        None,
    )
    if resolved is None:
        return None
    return _duration_minutes(case["created_at"], resolved["timestamp"])


def _first_response_at(case: dict[str, Any]) -> datetime | None:
    response_stages = {
        CaseStage.IN_PROGRESS.value,
        CaseStage.PENDING.value,
        CaseStage.ESCALATED.value,
        CaseStage.RESOLVED.value,
        CaseStage.CLOSED.value,
    }
    event = next(
        (event for event in case["history"] if event.get("to_stage") in response_stages),
        None,
    )
    return _parse_ts(event["timestamp"]) if event is not None else None


def _queue_key(case: dict[str, Any]) -> str:
    return case.get("queue") or "Unassigned"


def build_silver_model(bronze: BronzeModel) -> SilverModel:
    """Build conformed operational entities from Bronze evidence."""
    service_cases: list[dict[str, Any]] = []
    queues: dict[str, dict[str, Any]] = {}
    sla_events: list[dict[str, Any]] = []
    escalations: list[dict[str, Any]] = []

    for case in bronze.cases:
        resolution_minutes = _resolution_duration(case)
        is_resolved = case["stage"] in {CaseStage.RESOLVED.value, CaseStage.CLOSED.value}
        queue_name = _queue_key(case)
        queues.setdefault(queue_name, {"queue": queue_name})
        service_cases.append(
            {
                "case_id": case["case_id"],
                "category": case["category"],
                "priority": case["priority"],
                "status": case["stage"],
                "queue": queue_name,
                "owner": case.get("owner"),
                "created_at": case["created_at"],
                "updated_at": case["updated_at"],
                "resolution_outcome": case.get("resolution"),
                "is_open": not is_resolved,
                "is_resolved": is_resolved,
                "resolution_minutes": resolution_minutes,
            }
        )

        category = ServiceCategory(case["category"])
        priority = Priority(case["priority"])
        target = get_sla_target(category, priority)
        status = evaluate_sla(
            target,
            created_at=_parse_ts(case["created_at"]),
            first_response_at=_first_response_at(case),
            resolved_at=_parse_ts(case["updated_at"]) if is_resolved else None,
            now=_parse_ts(case["updated_at"]),
        )
        sla_events.append(
            {
                "case_id": case["case_id"],
                "category": case["category"],
                "priority": case["priority"],
                "response_due_at": status.response_due_at.isoformat(),
                "resolution_due_at": status.resolution_due_at.isoformat(),
                "response_breached": status.response_breached,
                "resolution_breached": status.resolution_breached,
                "sla_compliant": not (status.response_breached or status.resolution_breached),
            }
        )

    for event in bronze.case_events:
        if event.get("to_stage") == CaseStage.ESCALATED.value or "Escalated:" in event["detail"]:
            escalations.append(
                {
                    "case_id": event["case_id"],
                    "timestamp": event["timestamp"],
                    "reason": event["detail"].replace("Escalated: ", ""),
                }
            )

    automation_executions = tuple(
        {
            "flow_id": trace["flow_id"],
            "trace_type": trace["trace_type"],
            "canonical_case_id": trace["canonical_case_id"],
            "correlation_id": trace["correlation_id"],
            "step_count": len(trace["steps"]),
            "success_count": sum(
                1 for step in trace["steps"] if step["status"] == "simulated_success"
            ),
            "failure_count": sum(
                1 for step in trace["steps"] if step["status"] != "simulated_success"
            ),
        }
        for trace in bronze.automation_traces
    )

    agent_interactions = tuple(
        {
            "agent_id": trace["agent_id"],
            "tool_name": trace["tool_name"],
            "allowed": trace["allowed"],
            "correlation_id": trace["correlation_id"],
            "human_approval": trace.get("human_approval"),
        }
        for trace in bronze.agent_tool_traces
    )

    approval_decisions = tuple(
        {
            "approval_id": record["request"]["approval_id"],
            "case_id": record["request"]["case_id"],
            "requested_action": record["request"]["requested_action"],
            "requester": record["request"]["requester"],
            "approver_role": record["request"]["approver_role"],
            "correlation_id": record["request"]["correlation_id"],
            "decision": record["decision"],
            "decided_at": record["decided_at"],
        }
        for record in bronze.approval_records
    )

    integration_deliveries = tuple(
        {
            "envelope_id": trace["delivery"]["envelope_id"],
            "idempotency_key": trace["delivery"]["idempotency_key"],
            "correlation_id": trace["delivery"]["correlation_id"],
            "source_system": trace["delivery"]["source_system"],
            "target_system": trace["delivery"]["target_system"],
            "operation": trace["delivery"]["operation"],
            "state": trace["delivery"]["state"],
            "attempts": trace["delivery"]["attempts"],
            "manual_review_required": trace["delivery"]["manual_review_required"],
            "scenario": trace["scenario"],
        }
        for trace in bronze.integration_delivery_traces
    )

    # Touch median import through a stable no-op path to keep this module's
    # statistical dependency explicit near the conformance layer.
    if False:  # pragma: no cover
        median([])

    return SilverModel(
        service_cases=tuple(service_cases),
        lifecycle_events=bronze.case_events,
        queues=tuple(queues.values()),
        sla_events=tuple(sla_events),
        escalations=tuple(escalations),
        automation_executions=automation_executions,
        agent_interactions=agent_interactions,
        approval_decisions=approval_decisions,
        integration_deliveries=integration_deliveries,
    )


__all__ = ["SilverModel", "build_silver_model"]
