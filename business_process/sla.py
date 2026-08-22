"""Simple, configurable SLA model.

Deliberately platform-neutral and deliberately simple: fixed response and
resolution targets per priority, adjusted by a per-category multiplier. This
is not an attempt to reproduce Dynamics 365 or Salesforce SLA/entitlement
engines — see docs/business_process.md for the boundary this module sits
behind.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from business_process.priority import Priority
from business_process.taxonomy import ServiceCategory


@dataclass(frozen=True, slots=True)
class SLATarget:
    """Response and resolution targets, in minutes from case creation."""

    response_minutes: int
    resolution_minutes: int


_BASE_TARGETS: dict[Priority, SLATarget] = {
    Priority.CRITICAL: SLATarget(response_minutes=15, resolution_minutes=240),
    Priority.HIGH: SLATarget(response_minutes=30, resolution_minutes=480),
    Priority.MEDIUM: SLATarget(response_minutes=120, resolution_minutes=1440),
    Priority.LOW: SLATarget(response_minutes=480, resolution_minutes=4320),
}
"""Base targets by priority alone (response time is not category-adjusted)."""

_RESOLUTION_MULTIPLIER: dict[ServiceCategory, float] = {
    # Safety-adjacent equipment gets a tighter resolution target.
    ServiceCategory.CLINICAL_EQUIPMENT: 0.5,
    ServiceCategory.ACCESS_AND_IDENTITY: 0.75,
    ServiceCategory.DIGITAL_SUPPORT: 1.0,
    ServiceCategory.APPLICATION_SUPPORT: 1.0,
    ServiceCategory.FACILITIES: 1.25,
    # Least time-critical category gets the loosest resolution target.
    ServiceCategory.DATA_AND_REPORTING: 1.5,
}
"""Illustrative resolution-time adjustment per category, not a vendor spec."""


def get_sla_target(category: ServiceCategory, priority: Priority) -> SLATarget:
    """Return the SLA target for a given category/priority combination."""
    base = _BASE_TARGETS[priority]
    multiplier = _RESOLUTION_MULTIPLIER[category]
    return SLATarget(
        response_minutes=base.response_minutes,
        resolution_minutes=round(base.resolution_minutes * multiplier),
    )


@dataclass(frozen=True, slots=True)
class SLAStatus:
    """Point-in-time SLA evaluation for a single case."""

    response_due_at: datetime
    resolution_due_at: datetime
    response_breached: bool
    resolution_breached: bool


def evaluate_sla(
    target: SLATarget,
    *,
    created_at: datetime,
    now: datetime,
    first_response_at: datetime | None = None,
    resolved_at: datetime | None = None,
) -> SLAStatus:
    """Evaluate breach state for a case against its SLA target.

    If `first_response_at` / `resolved_at` are not yet known, `now` is used
    as the check time, so an in-flight case can already show as breached.
    """
    response_due_at = created_at + timedelta(minutes=target.response_minutes)
    resolution_due_at = created_at + timedelta(minutes=target.resolution_minutes)

    response_check_time = first_response_at or now
    resolution_check_time = resolved_at or now

    return SLAStatus(
        response_due_at=response_due_at,
        resolution_due_at=resolution_due_at,
        response_breached=response_check_time > response_due_at,
        resolution_breached=resolution_check_time > resolution_due_at,
    )
