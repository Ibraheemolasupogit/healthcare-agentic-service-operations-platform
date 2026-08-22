"""Typed models for the human-approval pattern (Power Automate approvals).

Models one consequential, non-clinical action requiring human sign-off —
e.g. an elevated access grant — never a clinical treatment decision. This
is a data shape plus validation only: no live Power Automate "Approvals"
connector call, no notification delivery. See power_platform/README.md
"Human approval" and docs/governance.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

from integrations.envelope import new_correlation_id


class ApprovalDecision(StrEnum):
    """The outcome of a human approval review."""

    APPROVED = "Approved"
    REJECTED = "Rejected"
    TIMED_OUT = "Timed Out"


class ApprovalValidationError(ValueError):
    """Raised when an `ApprovalRecord` is structurally incomplete or inconsistent."""


@dataclass(frozen=True, slots=True)
class ApprovalRequest:
    """A request for a human, holding `approver_role`, to authorise `requested_action`."""

    approval_id: str
    case_id: str
    requested_action: str
    requester: str
    approver_role: str
    correlation_id: str
    requested_at: datetime
    timeout_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "approval_id": self.approval_id,
            "case_id": self.case_id,
            "requested_action": self.requested_action,
            "requester": self.requester,
            "approver_role": self.approver_role,
            "correlation_id": self.correlation_id,
            "requested_at": self.requested_at.isoformat(),
            "timeout_at": self.timeout_at.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class ApprovalRecord:
    """The immutable audit record of how an `ApprovalRequest` was decided."""

    request: ApprovalRequest
    decision: ApprovalDecision
    reason: str
    decided_by: str
    decided_at: datetime
    audit_event_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "request": self.request.to_dict(),
            "decision": self.decision.value,
            "reason": self.reason,
            "decided_by": self.decided_by,
            "decided_at": self.decided_at.isoformat(),
            "audit_event_id": self.audit_event_id,
        }


def validate_approval_record(record: ApprovalRecord) -> None:
    """Raise `ApprovalValidationError` if `record` is incomplete or inconsistent."""
    errors: list[str] = []
    request = record.request
    for field_name, value in (
        ("approval_id", request.approval_id),
        ("case_id", request.case_id),
        ("requested_action", request.requested_action),
        ("requester", request.requester),
        ("approver_role", request.approver_role),
        ("correlation_id", request.correlation_id),
    ):
        if not value:
            errors.append(f"request.{field_name} is required")
    if not record.reason:
        errors.append("reason is required")
    if not record.decided_by:
        errors.append("decided_by is required")
    if not record.audit_event_id:
        errors.append("audit_event_id is required")
    if record.decided_at < request.requested_at:
        errors.append("decided_at cannot be before request.requested_at")
    if errors:
        raise ApprovalValidationError("; ".join(errors))


# Fixed reference timestamps — matches the reference date used by
# business_process.fixtures / integrations.examples, kept here for
# deterministic, reproducible approval examples (not wall-clock time).
_REFERENCE_REQUESTED_AT = datetime(2026, 1, 12, 11, 0, tzinfo=UTC)


def build_example_approvals() -> tuple[ApprovalRecord, ApprovalRecord]:
    """Two deterministic, synthetic approval examples: one Approved, one Rejected.

    Both relate to the same illustrative, non-clinical scenario — an
    elevated Dataverse security role request tied to the Access and
    Identity synthetic fixture case (`SR-AI-1004`) — never a clinical
    treatment approval.
    """
    approved_request = ApprovalRequest(
        approval_id="AR-AI-9001",
        case_id="SR-AI-1004",
        requested_action=(
            "Grant elevated Dataverse security role: Clinical Systems "
            "Administrator (time-boxed, 24h)"
        ),
        requester="identity-access-team",
        approver_role="identity-access-team-lead",
        correlation_id=new_correlation_id("approval:SR-AI-1004:elevated-role-grant"),
        requested_at=_REFERENCE_REQUESTED_AT,
        timeout_at=_REFERENCE_REQUESTED_AT + timedelta(hours=4),
    )
    approved = ApprovalRecord(
        request=approved_request,
        decision=ApprovalDecision.APPROVED,
        reason=(
            "Time-boxed elevation justified by an active on-call rotation; "
            "standard joiner checklist already on file."
        ),
        decided_by="identity-access-team-lead",
        decided_at=_REFERENCE_REQUESTED_AT + timedelta(minutes=45),
        audit_event_id="AE-AR-9001-DECISION",
    )

    rejected_request = ApprovalRequest(
        approval_id="AR-AI-9002",
        case_id="SR-AI-1004",
        requested_action="Grant permanent elevated Dataverse security role: System Customizer",
        requester="identity-access-team",
        approver_role="identity-access-team-lead",
        correlation_id=new_correlation_id("approval:SR-AI-1004:permanent-role-grant"),
        requested_at=_REFERENCE_REQUESTED_AT,
        timeout_at=_REFERENCE_REQUESTED_AT + timedelta(hours=4),
    )
    rejected = ApprovalRecord(
        request=rejected_request,
        decision=ApprovalDecision.REJECTED,
        reason=(
            "Permanent elevation not justified for this role; a time-boxed "
            "grant should be requested instead."
        ),
        decided_by="identity-access-team-lead",
        decided_at=_REFERENCE_REQUESTED_AT + timedelta(minutes=50),
        audit_event_id="AE-AR-9002-DECISION",
    )

    return approved, rejected


__all__ = [
    "ApprovalDecision",
    "ApprovalRecord",
    "ApprovalRequest",
    "ApprovalValidationError",
    "build_example_approvals",
    "validate_approval_record",
]
