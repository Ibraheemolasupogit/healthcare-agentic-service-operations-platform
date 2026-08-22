"""Tests for Bronze ingestion and Silver conformance."""

from analytics.fabric.ingestion import load_bronze_model
from analytics.fabric.silver import build_silver_model


def test_bronze_ingests_existing_operational_evidence():
    bronze = load_bronze_model()
    assert len(bronze.cases) == 6
    assert len(bronze.case_events) > len(bronze.cases)
    assert len(bronze.dynamics_examples) == 6
    assert len(bronze.salesforce_examples) == 6
    assert len(bronze.approval_records) == 2
    assert len(bronze.agent_tool_traces) == 2


def test_silver_builds_conformed_entities():
    silver = build_silver_model(load_bronze_model())
    assert len(silver.service_cases) == 6
    assert len(silver.lifecycle_events) > 0
    assert len(silver.queues) == 6
    assert len(silver.sla_events) == 6
    assert len(silver.escalations) == 1
    assert len(silver.automation_executions) == 1
    assert len(silver.approval_decisions) == 2


def test_silver_service_case_preserves_canonical_identity():
    silver = build_silver_model(load_bronze_model())
    case = next(case for case in silver.service_cases if case["case_id"] == "SR-DS-1001")
    assert case["category"] == "Digital Support"
    assert case["queue"] == "Digital Support"
    assert case["is_resolved"] is True
    assert case["resolution_minutes"] == 90.0


def test_silver_automation_execution_carries_correlation_id():
    silver = build_silver_model(load_bronze_model())
    execution = silver.automation_executions[0]
    assert execution["correlation_id"]
    assert execution["success_count"] == execution["step_count"]
    assert execution["failure_count"] == 0
