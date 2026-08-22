"""Tests for the Salesforce reference adapter."""

import json
from datetime import UTC, datetime

import pytest

from business_process import (
    CaseStage,
    Priority,
    Queue,
    ResolutionOutcome,
    ServiceCategory,
    classify_and_route,
    close_case,
    create_case,
    resolve_case,
    start_work,
)
from salesforce.mapping import (
    PRIORITY_TO_SALESFORCE,
    QUEUE_TO_SALESFORCE_NAME,
    SALESFORCE_NAME_TO_QUEUE,
    STAGE_TO_SALESFORCE_STATUS,
    UnsupportedSalesforceValueError,
    priority_from_salesforce,
    queue_from_salesforce_name,
    salesforce_priority_from,
    salesforce_queue_name_from,
    salesforce_status_from,
    stage_from_salesforce,
    to_salesforce_case,
    to_salesforce_feed,
)
from salesforce.models import SalesforceStatus
from salesforce.serialization import salesforce_case_to_dict, salesforce_feed_item_to_dict

_T0 = datetime(2026, 1, 12, 9, 0, tzinfo=UTC)


def _routed_case(**overrides):
    defaults = dict(
        case_id="SR-TEST-SF-0001",
        title="Test case",
        description="A test case description.",
        category=ServiceCategory.DIGITAL_SUPPORT,
        priority=Priority.MEDIUM,
        created_at=_T0,
        actor="requestor",
    )
    defaults.update(overrides)
    case = create_case(**defaults)
    classify_and_route(case, at=_T0, actor="intake-system")
    return case


# --- Priority -----------------------------------------------------------


def test_every_canonical_priority_has_a_salesforce_mapping():
    assert set(PRIORITY_TO_SALESFORCE.keys()) == set(Priority)
    assert len(set(PRIORITY_TO_SALESFORCE.values())) == 4  # non-lossy


def test_priority_round_trips_through_salesforce():
    for priority in Priority:
        value = salesforce_priority_from(priority)
        assert priority_from_salesforce(value) is priority


def test_unsupported_salesforce_priority_raises():
    with pytest.raises(UnsupportedSalesforceValueError):
        priority_from_salesforce("Nonexistent")


# --- Lifecycle / status ---------------------------------------------------


def test_every_canonical_stage_has_a_distinct_salesforce_status():
    assert set(STAGE_TO_SALESFORCE_STATUS.keys()) == set(CaseStage)
    assert len(set(STAGE_TO_SALESFORCE_STATUS.values())) == 8  # 1:1, no collapsing


def test_every_stage_round_trips_through_salesforce_status():
    for stage in CaseStage:
        status = salesforce_status_from(stage)
        assert stage_from_salesforce(status) is stage


def test_resolved_and_closed_map_to_distinct_salesforce_statuses():
    assert salesforce_status_from(CaseStage.RESOLVED) != salesforce_status_from(CaseStage.CLOSED)
    assert salesforce_status_from(CaseStage.CLOSED) is SalesforceStatus.CLOSED


def test_unsupported_salesforce_status_raises():
    with pytest.raises(UnsupportedSalesforceValueError):
        stage_from_salesforce("Nonexistent Status")


# --- Queue ----------------------------------------------------------------


def test_every_queue_has_a_salesforce_name_and_round_trips():
    assert set(QUEUE_TO_SALESFORCE_NAME.keys()) == set(Queue)
    for queue in Queue:
        name = salesforce_queue_name_from(queue)
        assert queue_from_salesforce_name(name) is queue


def test_unsupported_salesforce_queue_name_raises():
    with pytest.raises(UnsupportedSalesforceValueError):
        queue_from_salesforce_name("Some_Unknown_Queue")
    assert "Some_Unknown_Queue" not in SALESFORCE_NAME_TO_QUEUE


# --- to_salesforce_case ----------------------------------------------------


def test_to_salesforce_case_preserves_canonical_case_identity():
    case = _routed_case()
    sf_case = to_salesforce_case(case)
    assert sf_case.canonical_case_id == case.case_id


def test_to_salesforce_case_is_deterministic():
    case = _routed_case()
    first = to_salesforce_case(case)
    second = to_salesforce_case(case)
    assert first == second
    assert first.id == second.id


def test_different_cases_get_different_deterministic_ids():
    a = to_salesforce_case(_routed_case(case_id="SR-TEST-SF-0001"))
    b = to_salesforce_case(_routed_case(case_id="SR-TEST-SF-0002"))
    assert a.id != b.id
    assert a.case_number != b.case_number


