"""Tests for deterministic, rule-based case routing."""

from business_process import ROUTING_RULES, Queue, ServiceCategory, assign_owner, route_category
from business_process.queues import DEFAULT_QUEUE_OWNERS


def test_every_service_category_routes_to_exactly_one_queue():
    assert set(ROUTING_RULES.keys()) == set(ServiceCategory)
    assert set(ROUTING_RULES.values()) == set(Queue)


def test_routing_is_deterministic():
    for category in ServiceCategory:
        first = route_category(category)
        second = route_category(category)
        assert first is second


def test_clinical_equipment_routes_to_clinical_technology_queue():
    assert route_category(ServiceCategory.CLINICAL_EQUIPMENT) is Queue.CLINICAL_TECHNOLOGY


def test_every_queue_has_a_default_owner():
    assert set(DEFAULT_QUEUE_OWNERS.keys()) == set(Queue)
    for queue in Queue:
        owner = assign_owner(queue)
        assert isinstance(owner, str)
        assert owner
