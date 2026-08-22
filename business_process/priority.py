"""Platform-neutral case priority."""

from __future__ import annotations

from enum import StrEnum


class Priority(StrEnum):
    """Case priority, independent of any CRM platform's priority field."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


PRIORITY_ORDER: tuple[Priority, ...] = (
    Priority.LOW,
    Priority.MEDIUM,
    Priority.HIGH,
    Priority.CRITICAL,
)
"""Ascending order of urgency, low to critical."""


def priority_rank(priority: Priority) -> int:
    """Return the ordinal rank of a priority (0 = lowest urgency)."""
    return PRIORITY_ORDER.index(priority)
