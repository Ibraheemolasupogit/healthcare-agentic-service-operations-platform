"""Tests for bounded orchestration and deterministic evaluation evidence."""

import json

from ai.evaluation import (
    build_agent_tool_traces,
    build_ai_evaluation_cases,
    build_copilot_conversations,
    build_evaluation_summary,
    evaluate_all,
    generate_all,
)
from ai.orchestration import (
    answer_knowledge_question,
    plan_tool_invocation,
    summarize_case,
)
from business_process.fixtures import build_synthetic_cases


def test_plan_tool_invocation_blocks_unapproved_state_change():
    plan = plan_tool_invocation(
        agent_id="service-operations-coordinator", tool_name="transition_case"
    )
    assert plan.allowed is False
    assert "requires human approval" in plan.reason


def test_plan_tool_invocation_allows_approved_state_change():
    plan = plan_tool_invocation(
        agent_id="service-operations-coordinator",
        tool_name="transition_case",
        human_approved=True,
    )
    assert plan.allowed is True


def test_answer_knowledge_question_is_grounded():
    answer = answer_knowledge_question("How do I request MFA reset?")
    assert answer["refused"] is False
    assert answer["article_ids"][0] == "KA-ACCESS-001"


def test_answer_knowledge_question_refuses_clinical_content():
    answer = answer_knowledge_question("Diagnose this patient")
    assert answer["refused"] is True
    assert answer["article_ids"] == []


def test_summarize_case_uses_canonical_case_fields():
    case = build_synthetic_cases()[0]
    summary = summarize_case(case)
    assert summary["case_id"] == case.case_id
    assert summary["history_event_count"] == len(case.history)
    assert summary["latest_event"]


def test_ai_evaluation_cases_cover_required_categories():
    categories = {case.evaluation_type for case in build_ai_evaluation_cases()}
    assert {
        "intent_recognition",
        "category_recommendation",
        "priority_recommendation",
        "grounded_knowledge_answer",
        "case_summary_completeness",
        "unsafe_request_refusal",
        "unsupported_action_refusal",
        "invalid_tool_invocation_prevention",
        "human_approval_requirement",
        "deterministic_canonical_rule_enforcement",
    } <= categories


def test_evaluate_all_passes_every_synthetic_case():
    results = evaluate_all()
    assert all(result.passed for result in results)


def test_evaluation_summary_is_synthetic_and_json_safe():
    summary = build_evaluation_summary()
    json.dumps(summary)
    assert summary["evaluation"]["failed_count"] == 0
    assert "no live Copilot Studio tenant" in summary["note"]


def test_agent_tool_traces_are_labelled_as_simulation():
    traces = build_agent_tool_traces()
    assert traces
    assert all(trace["trace_type"] == "simulated_reference_agent_tool_trace" for trace in traces)
    assert all("not live Copilot Studio telemetry" in trace["note"] for trace in traces)


def test_copilot_conversations_are_synthetic():
    conversations = build_copilot_conversations()
    assert conversations
    assert all("Synthetic/reference" in conversation["note"] for conversation in conversations)


def test_generate_all_is_deterministic(tmp_path):
    first = generate_all(
        data_dir=tmp_path / "a" / "data",
        reports_dir=tmp_path / "a" / "reports",
        prompts_dir=tmp_path / "a" / "prompts",
        topics_dir=tmp_path / "a" / "topics",
    )
    second = generate_all(
        data_dir=tmp_path / "b" / "data",
        reports_dir=tmp_path / "b" / "reports",
        prompts_dir=tmp_path / "b" / "prompts",
        topics_dir=tmp_path / "b" / "topics",
    )
    assert set(first) == set(second)
    for name in first:
        assert first[name].read_text(encoding="utf-8") == second[name].read_text(encoding="utf-8")
