"""Reference Copilot Studio topic specifications.

These are version-controlled design specs, not exported Copilot Studio
solutions or deployed topic packages.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class CopilotTopic:
    """One representative Copilot Studio topic."""

    topic_id: str
    name: str
    trigger_intent: str
    required_inputs: tuple[str, ...]
    permitted_data_access: str
    tool_invoked: str | None
    ai_reasoning_used: bool
    human_approval_required: bool
    success_path: str
    refusal_or_escalation_path: str
    audit_event: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "topic_id": self.topic_id,
            "name": self.name,
            "trigger_intent": self.trigger_intent,
            "required_inputs": list(self.required_inputs),
            "permitted_data_access": self.permitted_data_access,
            "tool_invoked": self.tool_invoked,
            "ai_reasoning_used": self.ai_reasoning_used,
            "human_approval_required": self.human_approval_required,
            "success_path": self.success_path,
            "refusal_or_escalation_path": self.refusal_or_escalation_path,
            "audit_event": self.audit_event,
        }


COPILOT_TOPICS: tuple[CopilotTopic, ...] = (
    CopilotTopic(
        topic_id="topic-report-digital-issue",
        name="Report a digital issue",
        trigger_intent="User reports laptop, Wi-Fi, workstation, printer, or collaboration issue.",
        required_inputs=("title", "description", "category", "priority", "requestor"),
        permitted_data_access="Conversation fields only until create_case is invoked.",
        tool_invoked="create_case",
        ai_reasoning_used=True,
        human_approval_required=False,
        success_path="Collect fields, recommend triage, submit through approved intake tool.",
        refusal_or_escalation_path="Refuse secrets/credentials; ask human if low confidence.",
        audit_event="copilot_topic_digital_issue",
    ),
    CopilotTopic(
        topic_id="topic-report-facilities-issue",
        name="Report a facilities issue",
        trigger_intent="User reports estate, room, heating, cooling, or contractor issue.",
        required_inputs=("location", "description", "impact", "requestor"),
        permitted_data_access="Conversation fields only.",
        tool_invoked="create_case",
        ai_reasoning_used=True,
        human_approval_required=False,
        success_path="Collect location/impact and submit as Facilities service request.",
        refusal_or_escalation_path="Escalate to human if safety-sensitive ambiguity is present.",
        audit_event="copilot_topic_facilities_issue",
    ),
    CopilotTopic(
        topic_id="topic-report-clinical-equipment-issue",
        name="Report a clinical-equipment service issue",
        trigger_intent=(
            "User reports equipment maintenance, firmware, advisory, or logistics issue."
        ),
        required_inputs=("equipment_type", "description", "site", "priority", "requestor"),
        permitted_data_access="Operational equipment details only; no patient data.",
        tool_invoked="create_case",
        ai_reasoning_used=True,
        human_approval_required=False,
        success_path="Collect operational equipment fields and submit through intake.",
        refusal_or_escalation_path="Refuse diagnosis/treatment or patient-specific content.",
        audit_event="copilot_topic_equipment_issue",
    ),
    CopilotTopic(
        topic_id="topic-access-request",
        name="Access request",
        trigger_intent=(
            "User requests account, MFA, joiner, mover, leaver, or elevated access help."
        ),
        required_inputs=("access_need", "business_reason", "requestor"),
        permitted_data_access="Requestor's submitted fields and permitted case status.",
        tool_invoked="request_human_approval",
        ai_reasoning_used=True,
        human_approval_required=True,
        success_path="For standard access, collect request; for elevated access, open approval.",
        refusal_or_escalation_path=(
            "Refuse credential disclosure; require approval for elevated access."
        ),
        audit_event="copilot_topic_access_request",
    ),
    CopilotTopic(
        topic_id="topic-check-request-status",
        name="Check request status",
        trigger_intent="User asks for the status of a case they are permitted to view.",
        required_inputs=("case_id", "requestor_context"),
        permitted_data_access="Own request status only; no unrestricted case search.",
        tool_invoked="get_case",
        ai_reasoning_used=False,
        human_approval_required=False,
        success_path="Return permitted canonical stage and non-sensitive summary.",
        refusal_or_escalation_path="Refuse if caller is not permitted to view the case.",
        audit_event="copilot_topic_status_lookup",
    ),
    CopilotTopic(
        topic_id="topic-search-service-knowledge",
        name="Search service knowledge",
        trigger_intent="User asks how to handle a service-operations task.",
        required_inputs=("question",),
        permitted_data_access="Synthetic knowledge corpus only.",
        tool_invoked="retrieve_knowledge",
        ai_reasoning_used=True,
        human_approval_required=False,
        success_path="Return grounded answer with article ids.",
        refusal_or_escalation_path="Refuse clinical treatment or credential requests.",
        audit_event="copilot_topic_knowledge_search",
    ),
    CopilotTopic(
        topic_id="topic-explain-sla-status",
        name="Explain SLA status",
        trigger_intent="Service agent asks why a case is at risk or escalated.",
        required_inputs=("case_id",),
        permitted_data_access="Agent's queue-scoped case and canonical SLA evaluation output.",
        tool_invoked="evaluate_sla",
        ai_reasoning_used=True,
        human_approval_required=False,
        success_path="Explain supplied canonical SLA/escalation result without recalculating it.",
        refusal_or_escalation_path="Refuse to invent SLA formula or override canonical result.",
        audit_event="copilot_topic_sla_explanation",
    ),
    CopilotTopic(
        topic_id="topic-request-escalation",
        name="Request escalation",
        trigger_intent="User asks to escalate a case.",
        required_inputs=("case_id", "reason"),
        permitted_data_access="Case status and canonical escalation evaluation.",
        tool_invoked="evaluate_escalation",
        ai_reasoning_used=True,
        human_approval_required=True,
        success_path=(
            "Evaluate canonical escalation eligibility and route proposed action for review."
        ),
        refusal_or_escalation_path="Do not escalate solely from generated text.",
        audit_event="copilot_topic_escalation_request",
    ),
    CopilotTopic(
        topic_id="topic-provide-resolution-feedback",
        name="Provide resolution feedback",
        trigger_intent="Requestor provides feedback after resolution.",
        required_inputs=("case_id", "feedback_text"),
        permitted_data_access="Own resolved case status only.",
        tool_invoked=None,
        ai_reasoning_used=True,
        human_approval_required=False,
        success_path="Record feedback as informational evidence; do not change canonical state.",
        refusal_or_escalation_path=(
            "Escalate abusive, unsafe, or out-of-scope content to human review."
        ),
        audit_event="copilot_topic_resolution_feedback",
    ),
)

COPILOT_TOPICS_BY_ID: dict[str, CopilotTopic] = {topic.topic_id: topic for topic in COPILOT_TOPICS}


__all__ = ["COPILOT_TOPICS", "COPILOT_TOPICS_BY_ID", "CopilotTopic"]
