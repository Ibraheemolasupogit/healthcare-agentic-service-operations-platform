"""Tests for the case priority scale."""

from business_process import PRIORITY_ORDER, Priority
from business_process.priority import priority_rank


def test_priority_has_four_levels_low_to_critical():
    assert PRIORITY_ORDER == (Priority.LOW, Priority.MEDIUM, Priority.HIGH, Priority.CRITICAL)


def test_priority_rank_is_ascending_with_urgency():
    ranks = [priority_rank(priority) for priority in PRIORITY_ORDER]
    assert ranks == sorted(ranks)
    assert priority_rank(Priority.LOW) < priority_rank(Priority.CRITICAL)