def test_to_salesforce_case_maps_queue_and_is_closed_flag():
    case = _routed_case(category=ServiceCategory.CLINICAL_EQUIPMENT)
    sf_case = to_salesforce_case(case)
    assert sf_case.queue_name == "Clinical_Technology_Queue"
    assert sf_case.is_closed is False


def test_to_salesforce_case_without_queue_leaves_queue_name_none():
    case = create_case(
        case_id="SR-TEST-SF-0003",
        title="Unrouted",
        description="Not yet routed.",
        category=ServiceCategory.FACILITIES,
        priority=Priority.LOW,
        created_at=_T0,
        actor="requestor",
    )
    sf_case = to_salesforce_case(case)
    assert sf_case.queue_name is None
    assert sf_case.entitlement_name is None


def test_to_salesforce_case_milestones_are_empty_when_no_sla_supplied():
    case = _routed_case()
    sf_case = to_salesforce_case(case)
    assert sf_case.milestones == ()


def test_to_salesforce_case_milestones_populated_when_sla_supplied():
    case = _routed_case()
    due = datetime(2026, 1, 12, 10, 0, tzinfo=UTC)
    sf_case = to_salesforce_case(
        case,
        first_response_target=due,
        resolution_target=due,
        first_response_breached=True,
        resolution_breached=False,
    )
    assert len(sf_case.milestones) == 2
    types = {m.milestone_type for m in sf_case.milestones}
    assert types == {"First Response", "Resolution"}
    first_response = next(m for m in sf_case.milestones if m.milestone_type == "First Response")
    assert first_response.is_violated is True


def test_to_salesforce_case_is_closed_true_only_for_closed_stage():
    case = _routed_case()
    start_work(case, at=_T0, actor=case.owner)
    resolve_case(case, at=_T0, actor=case.owner, outcome=ResolutionOutcome.FIXED, notes="Fixed.")
    resolved_sf = to_salesforce_case(case)
    assert resolved_sf.is_closed is False
    assert resolved_sf.closed_date is None

    close_case(case, at=_T0, actor=case.owner)
    closed_sf = to_salesforce_case(case)
    assert closed_sf.is_closed is True
    assert closed_sf.closed_date == case.updated_at


def test_to_salesforce_case_resolution_fields():
    case = _routed_case()
    start_work(case, at=_T0, actor=case.owner)
    resolve_case(
        case,
        at=_T0,
        actor=case.owner,
        outcome=ResolutionOutcome.WORKAROUND_PROVIDED,
        notes="Temporary fix.",
    )
    sf_case = to_salesforce_case(case)
    assert sf_case.resolution_code == "Workaround Provided"
    assert sf_case.resolution_notes == "Temporary fix."


# --- to_salesforce_feed -----------------------------------------------------


def test_to_salesforce_feed_has_one_item_per_case_event():
    case = _routed_case()
    feed = to_salesforce_feed(case)
    assert len(feed) == len(case.history)


def test_to_salesforce_feed_items_reference_the_same_case():
    case = _routed_case()
    sf_case = to_salesforce_case(case)
    feed = to_salesforce_feed(case)
    assert all(item.parent_id == sf_case.id for item in feed)


def test_to_salesforce_feed_is_deterministic():
    case = _routed_case()
    assert to_salesforce_feed(case) == to_salesforce_feed(case)


# --- Serialization ----------------------------------------------------------


def test_salesforce_case_to_dict_is_json_serializable():
    case = _routed_case()
    start_work(case, at=_T0, actor=case.owner)
    resolve_case(case, at=_T0, actor=case.owner, outcome=ResolutionOutcome.FIXED, notes="Done.")
    close_case(case, at=_T0, actor=case.owner)
    sf_case = to_salesforce_case(case)
    payload = salesforce_case_to_dict(sf_case)
    reloaded = json.loads(json.dumps(payload))
    assert reloaded["canonical_case_id"] == case.case_id
    assert reloaded["status"] == "Closed"
    assert reloaded["is_closed"] is True


def test_salesforce_feed_item_to_dict_is_json_serializable():
    case = _routed_case()
    item = to_salesforce_feed(case)[0]
    payload = salesforce_feed_item_to_dict(item)
    json.dumps(payload)  # must not raise
    assert payload["feed_item_type"] == "TextPost"
