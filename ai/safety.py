"""Safety checks for synthetic Copilot/agent scenarios."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class SafetyDecision(StrEnum):
    """High-level safety classification for a user request."""

    ALLOW = "allow"
    REFUSE = "refuse"
    ESCALATE_TO_HUMAN = "escalate_to_human"


@dataclass(frozen=True, slots=True)
class SafetyAssessment:
    """Deterministic safety decision and rationale."""

    decision: SafetyDecision
    reason: str
    audit_event: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.value,
            "reason": self.reason,
            "audit_event": self.audit_event,
        }


_CLINICAL_TERMS = ("diagnose", "diagnosis", "treatment", "prescribe", "patient medication")
_SECRET_TERMS = ("password", "client secret", "private key", "token")
_UNSUPPORTED_ACTIONS = ("delete all", "bypass approval", "close every case", "ignore sla")


def assess_user_request(text: str) -> SafetyAssessment:
    """Classify obvious unsafe or unsupported requests deterministically."""
    lowered = text.lower()
    if any(term in lowered for term in _CLINICAL_TERMS):
        return SafetyAssessment(
            decision=SafetyDecision.REFUSE,
            reason=(
                "Clinical diagnosis or treatment advice is outside this service-operations scope."
            ),
            audit_event="ai_safety_refused_clinical_request",
        )
    if any(term in lowered for term in _SECRET_TERMS) and "reset" not in lowered:
        return SafetyAssessment(
            decision=SafetyDecision.REFUSE,
            reason="Secrets, credentials, and sensitive tokens must not be requested or exposed.",
            audit_event="ai_safety_refused_secret_request",
        )
    if any(term in lowered for term in _UNSUPPORTED_ACTIONS):
        return SafetyAssessment(
            decision=SafetyDecision.REFUSE,
            reason="Unsupported or governance-bypassing actions are not allowed.",
            audit_event="ai_safety_refused_unsupported_action",
        )
    if "escalate" in lowered or "approve" in lowered:
        return SafetyAssessment(
            decision=SafetyDecision.ESCALATE_TO_HUMAN,
            reason="Consequential requests require deterministic checks and/or human review.",
            audit_event="ai_safety_human_review_required",
        )
    return SafetyAssessment(
        decision=SafetyDecision.ALLOW,
        reason="Request is within synthetic service-operations scope.",
        audit_event="ai_safety_allowed",
    )


__all__ = ["SafetyAssessment", "SafetyDecision", "assess_user_request"]
