"""Typed, adapter-facing models mirroring Dynamics 365 / Dataverse shapes.

These are plain reference representations only — they hold no behaviour and
enforce no business rule. See docs/crm_schema_mapping.md for the full
canonical-field-by-field mapping and its caveats.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum, StrEnum


class DynamicsPriorityCode(IntEnum):
    """Reference `prioritycode` option set.

    Out-of-the-box Dataverse incidents ship only 3 values (1=High,
    2=Normal, 3=Low) — no native "Critical". This reference mapping models
    a 4-value option set (a common real-world customization) so the
    canonical 4-level `Priority` survives the round trip without collapsing
    two canonical priorities onto one code. See docs/crm_schema_mapping.md.
    """

    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


class DynamicsStateCode(IntEnum):
    """The native, global `statecode` option set for `incident` (fixed, not customizable)."""

    ACTIVE = 0
    RESOLVED = 1
    CANCELLED = 2


class DynamicsStatusReason(StrEnum):
    """Reference `statuscode` (status reason) labels.

    Real Dataverse `statuscode` values are environment-customizable local
    option sets (small integers in a real environment); this reference
    adapter represents them as readable labels. `CANCELLED` has no
    canonical lifecycle equivalent and is intentionally not reachable from
    `business_process.CaseStage` — see docs/crm_schema_mapping.md.
    """

    NEW = "New"
    CLASSIFIED = "Classified"
    ROUTED = "Routed"
    IN_PROGRESS = "In Progress"
    ON_HOLD = "On Hold"
    ESCALATED = "Escalated"
    PROBLEM_SOLVED = "Problem Solved"
    CANCELLED = "Cancelled"


@dataclass(frozen=True, slots=True)
class DynamicsIncidentResolution:
    """Reference shape for the `incidentresolution` entity created on resolve."""

    subject: str
    description: str


@dataclass(frozen=True, slots=True)
class DynamicsTimelineEntry:
    """Reference shape for one Case Timeline entry.

    Dataverse's real Case Timeline aggregates several entity types
    (`annotation` notes, `task`/`phonecall`/`email` activities, ...). This
    adapter uses a single generic, `annotation`-style shape for every
    `CaseEvent` for simplicity — see docs/crm_schema_mapping.md.
    """

    annotationid: str
    regarding_incidentid: str
    subject: str
    notetext: str
    createdon: datetime
    createdby: str


@dataclass(frozen=True, slots=True)
class DynamicsIncident:
    """Reference shape for the Dataverse `incident` (Case) entity.

    Field-by-field provenance is documented in docs/crm_schema_mapping.md.
    `owning_team` and `queue_name` are adapter conveniences: real Dataverse
    tracks queue membership via a separate `queueitem` record and ownership
    via a polymorphic `ownerid` lookup to `systemuser`/`team`, neither of
    which this reference adapter models as a full related entity.
    """

    incidentid: str
    ticketnumber: str
    title: str
    description: str
    prioritycode: DynamicsPriorityCode
    statecode: DynamicsStateCode
    statuscode: DynamicsStatusReason
    owning_team: str | None
    queue_name: str | None
    createdon: datetime
    modifiedon: datetime
    responsebyapplicable: datetime | None = None
    resolvebyapplicable: datetime | None = None
    sla_response_breached: bool | None = None
    sla_resolution_breached: bool | None = None
    resolution: DynamicsIncidentResolution | None = None
