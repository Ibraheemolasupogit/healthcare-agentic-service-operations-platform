"""Typed models for Power Automate workflow specifications.

A `WorkflowSpecification` is a deterministic, version-controlled description
of a conceptual Power Automate flow — not a live flow, not an exported
`.zip` solution. It is deliberately declarative: every step that performs a
canonical decision names the exact `business_process` (or `dynamics365`)
callable it invokes, so `power_platform.flow_validation.validate_workflow_spec()`
can prove the flow references real, existing canonical logic instead of
inventing its own. See docs/architecture.md and power_platform/README.md
for the architecture rule this package follows.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class TriggerType(StrEnum):
    """How a flow starts."""

    EVENT = "event"
    SCHEDULE = "schedule"
    MANUAL = "manual"


class StepKind(StrEnum):
    """What kind of thing a workflow step does.

    `CANONICAL_OPERATION` and `ADAPTER_OPERATION` are the only kinds that
    may reference a decision-bearing callable, and only by name from the
    closed `CanonicalOperation` / `AdapterOperation` vocabularies below —
    never by embedding equivalent logic inline.
    """

    CONDITION = "condition"
    CANONICAL_OPERATION = "canonical_operation"
    ADAPTER_OPERATION = "adapter_operation"
    CONNECTOR_CALL = "connector_call"
    APPROVAL = "approval"
    NOTIFICATION = "notification"
    AUDIT_EVENT = "audit_event"


class CanonicalOperation(StrEnum):
    """The closed set of `business_process` callables a flow step may invoke.

    Every member's value is exactly the attribute name on the
    `business_process` package — `flow_validation` checks this by
    introspection (`getattr`), never by calling the function, so a flow
    spec cannot silently drift from what `business_process` actually
    exposes. This is the primary mechanism preventing Power Platform
    artefacts from reimplementing canonical rules under a different name.
    """

    CREATE_CASE = "create_case"
    CLASSIFY_AND_ROUTE = "classify_and_route"
    START_WORK = "start_work"
    MARK_PENDING = "mark_pending"
    ESCALATE_CASE = "escalate_case"
    RESOLVE_CASE = "resolve_case"
    CLOSE_CASE = "close_case"
    TRANSITION_CASE = "transition_case"
    VALIDATE_TRANSITION = "validate_transition"
    GET_SLA_TARGET = "get_sla_target"
    EVALUATE_SLA = "evaluate_sla"
    SHOULD_ESCALATE = "should_escalate"
    DETERMINE_ESCALATION_REASON = "determine_escalation_reason"
    ROUTE_CATEGORY = "route_category"


class AdapterOperation(StrEnum):
    """The closed set of `dynamics365` translation callables a flow step may invoke.

    Same rule as `CanonicalOperation`: values match real `dynamics365`
    attribute names, checked by introspection.
    """

    TO_DYNAMICS_INCIDENT = "to_dynamics_incident"
    TO_DYNAMICS_TIMELINE = "to_dynamics_timeline"


@dataclass(frozen=True, slots=True)
class WorkflowStep:
    """One step in a `WorkflowSpecification`."""

    step_id: str
    name: str
    kind: StepKind
    description: str
    operation: str | None = None
    condition: str | None = None
    requires_human: bool = False
    on_failure: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "name": self.name,
            "kind": self.kind.value,
            "description": self.description,
            "operation": self.operation,
            "condition": self.condition,
            "requires_human": self.requires_human,
            "on_failure": self.on_failure,
        }

    @staticmethod
    def from_dict(payload: dict[str, Any]) -> WorkflowStep:
        return WorkflowStep(
            step_id=payload["step_id"],
            name=payload["name"],
            kind=StepKind(payload["kind"]),
            description=payload["description"],
            operation=payload.get("operation"),
            condition=payload.get("condition"),
            requires_human=payload.get("requires_human", False),
            on_failure=payload.get("on_failure", ""),
        )


@dataclass(frozen=True, slots=True)
class WorkflowSpecification:
    """A deterministic, version-controlled reference Power Automate flow.

    Not a live flow and not an exported solution — a structured description
    of one, small enough to review in a diff. See
    power_platform/power_automate/README.md for the format and one prose
    write-up per flow.
    """

    flow_id: str
    name: str
    description: str
    trigger_type: TriggerType
    trigger_detail: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    steps: tuple[WorkflowStep, ...]
    idempotency_strategy: str
    correlation_strategy: str
    failure_handling: str
    audit_events: tuple[str, ...]
    version: str = "1.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "flow_id": self.flow_id,
            "name": self.name,
            "description": self.description,
            "trigger_type": self.trigger_type.value,
            "trigger_detail": self.trigger_detail,
            "inputs": list(self.inputs),
            "outputs": list(self.outputs),
            "steps": [step.to_dict() for step in self.steps],
            "idempotency_strategy": self.idempotency_strategy,
            "correlation_strategy": self.correlation_strategy,
            "failure_handling": self.failure_handling,
            "audit_events": list(self.audit_events),
            "version": self.version,
        }

    @staticmethod
    def from_dict(payload: dict[str, Any]) -> WorkflowSpecification:
        return WorkflowSpecification(
            flow_id=payload["flow_id"],
            name=payload["name"],
            description=payload["description"],
            trigger_type=TriggerType(payload["trigger_type"]),
            trigger_detail=payload["trigger_detail"],
            inputs=tuple(payload["inputs"]),
            outputs=tuple(payload["outputs"]),
            steps=tuple(WorkflowStep.from_dict(s) for s in payload["steps"]),
            idempotency_strategy=payload["idempotency_strategy"],
            correlation_strategy=payload["correlation_strategy"],
            failure_handling=payload["failure_handling"],
            audit_events=tuple(payload["audit_events"]),
            version=payload.get("version", "1.0"),
        )


__all__ = [
    "AdapterOperation",
    "CanonicalOperation",
    "StepKind",
    "TriggerType",
    "WorkflowSpecification",
    "WorkflowStep",
]
