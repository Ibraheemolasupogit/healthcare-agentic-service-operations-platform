"""Deterministic synthetic case fixtures spanning every service category.

All content here is fictional. No patient-identifiable data, real NHS
identifiers, or clinical diagnosis/treatment logic is used — see
docs/business_process.md and the root README disclaimer. Timestamps are
built from a fixed reference point, not wall-clock time, so
`build_synthetic_cases()` produces equivalent output on every call.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from business_process.escalation import EscalationReason
from business_process.models import Case, ResolutionOutcome
from business_process.priority import Priority
from business_process.service import (
    classify_and_route,
    close_case,
    create_case,
    escalate_case,
    mark_pending,
    resolve_case,
    start_work,
)
from business_process.taxonomy import ServiceCategory

# Arbitrary fixed reference date used only to keep fixtures deterministic —
# it does not correspond to a real incident date or NHS reporting period.
_REFERENCE_START = datetime(2026, 1, 12, 9, 0, tzinfo=UTC)


@dataclass(frozen=True, slots=True)
class CaseScenario:
    """A fixed, synthetic starting point for one fixture case."""

    case_id: str
    title: str
    description: str
    category: ServiceCategory
    priority: Priority


def _at(minutes: int) -> datetime:
    return _REFERENCE_START + timedelta(minutes=minutes)


def _owner_of(case: Case) -> str:
    assert case.owner is not None, "case must be routed before work can start"
    return case.owner


def build_synthetic_cases() -> list[Case]:
    """Build six deterministic fixture cases, one per service category.

    Each case is walked through a different, realistic slice of the
    lifecycle (closed, escalated, pending, and in-flight) to demonstrate the
    domain model rather than exhaustively covering every stage.
    """
    cases: list[Case] = []

    # 1. Digital Support — routine request, resolved and closed.
    case = create_case(
        case_id="SR-DS-1001",
        title="Laptop will not connect to corporate Wi-Fi",
        description=(
            "Staff laptop repeatedly fails to authenticate against the corporate "
            "wireless network after a recent OS update."
        ),
        category=ServiceCategory.DIGITAL_SUPPORT,
        priority=Priority.MEDIUM,
        created_at=_at(0),
        actor="requestor",
    )
    classify_and_route(case, at=_at(5), actor="intake-system")
    start_work(case, at=_at(20), actor=_owner_of(case))
    resolve_case(
        case,
        at=_at(90),
        actor=_owner_of(case),
        outcome=ResolutionOutcome.FIXED,
        notes="Reissued network profile; laptop reconnected successfully.",
    )
    close_case(case, at=_at(100), actor=_owner_of(case))
    cases.append(case)

    # 2. Clinical Equipment — critical priority, escalated on SLA resolution breach.
    case = create_case(
        case_id="SR-CE-1002",
        title="Infusion pump fleet firmware advisory",
        description=(
            "Manufacturer advisory received for an infusion pump model deployed "
            "across the trust; fleet firmware status needs review. No patient or "
            "usage data is involved."
        ),
        category=ServiceCategory.CLINICAL_EQUIPMENT,
        priority=Priority.CRITICAL,
        created_at=_at(0),
        actor="requestor",
    )
    classify_and_route(case, at=_at(5), actor="intake-system")
    start_work(case, at=_at(15), actor=_owner_of(case))
    escalate_case(
        case,
        at=_at(300),
        actor=_owner_of(case),
        reason=EscalationReason.SLA_RESOLUTION_BREACH,
    )
    cases.append(case)

    # 3. Facilities — low priority, pending on an external contractor.
    case = create_case(
        case_id="SR-FA-1003",
        title="Meeting room air conditioning fault",
        description=(
            "Air conditioning unit in a ground-floor meeting room is not cooling; "
            "an external contractor call-out is required."
        ),
        category=ServiceCategory.FACILITIES,
        priority=Priority.LOW,
        created_at=_at(0),
        actor="requestor",
    )
    classify_and_route(case, at=_at(10), actor="intake-system")
    start_work(case, at=_at(60), actor=_owner_of(case))
    mark_pending(
        case,
        at=_at(120),
        actor=_owner_of(case),
        detail="Awaiting external contractor call-out slot.",
    )
    cases.append(case)

    # 4. Access and Identity — high priority joiner request, resolved and closed.
    case = create_case(
        case_id="SR-AI-1004",
        title="New starter access provisioning request",
        description=(
            "Standard system access request for a new starter joining a clinical "
            "administration team, per the standard joiner checklist."
        ),
        category=ServiceCategory.ACCESS_AND_IDENTITY,
        priority=Priority.HIGH,
        created_at=_at(0),
        actor="requestor",
    )
    classify_and_route(case, at=_at(5), actor="intake-system")
    start_work(case, at=_at(30), actor=_owner_of(case))
    resolve_case(
        case,
        at=_at(45),
        actor=_owner_of(case),
        outcome=ResolutionOutcome.FIXED,
        notes="Standard access profile provisioned per joiner checklist.",
    )
    close_case(case, at=_at(50), actor=_owner_of(case))
    cases.append(case)

    # 5. Application Support — routed, work not yet started.
    case = create_case(
        case_id="SR-AS-1005",
        title="Rostering application intermittent timeout",
        description=(
            "Line-of-business rostering application intermittently times out when "
            "generating weekly rota exports."
        ),
        category=ServiceCategory.APPLICATION_SUPPORT,
        priority=Priority.MEDIUM,
        created_at=_at(0),
        actor="requestor",
    )
    classify_and_route(case, at=_at(8), actor="intake-system")
    cases.append(case)

    # 6. Data and Reporting — low priority, resolved with no action required.
    case = create_case(
        case_id="SR-DR-1006",
        title="Monthly synthetic activity report export request",
        description=(
            "Request for a scheduled export of aggregate, non-identifiable monthly "
            "service activity figures for internal review."
        ),
        category=ServiceCategory.DATA_AND_REPORTING,
        priority=Priority.LOW,
        created_at=_at(0),
        actor="requestor",
    )
    classify_and_route(case, at=_at(15), actor="intake-system")
    start_work(case, at=_at(240), actor=_owner_of(case))
    resolve_case(
        case,
        at=_at(300),
        actor=_owner_of(case),
        outcome=ResolutionOutcome.NO_ACTION_REQUIRED,
        notes="Report already covered by an existing scheduled export; requestor notified.",
    )
    close_case(case, at=_at(310), actor=_owner_of(case))
    cases.append(case)

    return cases
