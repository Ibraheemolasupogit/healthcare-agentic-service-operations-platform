"""Tests for Gold KPI generation."""

from analytics.fabric.gold import (
    build_automation_metrics,
    build_case_metrics,
    build_copilot_usage,
    build_gold_model,
    build_sla_summary,
)
from analytics.fabric.ingestion import load_bronze_model
from analytics.fabric.silver import build_silver_model


def _silver():
    return build_silver_model(load_bronze_model())


def test_case_metrics_are_deterministic_and_proportional():
    metrics = build_case_metrics(_silver())
    assert metrics["total_cases"] == 6
    assert metrics["open_cases"] == 3
    assert metrics["resolved_cases"] == 3
    assert metrics["case_volume_by_category"]["Digital Support"] == 1
    assert metrics["case_volume_by_priority"]["Medium"] == 2
    assert metrics["mean_resolution_minutes"] == 145.0
    assert metrics["median_resolution_minutes"] == 90.0
    assert metrics["escalation_rate_percent"] == 16.67


def test_sla_summary_uses_canonical_evaluation_results():
    summary = build_sla_summary(_silver())
    assert summary["case_count"] == 6
    assert summary["sla_breach_count"] == 1
    assert summary["resolution_breach_count"] == 1
    assert summary["response_breach_count"] == 0
    assert summary["sla_compliance_rate_percent"] == 83.33


def test_automation_metrics_reflect_simulated_trace_and_approvals():
    metrics = build_automation_metrics(_silver())
    assert metrics["automation_execution_count"] == 1
    assert metrics["automation_success_count"] == 1
    assert metrics["automation_failure_count"] == 0
    assert metrics["approval_decisions_by_outcome"] == {"Approved": 1, "Rejected": 1}


def test_copilot_usage_counts_tool_risk_mix():
    usage = build_copilot_usage(_silver())
    assert usage["agent_tool_invocation_count"] == 2
    assert usage["tool_invocations_by_risk"]["read-only"] == 1
    assert usage["tool_invocations_by_risk"]["state-changing"] == 1
    assert usage["approval_required_action_count"] == 1


def test_gold_model_contains_all_outputs():
    gold = build_gold_model(_silver())
    assert gold.case_metrics["total_cases"] == 6
    assert gold.sla_summary["case_count"] == 6
    assert gold.automation_metrics["automation_step_count"] == 8
    assert gold.copilot_usage["agent_tool_invocation_count"] == 2
