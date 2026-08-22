"""Canonical <-> Salesforce mapping tables and pure translation functions.

Architecture rule (see docs/crm_schema_mapping.md): this module only
*translates* values it is given. It never imports or calls a
business_process decision function (`validate_transition`, `should_escalate`,
`evaluate_sla`, `route_category`, ...) — every value it needs (stage,
priority, queue, SLA due dates/breach flags) must already have been decided
by `business_process` and handed in by the caller. `tests/test_adapter_boundary.py`
enforces this at the source-code level.

No Salesforce SDK/API client is used or required — every mapping here is a
plain Python dict/function over the reference models in `salesforce.models`.
"""

from __future__ import annotations

import hashlib
from datetime import datetime

from business_process.models import Case, CaseEvent
from business_process.priority import Priority
from business_process.queues import Queue
from business_process.taxonomy import CaseStage
from salesforce.models import (
    SalesforceCase,
    SalesforceCaseMilestone,
    SalesforceFeedItem,
    SalesforcePriority,
    SalesforceStatus,
)


class UnsupportedSalesforceValueError(ValueError):
    """Raised when a Salesforce-side value has no defined canonical mapping."""


# --- Priority ---------------------------------------------------------------

PRIORITY_TO_SALESFORCE: dict[Priority, SalesforcePriority] = {
    Priority.CRITICAL: SalesforcePriority.CRITICAL,
    Priority.HIGH: SalesforcePriority.HIGH,
    Priority.MEDIUM: SalesforcePriority.MEDIUM,
    Priority.LOW: SalesforcePriority.LOW,
}
"""1:1, non-lossy. Assumes a customized 4-value Priority picklist; OOB
Salesforce ships only 3 values (High/Medium/Low) — see docs/crm_schema_mapping.md."""

SALESFORCE_TO_PRIORITY: dict[SalesforcePriority, Priority] = {
    sf: canonical for canonical, sf in PRIORITY_TO_SALESFORCE.items()
}


def salesforce_priority_from(priority: Priority) -> SalesforcePriority:
    """Translate a canonical `Priority` to a Salesforce `Priority` picklist value."""
    return PRIORITY_TO_SALESFORCE[priority]


def priority_from_salesforce(value: SalesforcePriority | str) -> Priority:
    """Translate a Salesforce `Priority` picklist value to a canonical `Priority`."""
    try:
        return SALESFORCE_TO_PRIORITY[SalesforcePriority(value)]
    except ValueError as exc:
        raise UnsupportedSalesforceValueError(
            f"Unsupported Salesforce Priority: {value!r}"
        ) from exc


# --- Lifecycle / status -------------------------------------------------

STAGE_TO_SALESFORCE_STATUS: dict[CaseStage, SalesforceStatus] = {
    CaseStage.SUBMITTED: SalesforceStatus.NEW,
    CaseStage.CLASSIFIED: SalesforceStatus.CLASSIFIED,
    CaseStage.ROUTED: SalesforceStatus.ROUTED,
    CaseStage.IN_PROGRESS: SalesforceStatus.WORKING,
    CaseStage.PENDING: SalesforceStatus.ON_HOLD,
    CaseStage.ESCALATED: SalesforceStatus.ESCALATED,
    CaseStage.RESOLVED: SalesforceStatus.RESOLVED,
    CaseStage.CLOSED: SalesforceStatus.CLOSED,
}
"""1:1, non-lossy in both directions — unlike Dynamics' two-tier state/status
model, Salesforce's single flat Status picklist needs no stage collapsing."""

SALESFORCE_STATUS_TO_STAGE: dict[SalesforceStatus, CaseStage] = {
    status: stage for stage, status in STAGE_TO_SALESFORCE_STATUS.items()
}


def salesforce_status_from(stage: CaseStage) -> SalesforceStatus:
    """Translate a canonical `CaseStage` to a Salesforce `Status` picklist value."""
    return STAGE_TO_SALESFORCE_STATUS[stage]


def stage_from_salesforce(status: SalesforceStatus | str) -> CaseStage:
    """Translate a Salesforce `Status` picklist value to a canonical `CaseStage`."""
    try:
        return SALESFORCE_STATUS_TO_STAGE[SalesforceStatus(status)]
    except ValueError as exc:
        raise UnsupportedSalesforceValueError(f"Unsupported Salesforce Status: {status!r}") from exc


# --- Queue / ownership --------------------------------------------------

QUEUE_TO_SALESFORCE_NAME: dict[Queue, str] = {
    Queue.DIGITAL_SUPPORT: "Digital_Support_Queue",
    Queue.CLINICAL_TECHNOLOGY: "Clinical_Technology_Queue",
    Queue.FACILITIES_OPERATIONS: "Facilities_Operations_Queue",
    Queue.IDENTITY_AND_ACCESS: "Identity_and_Access_Queue",
    Queue.APPLICATIONS: "Applications_Queue",
    Queue.DATA_SERVICES: "Data_Services_Queue",
}
"""1:1, non-lossy. Represents each queue's `Group.DeveloperName`; a real
deployment would resolve this to the Group's record Id. See docs/crm_schema_mapping.md."""

