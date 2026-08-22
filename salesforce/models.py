"""Typed, adapter-facing models mirroring Salesforce Service Cloud shapes.

These are plain reference representations only — they hold no behaviour and
enforce no business rule. See docs/crm_schema_mapping.md for the full
canonical-field-by-field mapping and its caveats. Python attribute names are
snake_case for idiomatic style; each field's real Salesforce API field name
is documented in docs/crm_schema_mapping.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class SalesforcePriority(StrEnum):
    """Reference `Case.Priority` picklist.

    Out-of-the-box Salesforce ships only 3 values (High/Medium/Low) — no
    native "Critical". Modelled as a 4-value picklist here (a common
    real-world customization) to avoid collapsing two canonical priorities
    together. Values are identical to canonical `Priority` today but kept
    as a distinct type deliberately: a real org's picklist is independently
    configurable and could diverge in wording. See docs/crm_schema_mapping.md.
    """

    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class SalesforceStatus(StrEnum):
    """Reference `Case.Status` picklist.

    Salesforce's `Status` is a single flat, fully customizable picklist
    (unlike Dynamics' two-tier state/status model), so all 8 canonical
    stages map onto 8 distinct values with no collapsing — see
    docs/crm_schema_mapping.md.
    """

    NEW = "New"
    CLASSIFIED = "Classified"
    ROUTED = "Routed"
    WORKING = "Working"
    ON_HOLD = "On Hold"
    ESCALATED = "Escalated"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


@dataclass(frozen=True, slots=True)
class SalesforceCaseMilestone:
    """Reference shape for one `CaseMilestone` record.

    Salesforce's native SLA mechanism is Entitlement Management
    (`Entitlement` + `CaseMilestone`), not flat due-date fields — this
    reference adapter produces one milestone per SLA dimension we track
    ("First Response", "Resolution"). See docs/crm_schema_mapping.md.
    """

    milestone_type: str
    target_date: datetime
    is_violated: bool
    completion_date: datetime | None = None


@dataclass(frozen=True, slots=True)
class SalesforceFeedItem:
    """Reference shape for one Chatter `FeedItem` on a Case.

    Salesforce's real case timeline is composed of several entities
    (`CaseComment`, `FeedItem`/`FeedComment`, `Task`, `EmailMessage`, ...).
    This adapter uses a single generic Chatter-post-style shape for every
    `CaseEvent` for simplicity — see docs/crm_schema_mapping.md.
    """

    feed_item_id: str
    parent_id: str
    body: str
    created_by: str
    created_date: datetime
    feed_item_type: str = "TextPost"


@dataclass(frozen=True, slots=True)
class SalesforceCase:
    """Reference shape for the Salesforce `Case` object.

    Field-by-field provenance (including real Salesforce API field names)
    is documented in docs/crm_schema_mapping.md. `canonical_case_id` is
    modelled as a custom external-id field
    (`Canonical_Case_Id__c`) — see "Idempotency and external IDs" there.
    """

    id: str
    case_number: str
    canonical_case_id: str
    subject: str
    description: str
    priority: SalesforcePriority
    status: SalesforceStatus
    is_closed: bool
    owner_id: str
    queue_name: str | None
    created_date: datetime
    last_modified_date: datetime
    entitlement_name: str | None = None
    milestones: tuple[SalesforceCaseMilestone, ...] = ()
    resolution_code: str | None = None
    resolution_notes: str | None = None
    closed_date: datetime | None = None
