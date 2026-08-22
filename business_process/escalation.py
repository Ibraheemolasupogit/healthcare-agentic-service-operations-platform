"""Deterministic escalation triggers.

Escalation here is a pure decision function over a case's priority, current
lifecycle stage, and SLA status — not an autonomous agent decision. Whether
(and how) an agent may call this in a later milestone is a governance
question tracked in docs/governance.md; this module only decides *whether
the conditions for escalation are met*.
"""

from __future__ import annotations

from enum import StrEnum

from business_process.priority import Priority
from business_process.sla import SLAStatus
from business_process.taxonomy import CaseStage


class EscalationReason(StrEnum):
    """Why a case qualifies for escalation."""

    SLA_RESOLUTION_BREACH = "SLA resolution target breached"
    SLA_RESPONSE_BREACH = "SLA response target breached"
    CRITICAL_PRIORITY_PENDING = "Critical priority case left pending"


def determine_escalation_reason(
    *, priority: Priority, stage: CaseStage, sla_status: SLAStatus
) -> EscalationReason | None:
    """Return the escalation reason that applies, or `None` if none do.

    Checked in order of severity: a breached resolution target outranks a
    breached response target, which outranks the priority/stage heuristic.
    """
    if sla_status.resolution_breached:
        return EscalationReason.SLA_RESOLUTION_BREACH
    if sla_status.response_breached:
        return EscalationReason.SLA_RESPONSE_BREACH
    if priority == Priority.CRITICAL and stage == CaseStage.PENDING:
        return EscalationReason.CRITICAL_PRIORITY_PENDING
    return None


def should_escalate(*, priority: Priority, stage: CaseStage, sla_status: SLAStatus) -> bool:
    """Return whether a case meets any escalation condition."""
    return (
        determine_escalation_reason(priority=priority, stage=stage, sla_status=sla_status)
        is not None
    )
