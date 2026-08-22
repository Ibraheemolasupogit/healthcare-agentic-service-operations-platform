"""Narrow bounded-agent definitions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class AgentRole(StrEnum):
    """Logical role for a bounded agent."""

    INTAKE = "Intake Agent"
    KNOWLEDGE = "Knowledge Agent"
    TRIAGE = "Triage Agent"
    CASE_SUMMARY = "Case Summary Agent"
    COORDINATOR = "Service Operations Coordinator"


@dataclass(frozen=True, slots=True)
class AgentDefinition:
    """One bounded agent and its operating constraints."""

    agent_id: str
    role: AgentRole
    responsibility: str
    allowed_tools: tuple[str, ...]
    prohibited_actions: tuple[str, ...]
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    handoff_conditions: tuple[str, ...]
    human_review_triggers: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "role": self.role.value,
            "responsibility": self.responsibility,
            "allowed_tools": list(self.allowed_tools),
            "prohibited_actions": list(self.prohibited_actions),
            "inputs": list(self.inputs),
            "outputs": list(self.outputs),
            "handoff_conditions": list(self.handoff_conditions),
            "human_review_triggers": list(self.human_review_triggers),
        }


_COMMON_PROHIBITIONS = (
    "Do not override canonical lifecycle validation.",
    "Do not calculate SLA or escalation rules in prompt text.",
    "Do not expose credentials or secrets.",
    "Do not provide clinical diagnosis or treatment advice.",
)

AGENTS: tuple[AgentDefinition, ...] = (
    AgentDefinition(
        agent_id="intake-agent",
        role=AgentRole.INTAKE,
        responsibility="Guide conversational service intake and collect required fields.",
        allowed_tools=("list_service_categories", "retrieve_knowledge", "create_case", "get_case"),
        prohibited_actions=_COMMON_PROHIBITIONS,
        inputs=("user_utterance", "conversation_context"),
        outputs=("intake_fields", "missing_fields", "draft_case_request"),
        handoff_conditions=("all required fields collected", "unsafe request detected"),
        human_review_triggers=("high-impact access request", "low confidence category"),
    ),
    AgentDefinition(
        agent_id="knowledge-agent",
        role=AgentRole.KNOWLEDGE,
        responsibility="Retrieve and ground service-operations answers in synthetic knowledge.",
        allowed_tools=("retrieve_knowledge",),
        prohibited_actions=_COMMON_PROHIBITIONS,
        inputs=("question",),
        outputs=("grounded_answer", "article_ids", "uncertainty"),
        handoff_conditions=("no relevant article found", "clinical question detected"),
        human_review_triggers=("knowledge gap", "request asks for credential or clinical content"),
    ),
    AgentDefinition(
        agent_id="triage-agent",
        role=AgentRole.TRIAGE,
        responsibility="Recommend category, priority, queue, SLA/escalation review inputs.",
        allowed_tools=(
            "list_service_categories",
            "retrieve_queue_assignment",
            "evaluate_sla",
            "evaluate_escalation",
            "get_case",
        ),
        prohibited_actions=_COMMON_PROHIBITIONS + ("Do not mutate case state.",),
        inputs=("case_text", "case_id_optional"),
        outputs=("triage_recommendation", "confidence", "uncertainty"),
        handoff_conditions=("confidence below threshold", "escalation appears applicable"),
        human_review_triggers=("critical recommendation", "multiple category matches"),
    ),
    AgentDefinition(
        agent_id="case-summary-agent",
        role=AgentRole.CASE_SUMMARY,
        responsibility="Summarize canonical case state and audit trail for service agents.",
        allowed_tools=("get_case",),
        prohibited_actions=_COMMON_PROHIBITIONS + ("Do not recommend closure as a decision.",),
        inputs=("case_id",),
        outputs=("case_summary", "open_items", "audit_reference"),
        handoff_conditions=("case not found", "case has unresolved escalation"),
        human_review_triggers=("summary includes uncertainty",),
    ),
    AgentDefinition(
        agent_id="service-operations-coordinator",
        role=AgentRole.COORDINATOR,
        responsibility="Coordinate bounded tool calls and approval gates across agents.",
        allowed_tools=(
            "get_case",
            "retrieve_queue_assignment",
            "evaluate_sla",
            "evaluate_escalation",
            "transition_case",
            "resolve_case",
            "request_human_approval",
            "retrieve_knowledge",
        ),
        prohibited_actions=_COMMON_PROHIBITIONS
        + ("Do not execute state change without approval.",),
        inputs=("agent_recommendation", "case_id", "requested_action"),
        outputs=("tool_plan", "approval_required", "audit_event"),
        handoff_conditions=("state-changing action requested", "unsupported tool requested"),
        human_review_triggers=("transition_case", "resolve_case", "elevated access"),
    ),
)

AGENTS_BY_ID: dict[str, AgentDefinition] = {agent.agent_id: agent for agent in AGENTS}


__all__ = ["AGENTS", "AGENTS_BY_ID", "AgentDefinition", "AgentRole"]
