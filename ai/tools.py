"""Allow-listed tool registry for bounded agentic AI.

Tools map to existing connector/canonical concepts. This module defines
permissions and risk only; it does not implement live calls or bypass
`business_process` validation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from power_platform.connectors import CONNECTOR_OPERATIONS_BY_NAME


class ToolRisk(StrEnum):
    """Risk classification used by agent/tool approval gates."""

    READ_ONLY = "read-only"
    RECOMMENDATION = "recommendation"
    STATE_CHANGING = "state-changing"
    CONSEQUENTIAL = "consequential"


class ToolValidationError(ValueError):
    """Raised when a tool call is not allowed by the registry."""


@dataclass(frozen=True, slots=True)
class ToolSpec:
    """One allow-listed AI tool."""

    name: str
    description: str
    risk: ToolRisk
    connector_operation: str | None
    requires_human_approval: bool
    allowed_agents: tuple[str, ...]
    audit_event: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "risk": self.risk.value,
            "connector_operation": self.connector_operation,
            "requires_human_approval": self.requires_human_approval,
            "allowed_agents": list(self.allowed_agents),
            "audit_event": self.audit_event,
        }


TOOL_REGISTRY: tuple[ToolSpec, ...] = (
    ToolSpec(
        name="create_case",
        description="Create a canonical case through the connector boundary.",
        risk=ToolRisk.STATE_CHANGING,
        connector_operation="create_case",
        requires_human_approval=False,
        allowed_agents=("intake-agent", "service-operations-coordinator"),
        audit_event="ai_tool_create_case_requested",
    ),
    ToolSpec(
        name="get_case",
        description="Retrieve a case by canonical id for status, summary, or SLA explanation.",
        risk=ToolRisk.READ_ONLY,
        connector_operation="get_case",
        requires_human_approval=False,
        allowed_agents=(
            "intake-agent",
            "case-summary-agent",
            "triage-agent",
            "service-operations-coordinator",
        ),
        audit_event="ai_tool_get_case_requested",
    ),
    ToolSpec(
        name="list_service_categories",
        description="List canonical service categories for intake guidance.",
        risk=ToolRisk.READ_ONLY,
        connector_operation="list_service_categories",
        requires_human_approval=False,
        allowed_agents=("intake-agent", "triage-agent"),
        audit_event="ai_tool_list_categories_requested",
    ),
    ToolSpec(
        name="retrieve_queue_assignment",
        description="Retrieve canonical queue assignment for a category.",
        risk=ToolRisk.RECOMMENDATION,
        connector_operation="retrieve_queue_assignment",
        requires_human_approval=False,
        allowed_agents=("triage-agent", "service-operations-coordinator"),
        audit_event="ai_tool_queue_assignment_requested",
    ),
    ToolSpec(
        name="evaluate_sla",
        description="Evaluate SLA status through canonical rules.",
        risk=ToolRisk.READ_ONLY,
        connector_operation="evaluate_sla",
        requires_human_approval=False,
        allowed_agents=("triage-agent", "service-operations-coordinator"),
        audit_event="ai_tool_evaluate_sla_requested",
    ),
    ToolSpec(
        name="evaluate_escalation",
        description="Evaluate escalation eligibility through canonical rules.",
        risk=ToolRisk.RECOMMENDATION,
        connector_operation="evaluate_escalation",
        requires_human_approval=False,
        allowed_agents=("triage-agent", "service-operations-coordinator"),
        audit_event="ai_tool_evaluate_escalation_requested",
    ),
    ToolSpec(
        name="transition_case",
        description="Request a canonical lifecycle transition.",
        risk=ToolRisk.STATE_CHANGING,
        connector_operation="transition_case",
        requires_human_approval=True,
        allowed_agents=("service-operations-coordinator",),
        audit_event="ai_tool_transition_case_requested",
    ),
    ToolSpec(
        name="resolve_case",
        description="Request case resolution through canonical rules.",
        risk=ToolRisk.STATE_CHANGING,
        connector_operation="resolve_case",
        requires_human_approval=True,
        allowed_agents=("service-operations-coordinator",),
        audit_event="ai_tool_resolve_case_requested",
    ),
    ToolSpec(
        name="retrieve_knowledge",
        description="Retrieve grounded service-operations knowledge articles.",
        risk=ToolRisk.READ_ONLY,
        connector_operation=None,
        requires_human_approval=False,
        allowed_agents=("knowledge-agent", "intake-agent", "service-operations-coordinator"),
        audit_event="ai_tool_retrieve_knowledge_requested",
    ),
    ToolSpec(
        name="request_human_approval",
        description="Open an approval request for a consequential proposed action.",
        risk=ToolRisk.CONSEQUENTIAL,
        connector_operation=None,
        requires_human_approval=False,
        allowed_agents=("service-operations-coordinator",),
        audit_event="ai_tool_human_approval_requested",
    ),
)

TOOL_REGISTRY_BY_NAME: dict[str, ToolSpec] = {tool.name: tool for tool in TOOL_REGISTRY}


def validate_tool_registry() -> None:
    """Raise if the registry references unknown connector operations or duplicates names."""
    names = [tool.name for tool in TOOL_REGISTRY]
    errors: list[str] = []
    if len(names) != len(set(names)):
        errors.append("duplicate tool names")
    for tool in TOOL_REGISTRY:
        if (
            tool.connector_operation
            and tool.connector_operation not in CONNECTOR_OPERATIONS_BY_NAME
        ):
            errors.append(f"{tool.name}: unknown connector operation {tool.connector_operation}")
        if not tool.allowed_agents:
            errors.append(f"{tool.name}: must declare at least one allowed agent")
        if not tool.audit_event:
            errors.append(f"{tool.name}: audit_event is required")
        if tool.risk in {ToolRisk.STATE_CHANGING, ToolRisk.CONSEQUENTIAL} and not (
            tool.requires_human_approval or tool.name in {"create_case", "request_human_approval"}
        ):
            errors.append(f"{tool.name}: state-changing/consequential tools need approval control")
    if errors:
        raise ToolValidationError("; ".join(errors))


def validate_tool_call(*, agent_id: str, tool_name: str, human_approved: bool = False) -> ToolSpec:
    """Return the tool spec if `agent_id` may call it, otherwise raise."""
    try:
        tool = TOOL_REGISTRY_BY_NAME[tool_name]
    except KeyError as exc:
        raise ToolValidationError(f"unknown tool: {tool_name}") from exc

    if agent_id not in tool.allowed_agents:
        raise ToolValidationError(f"{agent_id} is not allowed to call {tool_name}")
    if tool.requires_human_approval and not human_approved:
        raise ToolValidationError(f"{tool_name} requires human approval before invocation")
    return tool


__all__ = [
    "TOOL_REGISTRY",
    "TOOL_REGISTRY_BY_NAME",
    "ToolRisk",
    "ToolSpec",
    "ToolValidationError",
    "validate_tool_call",
    "validate_tool_registry",
]
