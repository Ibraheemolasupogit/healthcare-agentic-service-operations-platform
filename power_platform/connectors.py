"""The intended Power Platform <-> canonical service layer connector contract.

Nine representative operations a future custom connector would expose to
Power Automate/Power Apps. Every operation's `wraps_canonical`/`wraps_adapter`
names a real `business_process`/`dynamics365` callable (checked by
`power_platform.flow_validation`); example payloads below are built by
actually calling those callables against the existing deterministic
synthetic fixtures — not hand-typed — so they stay accurate as the
canonical model evolves.

No live HTTP endpoint, custom connector definition, or Dataverse plugin is
implemented here. See power_platform/connectors/README.md.
"""

from __future__ import annotations

from datetime import UTC, datetime

from business_process import (
    CaseStage,
    InvalidLifecycleTransitionError,
    Priority,
    ResolutionOutcome,
    ServiceCategory,
    assign_owner,
    case_to_dict,
    create_case,
    determine_escalation_reason,
    evaluate_sla,
    get_sla_target,
    resolve_case,
    route_category,
    transition_case,
)
from business_process.fixtures import build_synthetic_cases
from dynamics365 import dynamics_incident_to_dict, to_dynamics_incident
from power_platform.connector_spec import ConnectorOperation

_EXAMPLE_NOW = datetime(2026, 1, 12, 15, 0, tzinfo=UTC)


def _fixture(case_id: str):
    return next(case for case in build_synthetic_cases() if case.case_id == case_id)


def _build_create_case_operation() -> ConnectorOperation:
    example_case = create_case(
        case_id="SR-DS-9001",
        title="Shared workstation will not power on",
        description=(
            "Ward reception shared workstation does not power on after a scheduled restart."
        ),
        category=ServiceCategory.DIGITAL_SUPPORT,
        priority=Priority.MEDIUM,
        created_at=_EXAMPLE_NOW,
        actor="requestor",
    )
    return ConnectorOperation(
        name="create_case",
        description=(
            "Create a new canonical service request. Wraps business_process.create_case "
            "— the connector performs no validation or business logic of its own beyond "
            "required-field presence."
        ),
        wraps_canonical="create_case",
        wraps_adapter=None,
        request_schema={
            "title": "string, required",
            "description": "string, required",
            "category": "string, required — one of ServiceCategory",
            "priority": "string, required — one of Priority",
            "requestor": "string, required — role/team identifier, never a named individual",
        },
        response_schema={
            "case": "object — canonical Case, see business_process.serialization.case_to_dict"
        },
        example_request={
            "title": example_case.title,
            "description": example_case.description,
            "category": example_case.category.value,
            "priority": example_case.priority.value,
            "requestor": "requestor",
        },
        example_response={"case": case_to_dict(example_case)},
        idempotent=False,
        requires_correlation_id=True,
        caveat=(
            "Not idempotent by itself — the calling flow is responsible for de-duplicating "
            "retried submissions before calling this operation (see power_platform/README.md "
            "failure architecture)."
        ),
    )


def _build_transition_case_operation() -> ConnectorOperation:
    case = _fixture("SR-AS-1005")  # currently ROUTED — a legal next move exists
    before = case_to_dict(case)
    transition_case(
        case, CaseStage.IN_PROGRESS, at=_EXAMPLE_NOW, actor=case.owner or "", detail="Work started"
    )
    after = case_to_dict(case)

    invalid_example_case = _fixture("SR-AS-1005")
    try:
        transition_case(
            invalid_example_case,
            CaseStage.RESOLVED,
            at=_EXAMPLE_NOW,
            actor="test",
            detail="skip ahead",
        )
        error_example: dict[str, object] = {}  # pragma: no cover — ROUTED->RESOLVED is never legal
    except InvalidLifecycleTransitionError as exc:
        error_example = {"error": "InvalidLifecycleTransitionError", "detail": str(exc)}

    return ConnectorOperation(
        name="transition_case",
        description=(
            "Move a case to a new lifecycle stage. Wraps business_process.transition_case, "
            "which itself calls validate_transition — the connector never decides whether "
            "a move is legal."
        ),
        wraps_canonical="transition_case",
        wraps_adapter=None,
        request_schema={
            "case_id": "string, required",
            "to_stage": "string, required — one of CaseStage",
            "actor": "string, required",
            "detail": "string, required",
        },
        response_schema={
            "case": "object — canonical Case after the move (on success)",
            "error": (
                "string — exception type name (on failure, e.g. InvalidLifecycleTransitionError)"
            ),
        },
        example_request={
            "case_id": before["case_id"],
            "to_stage": "In Progress",
            "actor": case.owner,
            "detail": "Work started",
        },
        example_response={"case": after},
        idempotent=True,
        requires_correlation_id=True,
        caveat=(
            "Idempotent in effect, not by mechanism: replaying the same move once it has "
            "already happened raises InvalidLifecycleTransitionError rather than silently "
            f"succeeding twice — e.g. {error_example}. Callers should treat that specific "
            "error as 'already applied', not a failure."
        ),
    )


