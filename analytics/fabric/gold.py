"""Gold business-ready analytical outputs."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, median
from typing import Any

from ai.tools import TOOL_REGISTRY_BY_NAME, ToolRisk
from analytics.fabric.silver import SilverModel


@dataclass(frozen=True, slots=True)
class GoldModel:
    """Business-ready KPI outputs."""

    case_metrics: dict[str, Any]
    sla_summary: dict[str, Any]
    automation_metrics: dict[str, Any]
    copilot_usage: dict[str, Any]


def _count_by(records: tuple[dict[str, Any], ...], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        value = str(record.get(key) or "Unknown")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _percent(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100, 2)


def build_case_metrics(silver: SilverModel) -> dict[str, Any]:
    """Case volume, distribution, workload, resolution, and escalation metrics."""
    cases = silver.service_cases
    resolved_durations = [
        case["resolution_minutes"] for case in cases if case["resolution_minutes"] is not None
    ]
    resolved_count = sum(1 for case in cases if case["is_resolved"])
    open_count = sum(1 for case in cases if case["is_open"])
    return {
        "generated_from": "analytics.fabric.gold.build_case_metrics",
        "total_cases": len(cases),
        "open_cases": open_count,
        "resolved_cases": resolved_count,
        "case_volume_by_category": _count_by(cases, "category"),
        "case_volume_by_priority": _count_by(cases, "priority"),
        "case_volume_by_status": _count_by(cases, "status"),
        "queue_workload": _count_by(cases, "queue"),
        "resolution_outcomes": _count_by(cases, "resolution_outcome"),
        "mean_resolution_minutes": round(mean(resolved_durations), 2)
        if resolved_durations
        else None,
        "median_resolution_minutes": round(median(resolved_durations), 2)
        if resolved_durations
        else None,
        "escalation_count": len(silver.escalations),
        "escalation_rate_percent": _percent(len(silver.escalations), len(cases)),
        "note": "Synthetic/generated portfolio evidence; not production metrics.",
    }


def build_sla_summary(silver: SilverModel) -> dict[str, Any]:
    """SLA compliance and breach metrics."""
    events = silver.sla_events
    compliant = sum(1 for event in events if event["sla_compliant"])
    response_breaches = sum(1 for event in events if event["response_breached"])
    resolution_breaches = sum(1 for event in events if event["resolution_breached"])
    return {
        "generated_from": "analytics.fabric.gold.build_sla_summary",
        "case_count": len(events),
        "sla_compliant_count": compliant,
        "sla_compliance_rate_percent": _percent(compliant, len(events)),
        "sla_breach_count": len(events) - compliant,
        "response_breach_count": response_breaches,
        "resolution_breach_count": resolution_breaches,
        "breaches_by_category": _count_by(
            tuple(event for event in events if not event["sla_compliant"]), "category"
        ),
        "breaches_by_priority": _count_by(
            tuple(event for event in events if not event["sla_compliant"]), "priority"
        ),
        "note": "SLA status is derived via business_process.sla, not an analytics rule copy.",
    }


def build_automation_metrics(silver: SilverModel) -> dict[str, Any]:
    """Automation execution and approval workload metrics."""
    executions = silver.automation_executions
    approvals = silver.approval_decisions
    execution_count = len(executions)
    success_count = sum(1 for execution in executions if execution["failure_count"] == 0)
    return {
        "generated_from": "analytics.fabric.gold.build_automation_metrics",
        "automation_execution_count": execution_count,
        "automation_success_count": success_count,
        "automation_failure_count": execution_count - success_count,
        "automation_success_rate_percent": _percent(success_count, execution_count),
        "automation_step_count": sum(execution["step_count"] for execution in executions),
        "approval_decision_count": len(approvals),
        "human_approval_rate_percent": _percent(len(approvals), execution_count + len(approvals)),
        "approval_decisions_by_outcome": _count_by(approvals, "decision"),
        "note": "Automation metrics use simulated/reference traces only.",
    }


def build_copilot_usage(silver: SilverModel) -> dict[str, Any]:
    """Agent/tool usage and evaluation metrics."""
    interactions = silver.agent_interactions
    risk_counts: dict[str, int] = {risk.value: 0 for risk in ToolRisk}
    for interaction in interactions:
        tool = TOOL_REGISTRY_BY_NAME[interaction["tool_name"]]
        risk_counts[tool.risk.value] += 1
    state_changing = risk_counts[ToolRisk.STATE_CHANGING.value]
    consequential = risk_counts[ToolRisk.CONSEQUENTIAL.value]
    return {
        "generated_from": "analytics.fabric.gold.build_copilot_usage",
        "agent_tool_invocation_count": len(interactions),
        "agent_invocations_by_agent": _count_by(interactions, "agent_id"),
        "tool_invocations_by_name": _count_by(interactions, "tool_name"),
        "tool_invocations_by_risk": risk_counts,
        "recommendation_vs_state_changing": {
            "recommendation": risk_counts[ToolRisk.RECOMMENDATION.value],
            "state_changing": state_changing,
            "consequential": consequential,
            "read_only": risk_counts[ToolRisk.READ_ONLY.value],
        },
        "approval_required_action_count": state_changing + consequential,
        "note": "AI-assistance usage is synthetic/reference evidence, not production telemetry.",
    }


def build_gold_model(silver: SilverModel) -> GoldModel:
    """Build all Gold outputs."""
    return GoldModel(
        case_metrics=build_case_metrics(silver),
        sla_summary=build_sla_summary(silver),
        automation_metrics=build_automation_metrics(silver),
        copilot_usage=build_copilot_usage(silver),
    )


__all__ = [
    "GoldModel",
    "build_automation_metrics",
    "build_case_metrics",
    "build_copilot_usage",
    "build_gold_model",
    "build_sla_summary",
]
