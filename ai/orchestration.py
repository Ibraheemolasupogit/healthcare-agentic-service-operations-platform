"""Small deterministic orchestration helpers for bounded agents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai.knowledge import retrieve_knowledge
from ai.safety import SafetyDecision, assess_user_request
from ai.tools import ToolSpec, validate_tool_call
from ai.triage import TriageRecommendation, recommend_triage
from business_process import Case, case_to_dict


@dataclass(frozen=True, slots=True)
class ToolInvocationPlan:
    """An audited plan for a tool call."""

    agent_id: str
    tool: ToolSpec
    human_approved: bool
    allowed: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "tool": self.tool.to_dict(),
            "human_approved": self.human_approved,
            "allowed": self.allowed,
            "reason": self.reason,
        }


def plan_tool_invocation(
    *, agent_id: str, tool_name: str, human_approved: bool = False
) -> ToolInvocationPlan:
    """Validate a tool call and return an auditable plan."""
    try:
        tool = validate_tool_call(
            agent_id=agent_id, tool_name=tool_name, human_approved=human_approved
        )
        return ToolInvocationPlan(
            agent_id=agent_id,
            tool=tool,
            human_approved=human_approved,
            allowed=True,
            reason="Tool call is allow-listed for this agent.",
        )
    except Exception as exc:
        placeholder = validate_tool_call(
            agent_id="knowledge-agent", tool_name="retrieve_knowledge", human_approved=False
        )
        return ToolInvocationPlan(
            agent_id=agent_id,
            tool=placeholder,
            human_approved=human_approved,
            allowed=False,
            reason=str(exc),
        )


def summarize_case(case: Case) -> dict[str, Any]:
    """Return a deterministic summary grounded only in the supplied canonical case."""
    payload = case_to_dict(case)
    return {
        "case_id": case.case_id,
        "summary": (
            f"{case.title} is a {case.priority.value} {case.category.value} case currently "
            f"in {case.stage.value}."
        ),
        "queue": case.queue.value if case.queue else None,
        "owner": case.owner,
        "history_event_count": len(case.history),
        "latest_event": payload["history"][-1] if payload["history"] else None,
        "resolution": case.resolution.value if case.resolution else None,
    }


def answer_knowledge_question(question: str) -> dict[str, Any]:
    """Ground a knowledge response in retrieved synthetic articles."""
    safety = assess_user_request(question)
    if safety.decision is SafetyDecision.REFUSE:
        return {"answer": safety.reason, "article_ids": [], "refused": True}
    articles = retrieve_knowledge(question)
    if not articles:
        return {
            "answer": "No matching synthetic service-operations article was found.",
            "article_ids": [],
            "refused": False,
        }
    return {
        "answer": articles[0].answer,
        "article_ids": [article.article_id for article in articles],
        "refused": False,
    }


def recommend_intake_triage(title: str, description: str) -> TriageRecommendation:
    """Thin orchestration wrapper for deterministic triage."""
    return recommend_triage(title, description)


__all__ = [
    "ToolInvocationPlan",
    "answer_knowledge_question",
    "plan_tool_invocation",
    "recommend_intake_triage",
    "summarize_case",
]
