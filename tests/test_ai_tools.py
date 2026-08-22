"""Tests for the bounded AI tool registry and approval gates."""

import pytest

from ai.tools import (
    TOOL_REGISTRY,
    TOOL_REGISTRY_BY_NAME,
    ToolRisk,
    ToolValidationError,
    validate_tool_call,
    validate_tool_registry,
)
from power_platform.connectors import CONNECTOR_OPERATIONS_BY_NAME


def test_tool_registry_validates():
    validate_tool_registry()  # must not raise


def test_tool_registry_contains_expected_tools():
    assert set(TOOL_REGISTRY_BY_NAME) == {
        "create_case",
        "get_case",
        "list_service_categories",
        "retrieve_queue_assignment",
        "evaluate_sla",
        "evaluate_escalation",
        "transition_case",
        "resolve_case",
        "retrieve_knowledge",
        "request_human_approval",
    }


def test_connector_backed_tools_reference_existing_connector_operations():
    for tool in TOOL_REGISTRY:
        if tool.connector_operation is not None:
            assert tool.connector_operation in CONNECTOR_OPERATIONS_BY_NAME


@pytest.mark.parametrize("tool_name", ["transition_case", "resolve_case"])
def test_state_changing_tools_require_human_approval(tool_name):
    tool = TOOL_REGISTRY_BY_NAME[tool_name]
    assert tool.risk is ToolRisk.STATE_CHANGING
    assert tool.requires_human_approval is True
    with pytest.raises(ToolValidationError, match="requires human approval"):
        validate_tool_call(
            agent_id="service-operations-coordinator",
            tool_name=tool_name,
            human_approved=False,
        )


def test_state_changing_tool_allowed_after_human_approval():
    tool = validate_tool_call(
        agent_id="service-operations-coordinator",
        tool_name="transition_case",
        human_approved=True,
    )
    assert tool.name == "transition_case"


def test_agent_cannot_call_unassigned_tool():
    with pytest.raises(ToolValidationError, match="not allowed"):
        validate_tool_call(agent_id="knowledge-agent", tool_name="transition_case")


def test_unknown_tool_rejected():
    with pytest.raises(ToolValidationError, match="unknown tool"):
        validate_tool_call(agent_id="service-operations-coordinator", tool_name="delete_case")


def test_read_only_knowledge_tool_does_not_require_approval():
    tool = validate_tool_call(agent_id="knowledge-agent", tool_name="retrieve_knowledge")
    assert tool.risk is ToolRisk.READ_ONLY
    assert tool.requires_human_approval is False
