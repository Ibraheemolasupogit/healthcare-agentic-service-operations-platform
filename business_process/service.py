"""Case service operations: small, explicit functions over `Case`.

Each function performs one deterministic step (create, transition, route,
resolve, ...) and appends an audit event. There is no scheduler, no
persistence, and no implicit triggering — callers (tests, fixtures, and
eventually platform adapters) invoke these explicitly. This is intentionally
*not* a workflow engine.
"""

from __future__ import annotations

from datetime import datetime

from business_process.escalation import EscalationReason
from business_process.lifecycle import validate_transition
from business_process.models import Case, CaseEvent, ResolutionOutcome
from business_process.priority import Priority
from business_process.queues import assign_owner, route_category
from business_process.taxonomy import CaseStage, ServiceCategory


def create_case(
    *,
    case_id: str,
    title: str,
    description: str,
    category: ServiceCategory,
    priority: Priority,
    created_at: datetime,
    actor: str,
) -> Case:
    """Create a new case in the `SUBMITTED` stage with an initial audit event."""
    case = Case(
        case_id=case_id,
        title=title,
        description=description,
        category=category,
        priority=priority,
        created_at=created_at,
        updated_at=created_at,
        stage=CaseStage.SUBMITTED,
    )
    case.history.append(
        CaseEvent(
            timestamp=created_at,
            actor=actor,
            event_type="created",
            detail=(
                f"Case submitted in category '{category.value}' with priority '{priority.value}'"
            ),
            to_stage=CaseStage.SUBMITTED,
        )
    )
    return case


def transition_case(
    case: Case, to_stage: CaseStage, *, at: datetime, actor: str, detail: str
) -> Case:
    """Move `case` to `to_stage`, raising if the move is not allowed.

    Mutates and returns `case` for convenient chaining.
    """
    validate_transition(case.stage, to_stage)
    case.history.append(
        CaseEvent(
            timestamp=at,
            actor=actor,
            event_type="transition",
            detail=detail,
            from_stage=case.stage,
            to_stage=to_stage,
        )
    )
    case.stage = to_stage
    case.updated_at = at
    return case


def classify_and_route(case: Case, *, at: datetime, actor: str) -> Case:
    """Classify `case` into its category's queue and assign a default owner.

    Moves the case `SUBMITTED -> CLASSIFIED -> ROUTED`.
    """
    transition_case(
        case,
        CaseStage.CLASSIFIED,
        at=at,
        actor=actor,
        detail=f"Classified into '{case.category.value}'",
    )
    queue = route_category(case.category)
    owner = assign_owner(queue)
    case.queue = queue
    case.owner = owner
    transition_case(
        case,
        CaseStage.ROUTED,
        at=at,
        actor=actor,
        detail=f"Routed to '{queue.value}' queue, owner '{owner}'",
    )
    return case


def start_work(case: Case, *, at: datetime, actor: str) -> Case:
    """Move `case` from `ROUTED` (or back from `PENDING`/`ESCALATED`) to `IN_PROGRESS`."""
    return transition_case(case, CaseStage.IN_PROGRESS, at=at, actor=actor, detail="Work started")


def mark_pending(case: Case, *, at: datetime, actor: str, detail: str) -> Case:
    """Move `case` to `PENDING` (e.g. awaiting a third party)."""
    return transition_case(case, CaseStage.PENDING, at=at, actor=actor, detail=detail)


def escalate_case(case: Case, *, at: datetime, actor: str, reason: EscalationReason) -> Case:
    """Move `case` to `ESCALATED`, recording why."""
    return transition_case(
        case, CaseStage.ESCALATED, at=at, actor=actor, detail=f"Escalated: {reason.value}"
    )


def resolve_case(
    case: Case,
    *,
    at: datetime,
    actor: str,
    outcome: ResolutionOutcome,
    notes: str,
) -> Case:
    """Move `case` to `RESOLVED`, recording its outcome."""
    transition_case(
        case, CaseStage.RESOLVED, at=at, actor=actor, detail=f"Resolved: {outcome.value}"
    )
    case.resolution = outcome
    case.resolution_notes = notes
    return case


def close_case(case: Case, *, at: datetime, actor: str) -> Case:
    """Move `case` to `CLOSED`."""
    return transition_case(case, CaseStage.CLOSED, at=at, actor=actor, detail="Case closed")
