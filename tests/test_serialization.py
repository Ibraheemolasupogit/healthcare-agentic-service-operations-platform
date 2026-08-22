"""Tests for JSON-safe case serialization."""

import json
from datetime import UTC, datetime

from business_process import (
    Priority,
    ResolutionOutcome,
    ServiceCategory,
    case_to_dict,
    classify_and_route,
    close_case,
    create_case,
    resolve_case,
    start_work,
)

_T0 = datetime(2026, 1, 12, 9, 0, tzinfo=UTC)


def test_case_to_dict_is_json_serializable_and_round_trips_key_fields():
    case = create_case(
        case_id="SR-TEST-0002",
        title="Serialization test case",
        description="Description.",
        category=ServiceCategory.FACILITIES,
        priority=Priority.LOW,
        created_at=_T0,
        actor="requestor",
    )
    classify_and_route(case, at=_T0, actor="intake-system")
    start_work(case, at=_T0, actor=case.owner)
    resolve_case(
        case,
        at=_T0,
        actor=case.owner,
        outcome=ResolutionOutcome.WORKAROUND_PROVIDED,
        notes="Temporary fix applied.",
    )
    close_case(case, at=_T0, actor=case.owner)

    payload = case_to_dict(case)
    serialized = json.dumps(payload)  # must not raise
    reloaded = json.loads(serialized)

    assert reloaded["case_id"] == "SR-TEST-0002"
    assert reloaded["category"] == "Facilities"
    assert reloaded["priority"] == "Low"
    assert reloaded["stage"] == "Closed"
    assert reloaded["resolution"] == "Workaround Provided"
    assert reloaded["queue"] == "Facilities Operations"
    assert len(reloaded["history"]) == len(case.history)
    assert reloaded["history"][0]["event_type"] == "created"


def test_case_to_dict_represents_unset_queue_and_resolution_as_none():
    case = create_case(
        case_id="SR-TEST-0003",
        title="Unrouted case",
        description="Description.",
        category=ServiceCategory.DATA_AND_REPORTING,
        priority=Priority.LOW,
        created_at=_T0,
        actor="requestor",
    )
    payload = case_to_dict(case)
    assert payload["queue"] is None
    assert payload["owner"] is None
    assert payload["resolution"] is None
    assert payload["resolution_notes"] is None
