"""Deterministic, rule-based case routing.

Maps each `ServiceCategory` onto a target queue and a default owning team.
Routing here is a fixed lookup table — no AI triage, no runtime learning.
AI-assisted triage is explicitly out of scope until a later milestone (see
docs/roadmap.md) and, per the platform's governance principles, will remain
subject to human-in-the-loop review even then.
"""

from __future__ import annotations

from enum import StrEnum

from business_process.taxonomy import ServiceCategory


class Queue(StrEnum):
    """Synthetic service operations queues that cases are routed into."""

    DIGITAL_SUPPORT = "Digital Support"
    CLINICAL_TECHNOLOGY = "Clinical Technology"
    FACILITIES_OPERATIONS = "Facilities Operations"
    IDENTITY_AND_ACCESS = "Identity and Access"
    APPLICATIONS = "Applications"
    DATA_SERVICES = "Data Services"


ROUTING_RULES: dict[ServiceCategory, Queue] = {
    ServiceCategory.DIGITAL_SUPPORT: Queue.DIGITAL_SUPPORT,
    ServiceCategory.CLINICAL_EQUIPMENT: Queue.CLINICAL_TECHNOLOGY,
    ServiceCategory.FACILITIES: Queue.FACILITIES_OPERATIONS,
    ServiceCategory.ACCESS_AND_IDENTITY: Queue.IDENTITY_AND_ACCESS,
    ServiceCategory.APPLICATION_SUPPORT: Queue.APPLICATIONS,
    ServiceCategory.DATA_AND_REPORTING: Queue.DATA_SERVICES,
}
"""One-to-one mapping: every category routes to exactly one queue."""

DEFAULT_QUEUE_OWNERS: dict[Queue, str] = {
    Queue.DIGITAL_SUPPORT: "digital-support-team",
    Queue.CLINICAL_TECHNOLOGY: "clinical-technology-team",
    Queue.FACILITIES_OPERATIONS: "facilities-operations-team",
    Queue.IDENTITY_AND_ACCESS: "identity-access-team",
    Queue.APPLICATIONS: "applications-team",
    Queue.DATA_SERVICES: "data-services-team",
}
"""Default owning team per queue. Team identifiers, not named individuals."""


def route_category(category: ServiceCategory) -> Queue:
    """Return the queue a case in `category` is routed to."""
    return ROUTING_RULES[category]


def assign_owner(queue: Queue) -> str:
    """Return the default owning team for `queue`."""
    return DEFAULT_QUEUE_OWNERS[queue]
