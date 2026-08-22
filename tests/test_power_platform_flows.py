"""Tests for the four reference Power Automate flow specifications."""

import pytest

import business_process
import dynamics365
from power_platform.flow_validation import validate_workflow_spec
from power_platform.flows import (
    ALL_FLOWS,
    APPROVAL_FLOW,
    INTAKE_FLOW,
    RESOLUTION_NOTIFICATION_FLOW,
    SLA_MONITORING_FLOW,
)
from power_platform.workflow_spec import (
    AdapterOperation,
    CanonicalOperation,
    StepKind,
)


@pytest.mark.parametrize("flow", ALL_FLOWS, ids=[flow.flow_id for flow in ALL_FLOWS])
def test_every_flow_is_valid(flow):
    validate_workflow_spec(flow)  # must not raise


def test_every_canonical_operation_enum_value_resolves_on_business_process():
    """Drift guard: the closed CanonicalOperation vocabulary must stay in
    sync with what business_process actually exposes."""
    for operation in CanonicalOperation:
        assert callable(getattr(business_process, operation.value, None)), operation.value


def test_every_adapter_operation_enum_value_resolves_on_dynamics365():
    for operation in AdapterOperation:
        assert callable(getattr(dynamics365, operation.value, None)), operation.value


def test_all_flows_have_unique_flow_ids():
    ids = [flow.flow_id for flow in ALL_FLOWS]
    assert len(ids) == len(set(ids))


def test_condition_steps_never_carry_an_operation():
    for flow in ALL_FLOWS:
        for step in flow.steps:
            if step.kind is StepKind.CONDITION:
                assert step.operation is None, f"{flow.flow_id}/{step.step_id}"


# --- Intake flow: must decide classification/routing canonically -----------


def test_intake_flow_creates_case_via_canonical_operation():
    operations = {s.operation for s in INTAKE_FLOW.steps if s.kind is StepKind.CANONICAL_OPERATION}
    assert "create_case" in operations


def test_intake_flow_routes_via_canonical_operation_not_a_condition():
    canonical_ops = {
        s.operation for s in INTAKE_FLOW.steps if s.kind is StepKind.CANONICAL_OPERATION
    }
    assert "classify_and_route" in canonical_ops
    # No CONDITION step in this flow decides routing itself.
    for step in INTAKE_FLOW.steps:
        if step.kind is StepKind.CONDITION:
            assert "queue" not in (step.condition or "").lower()


def test_intake_flow_maps_to_dynamics_before_syncing_crm():
    step_ids = [s.step_id for s in INTAKE_FLOW.steps]
    assert step_ids.index("map-to-dynamics") < step_ids.index("sync-crm")


# --- SLA monitoring flow: must call evaluate_sla and escalation canonically


def test_sla_monitoring_flow_evaluates_sla_via_canonical_operation():
    canonical_ops = {
        s.operation for s in SLA_MONITORING_FLOW.steps if s.kind is StepKind.CANONICAL_OPERATION
    }
    assert "evaluate_sla" in canonical_ops
    assert "determine_escalation_reason" in canonical_ops


def test_sla_monitoring_flow_does_not_compute_breach_in_a_condition():
    for step in SLA_MONITORING_FLOW.steps:
        if step.kind is StepKind.CONDITION:
            lowered = (step.condition or "").lower()
            assert "breach" not in lowered
            assert "minute" not in lowered


def test_sla_monitoring_flow_escalates_only_after_condition_gate():
    step_ids = [s.step_id for s in SLA_MONITORING_FLOW.steps]
    assert step_ids.index("condition-escalate") < step_ids.index("escalate-case")


# --- Approval flow: human-in-the-loop gate ----------------------------------


def test_approval_flow_has_a_step_requiring_a_human():
    human_steps = [s for s in APPROVAL_FLOW.steps if s.requires_human]
    assert len(human_steps) == 1
    assert human_steps[0].kind is StepKind.APPROVAL


def test_approval_flow_records_audit_evidence_regardless_of_outcome():
    step_ids = [s.step_id for s in APPROVAL_FLOW.steps]
    # record-approval-audit happens before the approved/rejected branch.
    assert step_ids.index("record-approval-audit") < step_ids.index("condition-approved")


def test_approval_flow_does_not_model_clinical_treatment():
    text = " ".join(
        [APPROVAL_FLOW.description, APPROVAL_FLOW.trigger_detail]
        + [step.description for step in APPROVAL_FLOW.steps]
    ).lower()
    for forbidden in ("treatment", "diagnos", "patient"):
        assert forbidden not in text


# --- Resolution/closure flow -------------------------------------------------


def test_resolution_flow_closes_case_via_canonical_operation_last():
    assert RESOLUTION_NOTIFICATION_FLOW.steps[-1].operation == "close_case"
    assert RESOLUTION_NOTIFICATION_FLOW.steps[-1].kind is StepKind.CANONICAL_OPERATION


def test_resolution_flow_confirms_resolved_before_closing():
    step_ids = [s.step_id for s in RESOLUTION_NOTIFICATION_FLOW.steps]
    assert step_ids.index("confirm-resolved") < step_ids.index("close-case")


# --- No flow reimplements canonical rules -----------------------------------


def test_no_flow_step_description_or_condition_recomputes_sla_maths():
    forbidden_phrases = ("minutes since", "is overdue by", "response time >", "resolution time >")
    for flow in ALL_FLOWS:
        for step in flow.steps:
            text = f"{step.description} {step.condition or ''}".lower()
            for phrase in forbidden_phrases:
                assert phrase not in text, f"{flow.flow_id}/{step.step_id}"