SALESFORCE_NAME_TO_QUEUE: dict[str, Queue] = {
    name: queue for queue, name in QUEUE_TO_SALESFORCE_NAME.items()
}


def salesforce_queue_name_from(queue: Queue) -> str:
    """Translate a canonical `Queue` to its Salesforce Queue `DeveloperName`."""
    return QUEUE_TO_SALESFORCE_NAME[queue]


def queue_from_salesforce_name(name: str) -> Queue:
    """Translate a Salesforce Queue `DeveloperName` to a canonical `Queue`."""
    try:
        return SALESFORCE_NAME_TO_QUEUE[name]
    except KeyError as exc:
        raise UnsupportedSalesforceValueError(
            f"Unsupported Salesforce queue name: {name!r}"
        ) from exc


# --- Deterministic synthetic identifiers ---------------------------------


def _deterministic_id(seed: str, *, prefix: str = "500") -> str:
    """A deterministic, Salesforce-Id-shaped synthetic id derived from `seed`.

    Not a real Salesforce id-issuance algorithm (Salesforce uses a base62
    scheme this does not replicate) — just reproducible enough for
    deterministic examples/tests. `prefix` mirrors the "key prefix" pattern
    real Salesforce ids use per object type ("500" for Case). See
    "Idempotency and external IDs" in docs/crm_schema_mapping.md for why
    `canonical_case_id` (not this id) is the identity used for upserts.
    """
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest().upper()
    return f"{prefix}{digest[:15]}"


def _deterministic_case_number(seed: str) -> str:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    number = int(digest[:8], 16) % 100_000_000
    return f"{number:08d}"


def _feed_item_body(event: CaseEvent) -> str:
    return event.detail


# --- Translation: canonical -> Salesforce --------------------------------


def to_salesforce_case(
    case: Case,
    *,
    first_response_target: datetime | None = None,
    resolution_target: datetime | None = None,
    first_response_breached: bool | None = None,
    resolution_breached: bool | None = None,
) -> SalesforceCase:
    """Translate a canonical `Case` to a reference `SalesforceCase`.

    SLA milestone dates/breach flags are never computed here — pass in
    values already produced by `business_process.sla.evaluate_sla` (or
    leave them `None` if not yet known). See the module docstring's
    architecture rule.
    """
    status = salesforce_status_from(case.stage)
    milestones: list[SalesforceCaseMilestone] = []
    if first_response_target is not None:
        milestones.append(
            SalesforceCaseMilestone(
                milestone_type="First Response",
                target_date=first_response_target,
                is_violated=bool(first_response_breached),
            )
        )
    if resolution_target is not None:
        milestones.append(
            SalesforceCaseMilestone(
                milestone_type="Resolution",
                target_date=resolution_target,
                is_violated=bool(resolution_breached),
            )
        )

    owner_seed = f"queue:{case.queue.value}" if case.queue is not None else "unassigned"
    return SalesforceCase(
        id=_deterministic_id(case.case_id),
        case_number=_deterministic_case_number(case.case_id),
        canonical_case_id=case.case_id,
        subject=case.title,
        description=case.description,
        priority=salesforce_priority_from(case.priority),
        status=status,
        is_closed=(status == SalesforceStatus.CLOSED),
        owner_id=_deterministic_id(owner_seed, prefix="00G"),
        queue_name=salesforce_queue_name_from(case.queue) if case.queue is not None else None,
        created_date=case.created_at,
        last_modified_date=case.updated_at,
        entitlement_name=(
            f"{case.category.value} {case.priority.value} Entitlement"
            if case.queue is not None
            else None
        ),
        milestones=tuple(milestones),
        resolution_code=case.resolution.value if case.resolution is not None else None,
        resolution_notes=case.resolution_notes,
        closed_date=case.updated_at if status == SalesforceStatus.CLOSED else None,
    )


def to_salesforce_feed(case: Case) -> list[SalesforceFeedItem]:
    """Translate a canonical `Case`'s audit history to reference Chatter feed items."""
    parent_id = _deterministic_id(case.case_id)
    items: list[SalesforceFeedItem] = []
    for index, event in enumerate(case.history):
        items.append(
            SalesforceFeedItem(
                feed_item_id=_deterministic_id(f"{case.case_id}:event:{index}", prefix="0D5"),
                parent_id=parent_id,
                body=_feed_item_body(event),
                created_by=event.actor,
                created_date=event.timestamp,
            )
        )
    return items
