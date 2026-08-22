"""Tests for deterministic escalation triggers."""

from dataclasses import replace
from datetime import UTC, datetime

from business_process import CaseStage, EscalationReason, Priority
from business_process.escalation import determine_escalation_reason, should_escalate
from business_process.sla import SLAStatus

_NOW = datetime(2026, 1, 12, 9, 0, tzinfo=UTC)

_NO_BREACH = SLAStatus(
    response_due_at=_NOW,
    resolution_due_at=_NOW,
    response_breached=False,
    resolution_breached=False,
)


def test_no_escalation_when_no_breach_and_not_critical_pending():
    reason = determine_escalation_reason(
        priority=Priority.MEDIUM, stage=CaseStage.IN_PROGRESS, sla_status=_NO_BREACH
    )
    assert reason is None
    assert not should_escalate(
        priority=Priority.MEDIUM, stage=CaseStage.IN_PROGRESS, sla_status=_NO_BREACH
    )


def test_resolution_breach_escalates():
    status = replace(_NO_BREACH, resolution_breached=True)
    reason = determine_escalation_reason(
        priority=Priority.MEDIUM, stage=CaseStage.IN_PROGRESS, sla_status=status
    )
    assert reason is EscalationReason.SLA_RESOLUTION_BREACH


def test_response_breach_escalates_when_resolution_not_yet_breached():
    status = replace(_NO_BREACH, response_breached=True)
    reason = determine_escalation_reason(
        priority=Priority.MEDIUM, stage=CaseStage.IN_PROGRESS, sla_status=status
    )
    assert reason is EscalationReason.SLA_RESPONSE_BREACH


def test_resolution_breach_takes_priority_over_response_breach():
    status = replace(_NO_BREACH, response_breached=True, resolution_breached=True)
    reason = determine_escalation_reason(
        priority=Priority.MEDIUM, stage=CaseStage.IN_PROGRESS, sla_status=status
    )
    assert reason is EscalationReason.SLA_RESOLUTION_BREACH


def test_critical_priority_pending_escalates_even_without_sla_breach():
    reason = determine_escalation_reason(
        priority=Priority.CRITICAL, stage=CaseStage.PENDING, sla_status=_NO_BREACH
    )
    assert reason is EscalationReason.CRITICAL_PRIORITY_PENDING
    assert should_escalate(
        priority=Priority.CRITICAL, stage=CaseStage.PENDING, sla_status=_NO_BREACH
    )


def test_non_critical_pending_does_not_escalate_without_breach():
    reason = determine_escalation_reason(
        priority=Priority.LOW, stage=CaseStage.PENDING, sla_status=_NO_BREACH
    )
    assert reason is None
