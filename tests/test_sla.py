"""Tests for the configurable SLA model."""

from datetime import UTC, datetime, timedelta

from business_process import Priority, ServiceCategory, evaluate_sla, get_sla_target

_NOW = datetime(2026, 1, 12, 9, 0, tzinfo=UTC)


def test_critical_priority_has_tighter_targets_than_low_priority():
    critical = get_sla_target(ServiceCategory.APPLICATION_SUPPORT, Priority.CRITICAL)
    low = get_sla_target(ServiceCategory.APPLICATION_SUPPORT, Priority.LOW)
    assert critical.response_minutes < low.response_minutes
    assert critical.resolution_minutes < low.resolution_minutes


def test_clinical_equipment_resolution_target_is_tighter_than_data_and_reporting():
    clinical = get_sla_target(ServiceCategory.CLINICAL_EQUIPMENT, Priority.HIGH)
    reporting = get_sla_target(ServiceCategory.DATA_AND_REPORTING, Priority.HIGH)
    assert clinical.resolution_minutes < reporting.resolution_minutes


def test_get_sla_target_is_deterministic_for_every_combination():
    for category in ServiceCategory:
        for priority in Priority:
            first = get_sla_target(category, priority)
            second = get_sla_target(category, priority)
            assert first == second


def test_evaluate_sla_reports_no_breach_when_within_target():
    target = get_sla_target(ServiceCategory.DIGITAL_SUPPORT, Priority.HIGH)
    status = evaluate_sla(
        target,
        created_at=_NOW,
        now=_NOW + timedelta(minutes=1),
        first_response_at=_NOW + timedelta(minutes=1),
        resolved_at=_NOW + timedelta(minutes=5),
    )
    assert not status.response_breached
    assert not status.resolution_breached


def test_evaluate_sla_reports_breach_when_targets_exceeded():
    target = get_sla_target(ServiceCategory.DIGITAL_SUPPORT, Priority.CRITICAL)
    status = evaluate_sla(
        target,
        created_at=_NOW,
        now=_NOW + timedelta(days=1),
        first_response_at=None,
        resolved_at=None,
    )
    assert status.response_breached
    assert status.resolution_breached


def test_evaluate_sla_uses_now_when_case_is_still_open():
    target = get_sla_target(ServiceCategory.DIGITAL_SUPPORT, Priority.LOW)
    still_within_target = evaluate_sla(target, created_at=_NOW, now=_NOW + timedelta(minutes=10))
    assert not still_within_target.response_breached
    assert not still_within_target.resolution_breached
