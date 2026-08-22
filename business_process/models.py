"""The canonical case aggregate: a synthetic healthcare service request.

`Case` and `CaseEvent` are the platform-neutral data model that a future
Dynamics 365 or Salesforce adapter would map onto its own entities/objects —
see docs/business_process.md for that boundary. Nothing in this module talks
to any CRM, queue, or clock; it is a plain data holder mutated only via
`business_process.service` functions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from business_process.priority import Priority
from business_process.queues import Queue
from business_process.taxonomy import CaseStage, ServiceCategory


class ResolutionOutcome(StrEnum):
    """How a case was resolved."""

    FIXED = "Fixed"
    WORKAROUND_PROVIDED = "Workaround Provided"
    DUPLICATE = "Duplicate"
    NOT_REPRODUCIBLE = "Not Reproducible"
    NO_ACTION_REQUIRED = "No Action Required"
    CANCELLED = "Cancelled"


@dataclass(frozen=True, slots=True)
class CaseEvent:
    """One immutable entry in a case's audit trail.

    This is the case-level audit *data model* only. Durable storage,
    tamper-evidence, and cross-case audit review are governance-domain
    concerns for a later milestone (see governance/README.md).
    """

    timestamp: datetime
    actor: str
    event_type: str
    detail: str
    from_stage: CaseStage | None = None
    to_stage: CaseStage | None = None


@dataclass(slots=True)
class Case:
    """A synthetic healthcare service request — the canonical unit of work."""

    case_id: str
    title: str
    description: str
    category: ServiceCategory
    priority: Priority
    created_at: datetime
    updated_at: datetime
    stage: CaseStage = CaseStage.SUBMITTED
    queue: Queue | None = None
    owner: str | None = None
    resolution: ResolutionOutcome | None = None
    resolution_notes: str | None = None
    history: list[CaseEvent] = field(default_factory=list)
