"""Canonical <-> Dynamics 365 mapping tables and pure translation functions.

Architecture rule (see docs/crm_schema_mapping.md): this module only
*translates* values it is given. It never imports or calls a
business_process decision function (`validate_transition`, `should_escalate`,
`evaluate_sla`, `route_category`, ...) — every value it needs (stage,
priority, queue, SLA due dates/breach flags) must already have been decided
by `business_process` and handed in by the caller. `tests/test_adapter_boundary.py`
enforces this at the source-code level.

No Dynamics SDK is used or required — every mapping here is a plain Python
dict/function over the reference models in `dynamics365.models`.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from business_process.models import Case, CaseEvent
from business_process.priority import Priority
from business_process.queues import Queue
from business_process.taxonomy import CaseStage
from dynamics365.models import (
    DynamicsIncident,
    DynamicsIncidentResolution,
    DynamicsPriorityCode,
    DynamicsStateCode,
    DynamicsStatusReason,
    DynamicsTimelineEntry,
)

_NAMESPACE = uuid.uuid5(
    uuid.NAMESPACE_DNS,
    "dynamics365.synthetic.healthcare-agentic-service-operations-platform",
)


class UnsupportedDynamicsValueError(ValueError):
    """Raised when a Dynamics-side value has no defined canonical mapping."""


# --- Priority ---------------------------------------------------------------

PRIORITY_TO_DYNAMICS: dict[Priority, DynamicsPriorityCode] = {
    Priority.CRITICAL: DynamicsPriorityCode.CRITICAL,
    Priority.HIGH: DynamicsPriorityCode.HIGH,
    Priority.MEDIUM: DynamicsPriorityCode.NORMAL,
    Priority.LOW: DynamicsPriorityCode.LOW,
}
"""1:1, non-lossy. See docs/crm_schema_mapping.md (this assumes a customized
4-value prioritycode option set; OOB Dataverse ships only 3 values)."""

DYNAMICS_TO_PRIORITY: dict[DynamicsPriorityCode, Priority] = {
    code: priority for priority, code in PRIORITY_TO_DYNAMICS.items()
}


def dynamics_priority_from(priority: Priority) -> DynamicsPriorityCode:
    """Translate a canonical `Priority` to its Dynamics `prioritycode`."""
    return PRIORITY_TO_DYNAMICS[priority]


def priority_from_dynamics(code: DynamicsPriorityCode) -> Priority:
    """Translate a Dynamics `prioritycode` to a canonical `Priority`."""
    try:
        return DYNAMICS_TO_PRIORITY[DynamicsPriorityCode(code)]
    except ValueError as exc:
        raise UnsupportedDynamicsValueError(f"Unsupported Dynamics prioritycode: {code!r}") from exc


# --- Lifecycle / status -------------------------------------------------

STAGE_TO_DYNAMICS_STATUS: dict[CaseStage, tuple[DynamicsStateCode, DynamicsStatusReason]] = {
    CaseStage.SUBMITTED: (DynamicsStateCode.ACTIVE, DynamicsStatusReason.NEW),
    CaseStage.CLASSIFIED: (DynamicsStateCode.ACTIVE, DynamicsStatusReason.CLASSIFIED),
    CaseStage.ROUTED: (DynamicsStateCode.ACTIVE, DynamicsStatusReason.ROUTED),
    CaseStage.IN_PROGRESS: (DynamicsStateCode.ACTIVE, DynamicsStatusReason.IN_PROGRESS),
    CaseStage.PENDING: (DynamicsStateCode.ACTIVE, DynamicsStatusReason.ON_HOLD),
    CaseStage.ESCALATED: (DynamicsStateCode.ACTIVE, DynamicsStatusReason.ESCALATED),
    # Dataverse has no native distinction between "resolved" and "closed" —
    # resolving an incident (statecode=Resolved) *is* closing it. Both
    # canonical stages therefore map forward to the same Dynamics state.
    CaseStage.RESOLVED: (DynamicsStateCode.RESOLVED, DynamicsStatusReason.PROBLEM_SOLVED),
    CaseStage.CLOSED: (DynamicsStateCode.RESOLVED, DynamicsStatusReason.PROBLEM_SOLVED),
}
"""Forward mapping only — see DYNAMICS_STATUS_TO_STAGE for the (lossy) reverse."""

DYNAMICS_STATUS_TO_STAGE: dict[tuple[DynamicsStateCode, DynamicsStatusReason], CaseStage] = {
    (DynamicsStateCode.ACTIVE, DynamicsStatusReason.NEW): CaseStage.SUBMITTED,
    (DynamicsStateCode.ACTIVE, DynamicsStatusReason.CLASSIFIED): CaseStage.CLASSIFIED,
    (DynamicsStateCode.ACTIVE, DynamicsStatusReason.ROUTED): CaseStage.ROUTED,
    (DynamicsStateCode.ACTIVE, DynamicsStatusReason.IN_PROGRESS): CaseStage.IN_PROGRESS,
    (DynamicsStateCode.ACTIVE, DynamicsStatusReason.ON_HOLD): CaseStage.PENDING,
    (DynamicsStateCode.ACTIVE, DynamicsStatusReason.ESCALATED): CaseStage.ESCALATED,
    # Deliberate, documented lossy choice: (Resolved, Problem Solved) always
    # reverse-maps to canonical RESOLVED, never CLOSED — further progression
    # to CLOSED cannot be inferred from Dynamics state alone. See
    # docs/crm_schema_mapping.md "Lifecycle / Status".
    (DynamicsStateCode.RESOLVED, DynamicsStatusReason.PROBLEM_SOLVED): CaseStage.RESOLVED,
    # (CANCELLED, *) is intentionally absent: Dynamics' native "Cancelled"
    # state has no canonical lifecycle equivalent in this milestone.
}


def dynamics_status_from(stage: CaseStage) -> tuple[DynamicsStateCode, DynamicsStatusReason]:
    """Translate a canonical `CaseStage` to a `(statecode, statuscode)` pair."""
    return STAGE_TO_DYNAMICS_STATUS[stage]


def stage_from_dynamics(
    statecode: DynamicsStateCode, statuscode: DynamicsStatusReason
) -> CaseStage:
    """Translate a Dynamics `(statecode, statuscode)` pair to a canonical `CaseStage`.

    Raises `UnsupportedDynamicsValueError` for combinations with no
    canonical equivalent (notably any `CANCELLED` state).
    """
    try:
        return DYNAMICS_STATUS_TO_STAGE[(statecode, statuscode)]
    except KeyError as exc:
        raise UnsupportedDynamicsValueError(
            f"Unsupported Dynamics (statecode, statuscode): ({statecode!r}, {statuscode!r})"
        ) from exc


# --- Queue / ownership --------------------------------------------------

QUEUE_TO_DYNAMICS_NAME: dict[Queue, str] = {
    Queue.DIGITAL_SUPPORT: "Digital Support Queue",
    Queue.CLINICAL_TECHNOLOGY: "Clinical Technology Queue",
    Queue.FACILITIES_OPERATIONS: "Facilities Operations Queue",
    Queue.IDENTITY_AND_ACCESS: "Identity and Access Queue",
    Queue.APPLICATIONS: "Applications Queue",
    Queue.DATA_SERVICES: "Data Services Queue",
}
"""1:1, non-lossy. A real deployment would use the queue's Dataverse GUID;
this reference adapter uses its display name — see docs/crm_schema_mapping.md."""

DYNAMICS_NAME_TO_QUEUE: dict[str, Queue] = {
    name: queue for queue, name in QUEUE_TO_DYNAMICS_NAME.items()
}


def dynamics_queue_name_from(queue: Queue) -> str:
    """Translate a canonical `Queue` to its Dynamics queue display name."""
    return QUEUE_TO_DYNAMICS_NAME[queue]


def queue_from_dynamics_name(name: str) -> Queue:
    """Translate a Dynamics queue display name to a canonical `Queue`."""
    try:
        return DYNAMICS_NAME_TO_QUEUE[name]
    except KeyError as exc:
        raise UnsupportedDynamicsValueError(f"Unsupported Dynamics queue name: {name!r}") from exc


# --- Deterministic synthetic identifiers ---------------------------------


def _deterministic_guid(seed: str) -> str:
    """A deterministic, GUID-shaped synthetic id derived from `seed`.

    Not a real Dataverse id-issuance algorithm — just reproducible enough
    for deterministic examples/tests. See "Idempotency and external IDs" in
    docs/crm_schema_mapping.md for why `ticketnumber` (not this id) is the
    identity that should be used for upserts.
    """
    return str(uuid.uuid5(_NAMESPACE, seed))


def _timeline_subject(event: CaseEvent) -> str:
    if event.event_type == "created":
        return "Case created"
    if event.event_type == "transition" and event.to_stage is not None:
        return f"Status changed to {event.to_stage.value}"
    return event.event_type.replace("_", " ").title()


# --- Translation: canonical -> Dynamics ----------------------------------


def to_dynamics_incident(
    case: Case,
    *,
    response_due_at: datetime | None = None,
    resolve_by_at: datetime | None = None,
    response_breached: bool | None = None,
    resolution_breached: bool | None = None,
) -> DynamicsIncident:
    """Translate a canonical `Case` to a reference `DynamicsIncident`.

    SLA due dates/breach flags are never computed here — pass in values
    already produced by `business_process.sla.evaluate_sla` (or leave them
    `None` if not yet known). See the module docstring's architecture rule.
    """
    statecode, statuscode = dynamics_status_from(case.stage)
    resolution = None
    if case.resolution is not None:
        resolution = DynamicsIncidentResolution(
            subject=case.resolution.value,
            description=case.resolution_notes or "",
        )
    return DynamicsIncident(
        incidentid=_deterministic_guid(case.case_id),
        ticketnumber=case.case_id,
        title=case.title,
        description=case.description,
        prioritycode=dynamics_priority_from(case.priority),
        statecode=statecode,
        statuscode=statuscode,
        owning_team=case.owner,
        queue_name=dynamics_queue_name_from(case.queue) if case.queue is not None else None,
        createdon=case.created_at,
        modifiedon=case.updated_at,
        responsebyapplicable=response_due_at,
        resolvebyapplicable=resolve_by_at,
        sla_response_breached=response_breached,
        sla_resolution_breached=resolution_breached,
        resolution=resolution,
    )


def to_dynamics_timeline(case: Case) -> list[DynamicsTimelineEntry]:
    """Translate a canonical `Case`'s audit history to reference timeline entries."""
    incidentid = _deterministic_guid(case.case_id)
    entries: list[DynamicsTimelineEntry] = []
    for index, event in enumerate(case.history):
        entries.append(
            DynamicsTimelineEntry(
                annotationid=_deterministic_guid(f"{case.case_id}:event:{index}"),
                regarding_incidentid=incidentid,
                subject=_timeline_subject(event),
                notetext=event.detail,
                createdon=event.timestamp,
                createdby=event.actor,
            )
        )
    return entries
