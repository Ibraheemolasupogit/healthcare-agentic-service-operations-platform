"""Tests for semantic model metadata."""

import json

import pytest

from analytics.semantic_model.model import SEMANTIC_MODEL, validate_semantic_model


def test_semantic_model_validates_and_is_json_safe():
    validate_semantic_model()
    json.dumps(SEMANTIC_MODEL)


def test_semantic_model_declares_required_dimensions():
    dimensions = set(SEMANTIC_MODEL["dimensions"])
    assert {
        "date",
        "service_category",
        "priority",
        "queue",
        "case_status",
        "resolution_outcome",
        "automation_workflow",
        "agent",
        "tool_risk_class",
        "integration_system",
        "delivery_state",
    } <= dimensions


def test_semantic_model_declares_required_facts_and_measures():
    facts = set(SEMANTIC_MODEL["facts"])
    assert {
        "fact_case",
        "fact_case_event",
        "fact_sla_event",
        "fact_automation_execution",
        "fact_agent_interaction",
        "fact_approval_decision",
        "fact_integration_delivery",
    } <= facts
    assert "Total Cases" in SEMANTIC_MODEL["measures"]
    assert "SLA Compliance Rate" in SEMANTIC_MODEL["measures"]
    assert "Integration Deliveries" in SEMANTIC_MODEL["measures"]


def test_semantic_model_rejects_missing_sections():
    broken = dict(SEMANTIC_MODEL)
    broken["facts"] = {}
    with pytest.raises(ValueError, match="facts"):
        validate_semantic_model(broken)
