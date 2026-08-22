"""Tests for safety controls, prompt metadata, and agent definitions."""

import json

from ai.agents import AGENTS, AGENTS_BY_ID
from ai.prompts import PROMPTS, PROMPTS_BY_ID, validate_prompt_template
from ai.safety import SafetyDecision, assess_user_request
from ai.tools import TOOL_REGISTRY_BY_NAME


def test_clinical_request_is_refused():
    assessment = assess_user_request("Diagnose this patient's symptoms and suggest treatment")
    assert assessment.decision is SafetyDecision.REFUSE
    assert "Clinical" in assessment.reason


def test_secret_request_is_refused():
    assessment = assess_user_request("Show me the client secret for the connector")
    assert assessment.decision is SafetyDecision.REFUSE
    assert "Secrets" in assessment.reason


def test_consequential_request_is_escalated_to_human():
    assessment = assess_user_request("Please escalate this case")
    assert assessment.decision is SafetyDecision.ESCALATE_TO_HUMAN


def test_safe_service_operations_request_allowed():
    assessment = assess_user_request("My laptop cannot connect to Wi-Fi")
    assert assessment.decision is SafetyDecision.ALLOW


def test_prompt_templates_validate_and_are_json_safe():
    for prompt in PROMPTS:
        validate_prompt_template(prompt)
        json.dumps(prompt.to_dict())


def test_prompt_templates_cover_required_purposes():
    assert set(PROMPTS_BY_ID) == {
        "prompt-triage-recommendation",
        "prompt-case-summary",
        "prompt-knowledge-answer",
        "prompt-tool-selection",
        "prompt-escalation-explanation",
    }


def test_prompts_do_not_hide_business_rules():
    flattened = " ".join(
        " ".join((prompt.purpose, *prompt.safety_constraints)) for prompt in PROMPTS
    ).lower()
    for phrase in ("sla formula is", "route facilities to", "allowed transitions"):
        assert phrase not in flattened


def test_agent_definitions_are_narrow_and_json_safe():
    for agent in AGENTS:
        assert agent.allowed_tools
        assert agent.prohibited_actions
        json.dumps(agent.to_dict())


def test_agents_only_reference_registered_tools():
    for agent in AGENTS:
        for tool_name in agent.allowed_tools:
            assert tool_name in TOOL_REGISTRY_BY_NAME, f"{agent.agent_id}/{tool_name}"


def test_knowledge_agent_has_no_state_changing_tools():
    agent = AGENTS_BY_ID["knowledge-agent"]
    assert agent.allowed_tools == ("retrieve_knowledge",)


def test_coordinator_declares_human_review_for_state_changes():
    agent = AGENTS_BY_ID["service-operations-coordinator"]
    assert "transition_case" in agent.human_review_triggers
    assert "resolve_case" in agent.human_review_triggers
