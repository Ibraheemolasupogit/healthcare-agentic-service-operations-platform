"""Case lifecycle transition rules.

Defines which `CaseStage -> CaseStage` moves are allowed and rejects any
other move deterministically. This is deliberately *not* a workflow engine:
there is no scheduler, no persistence, and no side effects here — just a
pure function callers use to validate a move before applying it (see
`business_process.service.transition_case`).
"""

from __future__ import annotations

from business_process.taxonomy import CaseStage

ALLOWED_TRANSITIONS: dict[CaseStage, frozenset[CaseStage]] = {
    CaseStage.SUBMITTED: frozenset({CaseStage.CLASSIFIED}),
    CaseStage.CLASSIFIED: frozenset({CaseStage.ROUTED}),
    CaseStage.ROUTED: frozenset({CaseStage.IN_PROGRESS}),
    CaseStage.IN_PROGRESS: frozenset({CaseStage.PENDING, CaseStage.ESCALATED, CaseStage.RESOLVED}),
    CaseStage.PENDING: frozenset({CaseStage.IN_PROGRESS, CaseStage.ESCALATED}),
    CaseStage.ESCALATED: frozenset({CaseStage.IN_PROGRESS, CaseStage.RESOLVED}),
    CaseStage.RESOLVED: frozenset({CaseStage.CLOSED}),
    CaseStage.CLOSED: frozenset(),
}
"""Explicit allowed transitions. `CLOSED` is terminal."""


class InvalidLifecycleTransitionError(ValueError):
    """Raised when a case attempts a lifecycle move that is not allowed."""

    def __init__(self, current: CaseStage, target: CaseStage) -> None:
        super().__init__(
            f"Invalid case lifecycle transition: {current.value!r} -> {target.value!r}"
        )
        self.current = current
        self.target = target


def can_transition(current: CaseStage, target: CaseStage) -> bool:
    """Return whether moving from `current` to `target` is allowed."""
    return target in ALLOWED_TRANSITIONS[current]


def validate_transition(current: CaseStage, target: CaseStage) -> None:
    """Raise `InvalidLifecycleTransitionError` if the move is not allowed."""
    if not can_transition(current, target):
        raise InvalidLifecycleTransitionError(current, target)