def _build_get_case_operation() -> ConnectorOperation:
    case = _fixture("SR-DS-1001")
    return ConnectorOperation(
        name="get_case",
        description="Retrieve current canonical case state by case_id.",
        wraps_canonical=None,
        wraps_adapter=None,
        request_schema={"case_id": "string, required"},
        response_schema={
            "case": "object — canonical Case, see business_process.serialization.case_to_dict"
        },
        example_request={"case_id": case.case_id},
        example_response={"case": case_to_dict(case)},
        idempotent=True,
        requires_correlation_id=False,
        caveat=(
            "No persistence layer exists yet (see business_process/README.md) — "
            "business_process holds no case store to read from. This contract is defined "
            "now so Power Platform integration design is not blocked on it, but it cannot "
            "be backed by real data until a persistence milestone lands. The example "
            "response is drawn from a synthetic fixture, not a live read."
        ),
    )


def _build_evaluate_sla_operation() -> ConnectorOperation:
    case = _fixture("SR-CE-1002")  # the escalated, SLA-breached fixture
    target = get_sla_target(case.category, case.priority)
    status = evaluate_sla(target, created_at=case.created_at, now=_EXAMPLE_NOW)
    return ConnectorOperation(
        name="evaluate_sla",
        description=(
            "Evaluate a case's current SLA status. Wraps business_process.sla.get_sla_target "
            "+ evaluate_sla — the connector performs no breach-threshold maths itself."
        ),
        wraps_canonical="evaluate_sla",
        wraps_adapter=None,
        request_schema={"case_id": "string, required"},
        response_schema={
            "response_due_at": "ISO-8601 timestamp",
            "resolution_due_at": "ISO-8601 timestamp",
            "response_breached": "boolean",
            "resolution_breached": "boolean",
        },
        example_request={"case_id": case.case_id},
        example_response={
            "response_due_at": status.response_due_at.isoformat(),
            "resolution_due_at": status.resolution_due_at.isoformat(),
            "response_breached": status.response_breached,
            "resolution_breached": status.resolution_breached,
        },
        idempotent=True,
        requires_correlation_id=False,
    )


def _build_evaluate_escalation_operation() -> ConnectorOperation:
    case = _fixture("SR-CE-1002")
    target = get_sla_target(case.category, case.priority)
    status = evaluate_sla(target, created_at=case.created_at, now=_EXAMPLE_NOW)
    reason = determine_escalation_reason(
        priority=case.priority, stage=case.stage, sla_status=status
    )
    return ConnectorOperation(
        name="evaluate_escalation",
        description=(
            "Determine whether a case currently qualifies for escalation, and why. Wraps "
            "business_process.should_escalate / determine_escalation_reason."
        ),
        wraps_canonical="determine_escalation_reason",
        wraps_adapter=None,
        request_schema={"case_id": "string, required"},
        response_schema={
            "should_escalate": "boolean",
            "reason": "string or null — one of EscalationReason",
        },
        example_request={"case_id": case.case_id},
        example_response={
            "should_escalate": reason is not None,
            "reason": reason.value if reason is not None else None,
        },
        idempotent=True,
        requires_correlation_id=False,
    )


def _build_resolve_case_operation() -> ConnectorOperation:
    case = _fixture("SR-AS-1005")
    transition_case(
        case, CaseStage.IN_PROGRESS, at=_EXAMPLE_NOW, actor=case.owner or "", detail="Work started"
    )
    resolve_case(
        case,
        at=_EXAMPLE_NOW,
        actor=case.owner or "",
        outcome=ResolutionOutcome.FIXED,
        notes="Restarted the affected service; timeout no longer reproduces.",
    )
    return ConnectorOperation(
        name="resolve_case",
        description=(
            "Resolve a case with an outcome and notes. Wraps business_process.resolve_case."
        ),
        wraps_canonical="resolve_case",
        wraps_adapter=None,
        request_schema={
            "case_id": "string, required",
            "outcome": "string, required — one of ResolutionOutcome",
            "notes": "string, required",
            "actor": "string, required",
        },
        response_schema={"case": "object — canonical Case after resolution"},
        example_request={
            "case_id": case.case_id,
            "outcome": "Fixed",
            "notes": "Restarted the affected service; timeout no longer reproduces.",
            "actor": case.owner,
        },
        example_response={"case": case_to_dict(case)},
        idempotent=True,
        requires_correlation_id=True,
        caveat=(
            "Idempotent via the same mechanism as transition_case — a repeat call once "
            "already resolved raises InvalidLifecycleTransitionError."
        ),
    )


