"""Platform-neutral service taxonomy and case lifecycle definitions.

These types define the conceptual vocabulary shared across every platform
bounded context (Dynamics 365, Salesforce, Power Platform, Copilot Studio,
agentic AI) so that "what a case is" and "what stage it is in" are defined
once, independently of any single CRM/SaaS platform.

Scope note (Milestone 1): this module defines the taxonomy and lifecycle as
types only. It intentionally contains no workflow engine, no state-transition
rules, and no persistence — that is planned for a later milestone (see
docs/roadmap.md).
"""

from __future__ import annotations

from enum import StrEnum


class ServiceCategory(StrEnum):
    """Synthetic NHS-style service request categories."""

    DIGITAL_SUPPORT = "Digital Support"
    CLINICAL_EQUIPMENT = "Clinical Equipment"
    FACILITIES = "Facilities"
    ACCESS_AND_IDENTITY = "Access and Identity"
    APPLICATION_SUPPORT = "Application Support"
    DATA_AND_REPORTING = "Data and Reporting"


class CaseStage(StrEnum):
    """Conceptual case lifecycle stages, in order."""

    SUBMITTED = "Submitted"
    CLASSIFIED = "Classified"
    ROUTED = "Routed"
    IN_PROGRESS = "In Progress"
    PENDING = "Pending"
    ESCALATED = "Escalated"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


CASE_LIFECYCLE_ORDER: tuple[CaseStage, ...] = (
    CaseStage.SUBMITTED,
    CaseStage.CLASSIFIED,
    CaseStage.ROUTED,
    CaseStage.IN_PROGRESS,
    CaseStage.PENDING,
    CaseStage.ESCALATED,
    CaseStage.RESOLVED,
    CaseStage.CLOSED,
)
"""Reference ordering only — not an enforced state machine in this milestone."""
