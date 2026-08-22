"""Validation for workflow specifications: structural completeness plus the
canonical-domain boundary rule.

This module only *introspects* `business_process` and `dynamics365` — it
checks that a named operation exists and is callable (`getattr`), and never
calls it. It never decides a lifecycle transition, SLA breach, escalation,
or routing outcome itself. See power_platform/README.md "Architecture rule
this package follows".
"""

from __future__ import annotations

import business_process
import dynamics365
from power_platform.connectors import CONNECTOR_OPERATIONS_BY_NAME
from power_platform.workflow_spec import (
    AdapterOperation,
    CanonicalOperation,
    StepKind,
    WorkflowSpecification,
    WorkflowStep,
)


class WorkflowValidationError(ValueError):
    """Raised when a `WorkflowSpecification` is structurally incomplete or
    violates the canonical-domain boundary rule."""


def _canonical_operation_exists(name: str) -> bool:
    try:
        operation = CanonicalOperation(name)
    except ValueError:
        return False
    return callable(getattr(business_process, operation.value, None))


def _adapter_operation_exists(name: str) -> bool:
    try:
        operation = AdapterOperation(name)
    except ValueError:
        return False
    return callable(getattr(dynamics365, operation.value, None))


def _validate_step(step: WorkflowStep, errors: list[str]) -> None:
    if not step.step_id:
        errors.append("a step is missing step_id")
    if not step.name:
        errors.append(f"{step.step_id}: name is required")
    if not step.description:
        errors.append(f"{step.step_id}: description is required")

    if step.kind is StepKind.CANONICAL_OPERATION:
        if not step.operation:
            errors.append(f"{step.step_id}: canonical_operation step requires 'operation'")
        elif not _canonical_operation_exists(step.operation):
            errors.append(
                f"{step.step_id}: '{step.operation}' is not a recognized, existing "
                "business_process operation — spec has drifted from the canonical package"
            )
    elif step.kind is StepKind.ADAPTER_OPERATION:
        if not step.operation:
            errors.append(f"{step.step_id}: adapter_operation step requires 'operation'")
        elif not _adapter_operation_exists(step.operation):
            errors.append(
                f"{step.step_id}: '{step.operation}' is not a recognized, existing "
                "dynamics365 operation — spec has drifted from the adapter package"
            )
    elif step.kind is StepKind.CONNECTOR_CALL:
        if not step.operation:
            errors.append(f"{step.step_id}: connector_call step requires 'operation'")
        elif step.operation not in CONNECTOR_OPERATIONS_BY_NAME:
            errors.append(
                f"{step.step_id}: '{step.operation}' is not a defined connector operation "
                "(see power_platform/connectors.py)"
            )
    elif step.kind is StepKind.CONDITION and step.operation is not None:
        # Structural boundary rule: a CONDITION step only branches on
        # already-computed prior state — it must never also claim to
        # perform a canonical/adapter/connector call itself.
        errors.append(
            f"{step.step_id}: condition steps must not carry an 'operation' "
            "(a condition may only branch on state already produced by a prior step)"
        )


def validate_workflow_spec(spec: WorkflowSpecification) -> None:
    """Raise `WorkflowValidationError` if `spec` is incomplete, internally
    inconsistent, or references a canonical/adapter operation that does not
    exist."""
    errors: list[str] = []

    for field_name, value in (
        ("flow_id", spec.flow_id),
        ("name", spec.name),
        ("description", spec.description),
        ("trigger_detail", spec.trigger_detail),
        ("idempotency_strategy", spec.idempotency_strategy),
        ("correlation_strategy", spec.correlation_strategy),
        ("failure_handling", spec.failure_handling),
    ):
        if not value:
            errors.append(f"{field_name} is required")

    if not spec.inputs:
        errors.append("must declare at least one input")
    if not spec.outputs:
        errors.append("must declare at least one output")
    if not spec.steps:
        errors.append("must declare at least one step")
    if not spec.audit_events:
        errors.append("must declare at least one audit event")

    step_ids = [step.step_id for step in spec.steps]
    if len(step_ids) != len(set(step_ids)):
        errors.append("duplicate step_id values in steps")

    for step in spec.steps:
        _validate_step(step, errors)

    if errors:
        raise WorkflowValidationError(f"{spec.flow_id}: " + "; ".join(errors))


__all__ = ["WorkflowValidationError", "validate_workflow_spec"]
