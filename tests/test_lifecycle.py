"""Tests for case lifecycle transition rules."""

import pytest

from business_process import CaseStage
from business_process.lifecycle import (
    InvalidLifecycleTransitionError,
    can_transition,
    validate_transition,
)


def test_canonical_happy_path_is_allowed():
    path = [
        CaseStage.SUBMITTED,
        CaseStage.CLASSIFIED,
        CaseStage.ROUTED,
        CaseStage.IN_PROGRESS,
        CaseStage.RESOLVED,
        CaseStage.CLOSED,
    ]
    for current, target in zip(path, path[1:], strict=False):
        assert can_transition(current, target)
        validate_transition(current, target)  # should not raise


def test_pending_and_escalated_branches_from_in_progress_are_allowed():
    assert can_transition(CaseStage.IN_PROGRESS, CaseStage.PENDING)
    assert can_transition(CaseStage.IN_PROGRESS, CaseStage.ESCALATED)
    assert can_transition(CaseStage.PENDING, CaseStage.IN_PROGRESS)
    assert can_transition(CaseStage.PENDING, CaseStage.ESCALATED)
    assert can_transition(CaseStage.ESCALATED, CaseStage.IN_PROGRESS)
    assert can_transition(CaseStage.ESCALATED, CaseStage.RESOLVED)


def test_closed_is_terminal():
    for stage in CaseStage:
        assert not can_transition(CaseStage.CLOSED, stage)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (CaseStage.SUBMITTED, CaseStage.ROUTED),
        (CaseStage.SUBMITTED, CaseStage.RESOLVED),
        (CaseStage.CLASSIFIED, CaseStage.IN_PROGRESS),
        (CaseStage.ROUTED, CaseStage.PENDING),
        (CaseStage.RESOLVED, CaseStage.IN_PROGRESS),
        (CaseStage.CLOSED, CaseStage.SUBMITTED),
    ],
)
def test_skipping_or_reversing_stages_is_rejected(current, target):
    assert not can_transition(current, target)
    with pytest.raises(InvalidLifecycleTransitionError):
        validate_transition(current, target)


def test_every_non_closed_stage_has_at_least_one_allowed_transition():
    for stage in CaseStage:
        if stage is CaseStage.CLOSED:
            continue
        assert any(can_transition(stage, target) for target in CaseStage)