def _build_list_service_categories_operation() -> ConnectorOperation:
    return ConnectorOperation(
        name="list_service_categories",
        description=(
            "List the canonical service taxonomy. A static read over "
            "business_process.taxonomy.ServiceCategory — no decision involved."
        ),
        wraps_canonical=None,
        wraps_adapter=None,
        request_schema={},
        response_schema={"categories": "array of string — ServiceCategory values"},
        example_request={},
        example_response={"categories": [c.value for c in ServiceCategory]},
        idempotent=True,
        requires_correlation_id=False,
    )


def _build_retrieve_queue_assignment_operation() -> ConnectorOperation:
    category = ServiceCategory.CLINICAL_EQUIPMENT
    queue = route_category(category)
    owner = assign_owner(queue)
    return ConnectorOperation(
        name="retrieve_queue_assignment",
        description=(
            "Given a service category, return the canonical queue and default owning team "
            "it routes to. Wraps business_process.route_category + assign_owner — the "
            "connector does not decide routing itself."
        ),
        wraps_canonical="route_category",
        wraps_adapter=None,
        request_schema={"category": "string, required — one of ServiceCategory"},
        response_schema={"queue": "string — one of Queue", "owner": "string — owning team"},
        example_request={"category": category.value},
        example_response={"queue": queue.value, "owner": owner},
        idempotent=True,
        requires_correlation_id=False,
        caveat=(
            "Returns the canonical Queue value, not a platform-specific display name — a "
            "caller that needs the Dynamics queue name should separately use the "
            "dynamics365 adapter (see docs/crm_schema_mapping.md)."
        ),
    )


def _build_sync_dynamics_representation_operation() -> ConnectorOperation:
    case = _fixture("SR-DS-1001")
    incident = to_dynamics_incident(case)
    return ConnectorOperation(
        name="sync_dynamics_representation",
        description=(
            "Push the current canonical case's Dynamics reference representation to the "
            "CRM boundary. Wraps dynamics365.to_dynamics_incident for translation; the "
            "actual CRM write is a future, live-connector concern — see "
            "integrations/README.md. Added beyond the 8 canonical-facing operations "
            "because both the intake and resolution-notification flows need a distinct "
            "step for 'persist the translated representation', which is CRM-facing rather "
            "than canonical-facing."
        ),
        wraps_canonical=None,
        wraps_adapter="to_dynamics_incident",
        request_schema={
            "incident": (
                "object — DynamicsIncident, see dynamics365.serialization.dynamics_incident_to_dict"
            )
        },
        response_schema={
            "incidentid": "string",
            "sync_status": "string — 'upserted' in this reference contract",
        },
        example_request={"incident": dynamics_incident_to_dict(incident)},
        example_response={"incidentid": incident.incidentid, "sync_status": "upserted"},
        idempotent=True,
        requires_correlation_id=True,
        caveat=(
            "No live Dataverse write occurs — 'upserted' here describes the intended real "
            "behaviour (keyed on ticketnumber, see docs/crm_schema_mapping.md Idempotency "
            "and external IDs), not an actual CRM call."
        ),
    )


CONNECTOR_OPERATIONS: tuple[ConnectorOperation, ...] = (
    _build_create_case_operation(),
    _build_transition_case_operation(),
    _build_get_case_operation(),
    _build_evaluate_sla_operation(),
    _build_evaluate_escalation_operation(),
    _build_resolve_case_operation(),
    _build_list_service_categories_operation(),
    _build_retrieve_queue_assignment_operation(),
    _build_sync_dynamics_representation_operation(),
)
"""The nine representative connector operations. The first eight match the
operations named in the Milestone 4 brief (`retrieve_queue_assignment` for
"retrieve queue assignment"); `sync_dynamics_representation` is a ninth,
explicitly justified addition — see its docstring above."""

CONNECTOR_OPERATIONS_BY_NAME: dict[str, ConnectorOperation] = {
    op.name: op for op in CONNECTOR_OPERATIONS
}

__all__ = ["CONNECTOR_OPERATIONS", "CONNECTOR_OPERATIONS_BY_NAME"]
