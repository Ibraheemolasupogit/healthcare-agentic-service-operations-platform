"""Tests for the Dynamics 365 reference adapter."""

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
from dynamics365.mapping import (
    DYNAMICS_NAME_TO_QUEUE,
    DYNAMICS_STATUS_TO_STAGE,
    PRIORITY_TO_DYNAMICS,
    QUEUE_TO_DYNAMICS_NAME,
    STAGE_TO_DYNAMICS_STATUS,
    UnsupportedDynamicsValueError,
    dynamics_priority_from,
    dynamics_queue_name_from,
    dynamics_status_from,
    priority_from_dynamics,
    queue_from_dynamics_name,
    stage_from_dynamics,
    to_dynamics_incident,
    to_dynamics_timeline,
)
from dynamics365.models import DynamicsStateCode, DynamicsStatusReason
from dynamics365.serialization import dynamics_incident_to_dict, dynamics_timeline_entry_to_dict

_T0 = datetime(2026, 1, 12, 9, 0, tzinfo=UTC)


def _routed_case(**overrides):
    defaults = dict(
        case_id="SR-TEST-D365-0001",
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


def test_every_canonical_priority_has_a_dynamics_mapping():
    assert set(PRIORITY_TO_DYNAMICS.keys()) == set(Priority)
    assert len(set(PRIORITY_TO_DYNAMICS.values())) == 4  # non-lossy: 4 distinct codes


def test_priority_round_trips_through_dynamics():
    for priority in Priority:
        code = dynamics_priority_from(priority)
        assert priority_from_dynamics(code) is priority


def test_unsupported_dynamics_prioritycode_raises():
    with pytest.raises(UnsupportedDynamicsValueError):
        priority_from_dynamics(99)  # type: ignore[arg-type]


# --- Lifecycle / status ---------------------------------------------------


def test_every_canonical_stage_has_a_forward_dynamics_mapping():
    assert set(STAGE_TO_DYNAMICS_STATUS.keys()) == set(CaseStage)


def test_resolved_and_closed_both_map_forward_to_dynamics_resolved_state():
    resolved = dynamics_status_from(CaseStage.RESOLVED)
    closed = dynamics_status_from(CaseStage.CLOSED)
    assert resolved == closed == (DynamicsStateCode.RESOLVED, DynamicsStatusReason.PROBLEM_SOLVED)


def test_reverse_mapping_of_dynamics_resolved_state_defaults_to_canonical_resolved():
    stage = stage_from_dynamics(DynamicsStateCode.RESOLVED, DynamicsStatusReason.PROBLEM_SOLVED)
    assert stage is CaseStage.RESOLVED  # documented, deliberate lossy choice


def test_active_stage_statuses_round_trip():
    for stage in (
        CaseStage.SUBMITTED,
        CaseStage.CLASSIFIED,
        CaseStage.ROUTED,
        CaseStage.IN_PROGRESS,
        CaseStage.PENDING,
        CaseStage.ESCALATED,
    ):
        statecode, statuscode = dynamics_status_from(stage)
        assert stage_from_dynamics(statecode, statuscode) is stage


def test_cancelled_dynamics_state_has_no_canonical_mapping():
    assert (
        DynamicsStateCode.CANCELLED,
        DynamicsStatusReason.CANCELLED,
    ) not in DYNAMICS_STATUS_TO_STAGE
    with pytest.raises(UnsupportedDynamicsValueError):
        stage_from_dynamics(DynamicsStateCode.CANCELLED, DynamicsStatusReason.CANCELLED)


# --- Queue ----------------------------------------------------------------


def test_every_queue_has_a_dynamics_name_and_round_trips():
    assert set(QUEUE_TO_DYNAMICS_NAME.keys()) == set(Queue)
    for queue in Queue:
        name = dynamics_queue_name_from(queue)
        assert queue_from_dynamics_name(name) is queue


def test_unsupported_dynamics_queue_name_raises():
    with pytest.raises(UnsupportedDynamicsValueError):
        queue_from_dynamics_name("Some Unknown Queue")
    assert "Some Unknown Queue" not in DYNAMICS_NAME_TO_QUEUE


# --- to_dynamics_incident --------------------------------------------------


def test_to_dynamics_incident_preserves_canonical_case_identity():
    case = _routed_case()
    incident = to_dynamics_incident(case)
    assert incident.ticketnumber == case.case_id


def test_to_dynamics_incident_is_deterministic():
    case = _routed_case()
    first = to_dynamics_incident(case)
    second = to_dynamics_incident(case)
    assert first == second
    assert first.incidentid == second.incidentid


def test_different_cases_get_different_deterministic_incident_ids():
    a = to_dynamics_incident(_routed_case(case_id="SR-TEST-D365-0001"))
    b = to_dynamics_incident(_routed_case(case_id="SR-TEST-D365-0002"))
    assert a.incidentid != b.incidentid


def test_to_dynamics_incident_maps_queue_and_owner():
    case = _routed_case(category=ServiceCategory.CLINICAL_EQUIPMENT)
    incident = to_dynamics_incident(case)
    assert incident.queue_name == "Clinical Technology Queue"
    assert incident.owning_team == "clinical-technology-team"


def test_to_dynamics_incident_without_queue_leaves_queue_name_none():
    case = create_case(
        case_id="SR-TEST-D365-0003",
        title="Unrouted",
        description="Not yet routed.",
        category=ServiceCategory.FACILITIES,
        priority=Priority.LOW,
        created_at=_T0,
        actor="requestor",
    )
    incident = to_dynamics_incident(case)
    assert incident.queue_name is None
    assert incident.owning_team is None


def test_to_dynamics_incident_sla_fields_are_none_when_not_supplied():
    case = _routed_case()
    incident = to_dynamics_incident(case)
    assert incident.responsebyapplicable is None
    assert incident.resolvebyapplicable is None
    assert incident.sla_response_breached is None
    assert incident.sla_resolution_breached is None


def test_to_dynamics_incident_sla_fields_pass_through_when_supplied():
    case = _routed_case()
    due = datetime(2026, 1, 12, 10, 0, tzinfo=UTC)
    incident = to_dynamics_incident(
        case,
        response_due_at=due,
        resolve_by_at=due,
        response_breached=True,
        resolution_breached=False,
    )
    assert incident.responsebyapplicable == due
    assert incident.sla_response_breached is True
    assert incident.sla_resolution_breached is False


def test_to_dynamics_incident_resolution_is_none_until_resolved():
    case = _routed_case()
    assert to_dynamics_incident(case).resolution is None


def test_to_dynamics_incident_resolution_is_populated_when_resolved():
    case = _routed_case()
    start_work(case, at=_T0, actor=case.owner)
    resolve_case(case, at=_T0, actor=case.owner, outcome=ResolutionOutcome.FIXED, notes="Fixed it.")
    incident = to_dynamics_incident(case)
    assert incident.resolution is not None
    assert incident.resolution.subject == "Fixed"
    assert incident.resolution.description == "Fixed it."


# --- to_dynamics_timeline --------------------------------------------------


def test_to_dynamics_timeline_has_one_entry_per_case_event():
    case = _routed_case()
    timeline = to_dynamics_timeline(case)
    assert len(timeline) == len(case.history)


def test_to_dynamics_timeline_entries_reference_the_same_incident():
    case = _routed_case()
    incident = to_dynamics_incident(case)
    timeline = to_dynamics_timeline(case)
    assert all(entry.regarding_incidentid == incident.incidentid for entry in timeline)


def test_to_dynamics_timeline_is_deterministic():
    case = _routed_case()
    assert to_dynamics_timeline(case) == to_dynamics_timeline(case)


def test_timeline_subject_humanizes_an_unrecognized_event_type():
    # business_process only ever produces "created"/"transition" events
    # today, but the timeline subject fallback exists for future event
    # types — exercise it directly rather than leaving it untested.
    from business_process.models import CaseEvent
    from dynamics365.mapping import _timeline_subject

    event = CaseEvent(timestamp=_T0, actor="system", event_type="custom_note", detail="A note.")
    assert _timeline_subject(event) == "Custom Note"


# --- Serialization ----------------------------------------------------------


def test_dynamics_incident_to_dict_is_json_serializable():
    case = _routed_case()
    start_work(case, at=_T0, actor=case.owner)
    resolve_case(case, at=_T0, actor=case.owner, outcome=ResolutionOutcome.FIXED, notes="Done.")
    close_case(case, at=_T0, actor=case.owner)
    incident = to_dynamics_incident(case)
    payload = dynamics_incident_to_dict(incident)
    reloaded = json.loads(json.dumps(payload))
    assert reloaded["ticketnumber"] == case.case_id
    assert reloaded["statuscode"] == "Problem Solved"
    assert reloaded["resolution"]["subject"] == "Fixed"


def test_dynamics_timeline_entry_to_dict_is_json_serializable():
    case = _routed_case()
    entry = to_dynamics_timeline(case)[0]
    payload = dynamics_timeline_entry_to_dict(entry)
    json.dumps(payload)  # must not raise
    assert payload["subject"] == "Case created"
