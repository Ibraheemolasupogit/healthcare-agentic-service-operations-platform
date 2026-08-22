"""Tests for Copilot Studio reference topic specs."""

import json

from copilot.copilot_studio.topics import COPILOT_TOPICS, COPILOT_TOPICS_BY_ID


def test_topics_cover_required_conversation_patterns():
    assert set(COPILOT_TOPICS_BY_ID) == {
        "topic-report-digital-issue",
        "topic-report-facilities-issue",
        "topic-report-clinical-equipment-issue",
        "topic-access-request",
        "topic-check-request-status",
        "topic-search-service-knowledge",
        "topic-explain-sla-status",
        "topic-request-escalation",
        "topic-provide-resolution-feedback",
    }


def test_every_topic_has_required_metadata_and_json_safe():
    for topic in COPILOT_TOPICS:
        assert topic.trigger_intent
        assert topic.required_inputs
        assert topic.permitted_data_access
        assert topic.success_path
        assert topic.refusal_or_escalation_path
        assert topic.audit_event
        json.dumps(topic.to_dict())


def test_access_and_escalation_topics_require_human_approval():
    assert COPILOT_TOPICS_BY_ID["topic-access-request"].human_approval_required is True
    assert COPILOT_TOPICS_BY_ID["topic-request-escalation"].human_approval_required is True


def test_status_topic_is_read_only():
    topic = COPILOT_TOPICS_BY_ID["topic-check-request-status"]
    assert topic.tool_invoked == "get_case"
    assert topic.ai_reasoning_used is False
    assert "Own request status only" in topic.permitted_data_access


def test_equipment_topic_excludes_patient_data():
    topic = COPILOT_TOPICS_BY_ID["topic-report-clinical-equipment-issue"]
    assert "no patient data" in topic.permitted_data_access.lower()


def test_resolution_feedback_does_not_change_state():
    topic = COPILOT_TOPICS_BY_ID["topic-provide-resolution-feedback"]
    assert topic.tool_invoked is None
    assert "do not change canonical state" in topic.success_path.lower()
