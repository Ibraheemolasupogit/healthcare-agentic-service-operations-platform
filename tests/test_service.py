"""Tests for the case service operations (create, transition, route, resolve)."""

from datetime import UTC, datetime

import pytest

from business_process import (
    CaseStage,
    InvalidLifecycleTransitionError,
    Priority,
    Queue,
    ResolutionOutcome,
    ServiceCategory,
    classify_and_route,
    close_case,
    create_case,
    mark_pending,
    resolve_case,
    start_work,
    transition_case,
)

_T0 = datetime(2026, 1, 12, 9, 0, tzinfo=UTC)


def _new_case(**overrides):
    defaults = dict(
        case_id="SR-TEST-0001",
        title="Test case",
        description="A test case description.",
        category=ServiceCategory.DIGITAL_SUPPORT,
        priority=Priority.MEDIUM,
        created_at=_T0,
        actor="requestor",
    )
    defaults.update(overrides)
    return create_case(**defaults)


def test_create_case_starts_submitted_with_one_audit_event():
    case = _new_case()
    assert case.stage is CaseStage.SUBMITTED
    assert case.created_at == case.updated_at == _T0
    assert case.queue is None
    assert case.owner is None
    assert len(case.history) == 1
    assert case.history[0].event_type == "created"
    assert case.history[0].to_stage is CaseStage.SUBMITTED


def test_classify_and_route_assigns_queue_and_owner_deterministically():
    case = _new_case(category=ServiceCategory.CLINICAL_EQUIPMENT)
    classify_and_route(case, at=_T0, actor="intake-system")
    assert case.stage is CaseStage.ROUTED
    assert case.queue is Queue.CLINICAL_TECHNOLOGY
    assert case.owner == "clinical-technology-team"
    # created -> classified -> routed
    assert [event.to_stage for event in case.history] == [
        CaseStage.SUBMITTED,
        CaseStage.CLASSIFIED,
        CaseStage.ROUTED,
    ]


def test_full_happy_path_reaches_closed_with_resolution():
    case = _new_case()
    classify_and_route(case, at=_T0, actor="intake-system")
    start_work(case, at=_T0, actor=case.owner)
    resolve_case(case, at=_T0, actor=case.owner, outcome=ResolutionOutcome.FIXED, notes="Fixed it.")
    close_case(case, at=_T0, actor=case.owner)

    assert case.stage is CaseStage.CLOSED
    assert case.resolution is ResolutionOutcome.FIXED
    assert case.resolution_notes == "Fixed it."
    assert len(case.history) == 6


def test_mark_pending_and_resume_round_trip():
    case = _new_case()
    classify_and_route(case, at=_T0, actor="intake-system")
    start_work(case, at=_T0, actor=case.owner)
    mark_pending(case, at=_T0, actor=case.owner, detail="Waiting on third party.")
    assert case.stage is CaseStage.PENDING
    start_work(case, at=_T0, actor=case.owner)
    assert case.stage is CaseStage.IN_PROGRESS


def test_invalid_transition_raises_and_leaves_case_unchanged():
    case = _new_case()
    with pytest.raises(InvalidLifecycleTransitionError):
        transition_case(case, CaseStage.RESOLVED, at=_T0, actor="requestor", detail="skip ahead")
    assert case.stage is CaseStage.SUBMITTED
    assert len(case.history) == 1


def test_transition_updates_updated_at():
    case = _new_case()
    later = _T0.replace(hour=10)
    transition_case(case, CaseStage.CLASSIFIED, at=later, actor="intake-system", detail="ok")
    assert case.updated_at == later
    assert case.created_at == _T0
