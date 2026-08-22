"""Tests for workflow specification validation, including rejected specs."""

from dataclasses import replace

import pytest

from power_platform.flow_validation import WorkflowValidationError, validate_workflow_spec
from power_platform.flows import INTAKE_FLOW
from power_platform.workflow_spec import StepKind, WorkflowStep


def test_valid_flow_passes():
    validate_workflow_spec(INTAKE_FLOW)  # must not raise


def test_missing_idempotency_strategy_is_rejected():
    broken = replace(INTAKE_FLOW, idempotency_strategy="")
    with pytest.raises(WorkflowValidationError, match="idempotency_strategy"):
        validate_workflow_spec(broken)


def test_missing_correlation_strategy_is_rejected():
    broken = replace(INTAKE_FLOW, correlation_strategy="")
    with pytest.raises(WorkflowValidationError, match="correlation_strategy"):
        validate_workflow_spec(broken)


def test_missing_failure_handling_is_rejected():
    broken = replace(INTAKE_FLOW, failure_handling="")
    with pytest.raises(WorkflowValidationError, match="failure_handling"):
        validate_workflow_spec(broken)


def test_no_steps_is_rejected():
    broken = replace(INTAKE_FLOW, steps=())
    with pytest.raises(WorkflowValidationError, match="at least one step"):
        validate_workflow_spec(broken)


def test_no_audit_events_is_rejected():
    broken = replace(INTAKE_FLOW, audit_events=())
    with pytest.raises(WorkflowValidationError, match="audit event"):
        validate_workflow_spec(broken)


def test_duplicate_step_ids_are_rejected():
    duplicated_step = replace(INTAKE_FLOW.steps[0], step_id=INTAKE_FLOW.steps[1].step_id)
    broken = replace(INTAKE_FLOW, steps=(duplicated_step, *INTAKE_FLOW.steps[1:]))
    with pytest.raises(WorkflowValidationError, match="duplicate step_id"):
        validate_workflow_spec(broken)


def test_step_with_missing_step_id_is_rejected():
    bad_step = WorkflowStep(step_id="", name="Bad", kind=StepKind.NOTIFICATION, description="desc")
    broken = replace(INTAKE_FLOW, steps=(bad_step,))
    with pytest.raises(WorkflowValidationError, match="missing step_id"):
        validate_workflow_spec(broken)


def test_step_with_missing_name_is_rejected():
    bad_step = WorkflowStep(step_id="bad", name="", kind=StepKind.NOTIFICATION, description="desc")
    broken = replace(INTAKE_FLOW, steps=(bad_step,))
    with pytest.raises(WorkflowValidationError, match="name is required"):
        validate_workflow_spec(broken)


def test_step_with_missing_description_is_rejected():
    bad_step = WorkflowStep(step_id="bad", name="Bad", kind=StepKind.NOTIFICATION, description="")
    broken = replace(INTAKE_FLOW, steps=(bad_step,))
    with pytest.raises(WorkflowValidationError, match="description is required"):
        validate_workflow_spec(broken)


def test_adapter_operation_step_with_no_operation_is_rejected():
    bad_step = WorkflowStep(
        step_id="bad", name="Bad", kind=StepKind.ADAPTER_OPERATION, description="desc"
    )
    broken = replace(INTAKE_FLOW, steps=(bad_step,))
    with pytest.raises(WorkflowValidationError, match="adapter_operation step requires"):
        validate_workflow_spec(broken)


def test_connector_call_step_with_no_operation_is_rejected():
    bad_step = WorkflowStep(
        step_id="bad", name="Bad", kind=StepKind.CONNECTOR_CALL, description="desc"
    )
    broken = replace(INTAKE_FLOW, steps=(bad_step,))
    with pytest.raises(WorkflowValidationError, match="connector_call step requires"):
        validate_workflow_spec(broken)


def test_canonical_operation_step_with_no_operation_is_rejected():
    bad_step = WorkflowStep(
        step_id="bad", name="Bad", kind=StepKind.CANONICAL_OPERATION, description="desc"
    )
    broken = replace(INTAKE_FLOW, steps=(bad_step,))
    with pytest.raises(WorkflowValidationError, match="requires 'operation'"):
        validate_workflow_spec(broken)


def test_canonical_operation_step_with_unknown_operation_name_is_rejected():
    bad_step = WorkflowStep(
        step_id="bad",
        name="Bad",
        kind=StepKind.CANONICAL_OPERATION,
        description="desc",
        operation="delete_the_database",
    )
    broken = replace(INTAKE_FLOW, steps=(bad_step,))
    with pytest.raises(WorkflowValidationError, match="not a recognized, existing"):
        validate_workflow_spec(broken)


def test_adapter_operation_step_with_unknown_operation_name_is_rejected():
    bad_step = WorkflowStep(
        step_id="bad",
        name="Bad",
        kind=StepKind.ADAPTER_OPERATION,
        description="desc",
        operation="to_salesforce_case",  # a real function, but not a dynamics365 one
    )
    broken = replace(INTAKE_FLOW, steps=(bad_step,))
    with pytest.raises(WorkflowValidationError, match="dynamics365 operation"):
        validate_workflow_spec(broken)


def test_connector_call_step_with_unknown_operation_name_is_rejected():
    bad_step = WorkflowStep(
        step_id="bad",
        name="Bad",
        kind=StepKind.CONNECTOR_CALL,
        description="desc",
        operation="delete_all_cases",
    )
    broken = replace(INTAKE_FLOW, steps=(bad_step,))
    with pytest.raises(WorkflowValidationError, match="not a defined connector operation"):
        validate_workflow_spec(broken)


def test_condition_step_carrying_an_operation_is_rejected():
    bad_step = WorkflowStep(
        step_id="bad",
        name="Bad",
        kind=StepKind.CONDITION,
        description="desc",
        operation="evaluate_sla",
    )
    broken = replace(INTAKE_FLOW, steps=(bad_step,))
    with pytest.raises(WorkflowValidationError, match="must not carry an 'operation'"):
        validate_workflow_spec(broken)


def test_missing_inputs_is_rejected():
    broken = replace(INTAKE_FLOW, inputs=())
    with pytest.raises(WorkflowValidationError, match="at least one input"):
        validate_workflow_spec(broken)


def test_missing_outputs_is_rejected():
    broken = replace(INTAKE_FLOW, outputs=())
    with pytest.raises(WorkflowValidationError, match="at least one output"):
        validate_workflow_spec(broken)
