"""Tests for the typed workflow specification models and their serialization."""

from power_platform.workflow_spec import (
    StepKind,
    TriggerType,
    WorkflowSpecification,
    WorkflowStep,
)


def _sample_spec() -> WorkflowSpecification:
    return WorkflowSpecification(
        flow_id="test-flow-v1",
        name="Test Flow",
        description="A minimal flow for round-trip testing.",
        trigger_type=TriggerType.EVENT,
        trigger_detail="Test trigger",
        inputs=("a",),
        outputs=("b",),
        steps=(
            WorkflowStep(
                step_id="step-1",
                name="Step One",
                kind=StepKind.CANONICAL_OPERATION,
                description="Does a thing.",
                operation="create_case",
            ),
        ),
        idempotency_strategy="test strategy",
        correlation_strategy="test correlation",
        failure_handling="test failure handling",
        audit_events=("thing_happened",),
    )


def test_workflow_step_to_dict_and_from_dict_round_trip():
    step = WorkflowStep(
        step_id="s1",
        name="Step",
        kind=StepKind.APPROVAL,
        description="desc",
        requires_human=True,
        on_failure="fail note",
    )
    payload = step.to_dict()
    rebuilt = WorkflowStep.from_dict(payload)
    assert rebuilt == step


def test_workflow_step_optional_fields_default_sensibly():
    step = WorkflowStep(step_id="s1", name="Step", kind=StepKind.NOTIFICATION, description="desc")
    assert step.operation is None
    assert step.condition is None
    assert step.requires_human is False
    assert step.on_failure == ""


def test_workflow_specification_to_dict_and_from_dict_round_trip():
    spec = _sample_spec()
    payload = spec.to_dict()
    rebuilt = WorkflowSpecification.from_dict(payload)
    assert rebuilt == spec


def test_workflow_specification_to_dict_is_json_serializable():
    import json

    payload = _sample_spec().to_dict()
    reloaded = json.loads(json.dumps(payload))
    assert reloaded["flow_id"] == "test-flow-v1"
    assert reloaded["trigger_type"] == "event"
    assert reloaded["steps"][0]["kind"] == "canonical_operation"


def test_trigger_type_has_three_members():
    assert {member.value for member in TriggerType} == {"event", "schedule", "manual"}


def test_step_kind_covers_every_expected_kind():
    assert {member.value for member in StepKind} == {
        "condition",
        "canonical_operation",
        "adapter_operation",
        "connector_call",
        "approval",
        "notification",
        "audit_event",
    }
