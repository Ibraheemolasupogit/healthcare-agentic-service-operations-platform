"""The four reference Power Automate flow specifications for Milestone 4.

Every `WorkflowSpecification` here is validated (see
tests/test_power_platform_flows.py) with
`power_platform.flow_validation.validate_workflow_spec`. Each step that
performs a canonical or Dynamics-representation decision names a real
`business_process`/`dynamics365` callable — see power_platform/README.md.
"""

from __future__ import annotations

from power_platform.workflow_spec import (
    StepKind,
    TriggerType,
    WorkflowSpecification,
    WorkflowStep,
)

INTAKE_FLOW = WorkflowSpecification(
    flow_id="power-automate-intake-v1",
    name="New Service Request Intake",
    description=(
        "Takes a new service request from Power Apps, Power Pages, or an inbound "
        "integration event, creates the canonical case, classifies and routes it, "
        "translates it into a Dynamics 365 reference representation, and "
        "acknowledges the requestor."
    ),
    trigger_type=TriggerType.EVENT,
    trigger_detail=(
        "Power Apps canvas app submission, Power Pages portal submission, or an "
        "inbound IntegrationEnvelope event with operation=create"
    ),
    inputs=("requestor", "title", "description", "category", "priority"),
    outputs=("canonical_case_id", "dynamics_incident_id", "acknowledgement_reference"),
    steps=(
        WorkflowStep(
            step_id="validate-input",
            name="Validate request fields",
            kind=StepKind.CONDITION,
            description=(
                "Confirm title/description are non-empty and category/priority are "
                "members of the canonical taxonomy before any case is created."
            ),
            condition=(
                "title and description non-empty; category in ServiceCategory; priority in Priority"
            ),
            on_failure=(
                "Return a validation error to the caller; no case is created; "
                "no audit event is raised."
            ),
        ),
        WorkflowStep(
            step_id="create-case",
            name="Create canonical case",
            kind=StepKind.CANONICAL_OPERATION,
            operation="create_case",
            description=(
                "Create the case in SUBMITTED stage via the connector boundary's "
                "create_case operation."
            ),
        ),
        WorkflowStep(
            step_id="classify-and-route",
            name="Classify and route",
            kind=StepKind.CANONICAL_OPERATION,
            operation="classify_and_route",
            description=(
                "Classify into CLASSIFIED then ROUTED using the canonical routing "
                "table; assigns queue and owner deterministically. This flow does "
                "not decide the queue itself."
            ),
        ),
        WorkflowStep(
            step_id="map-to-dynamics",
            name="Map to Dynamics representation",
            kind=StepKind.ADAPTER_OPERATION,
            operation="to_dynamics_incident",
            description=(
                "Translate the routed canonical case into a reference DynamicsIncident. "
                "No SLA fields are populated yet (not evaluated at intake)."
            ),
        ),
        WorkflowStep(
            step_id="map-timeline",
            name="Map audit timeline",
            kind=StepKind.ADAPTER_OPERATION,
            operation="to_dynamics_timeline",
            description=(
                "Translate the case's audit history so far into reference Dynamics "
                "timeline entries."
            ),
        ),
        WorkflowStep(
            step_id="sync-crm",
            name="Persist CRM representation",
            kind=StepKind.CONNECTOR_CALL,
            operation="sync_dynamics_representation",
            description=(
                "Push the translated representation to the CRM boundary via the connector contract."
            ),
            on_failure=(
                "Canonical case creation has already succeeded and is not rolled back. "
                "Raise a crm_sync_failed audit event and queue manual reconciliation — "
                "see 'CRM update failure after canonical success' in power_platform/README.md."
            ),
        ),
        WorkflowStep(
            step_id="acknowledge-requestor",
            name="Issue acknowledgement",
            kind=StepKind.NOTIFICATION,
            description=(
                "Notify the requestor that their case was received, with its "
                "canonical_case_id for tracking."
            ),
        ),
        WorkflowStep(
            step_id="audit-intake",
            name="Record intake audit evidence",
            kind=StepKind.AUDIT_EVENT,
            description=(
                "Record that intake completed, referencing canonical_case_id and correlation_id."
            ),
        ),
    ),
    idempotency_strategy=(
        "The caller (Power Apps/Power Pages/integration event) must supply a "
        "client-generated request token; the flow checks for an existing case "
        "created from the same token within a short window before calling "
        "create_case again, since create_case itself has no natural idempotency "
        "key (see power_platform/connectors.py create_case caveat)."
    ),
    correlation_strategy=(
        "correlation_id = integrations.envelope.new_correlation_id(f'intake:{request_token}'), "
        "generated once at validate-input and threaded through every subsequent step "
        "and audit event."
    ),
    failure_handling=(
        "Steps validate-input through classify-and-route must all succeed or the flow "
        "aborts with no partial case created (create_case and classify_and_route both "
        "raise on invalid input/state, per business_process). A failure in sync-crm "
        "after canonical success is handled per that step's on_failure — canonical "
        "state is the source of truth and is never reverted to match a failed CRM write."
    ),
    audit_events=("case_created", "case_routed", "crm_synced", "acknowledgement_sent"),
)

SLA_MONITORING_FLOW = WorkflowSpecification(
    flow_id="power-automate-sla-monitoring-v1",
    name="SLA Monitoring and Escalation",
    description=(
        "Periodically re-evaluates each open case's SLA status using "
        "business_process, escalates where the canonical rules say to, and "
        "keeps the Dynamics representation in sync."
    ),
    trigger_type=TriggerType.SCHEDULE,
    trigger_detail=(
        "Recurring schedule (e.g. every 15 minutes), plus an event-driven re-check on case update"
    ),
    inputs=("case_id",),
    outputs=("sla_status", "escalation_reason", "dynamics_sync_status"),
    steps=(
        WorkflowStep(
            step_id="get-case",
            name="Get current case state",
            kind=StepKind.CONNECTOR_CALL,
            operation="get_case",
            description="Retrieve current canonical case state via the connector boundary.",
        ),
        WorkflowStep(
            step_id="get-sla-target",
            name="Get SLA target",
            kind=StepKind.CANONICAL_OPERATION,
            operation="get_sla_target",
            description="Look up the case's response/resolution targets by category and priority.",
        ),
        WorkflowStep(
            step_id="evaluate-sla",
            name="Evaluate SLA status",
            kind=StepKind.CANONICAL_OPERATION,
            operation="evaluate_sla",
            description=(
                "Evaluate breach state against the target. This flow does not "
                "compute breach thresholds itself."
            ),
        ),
        WorkflowStep(
            step_id="evaluate-escalation",
            name="Evaluate escalation eligibility",
            kind=StepKind.CANONICAL_OPERATION,
            operation="determine_escalation_reason",
            description=(
                "Determine whether the case qualifies for escalation, and why, "
                "from its priority, stage, and SLA status."
            ),
        ),
        WorkflowStep(
            step_id="condition-escalate",
            name="Branch on escalation reason",
            kind=StepKind.CONDITION,
            description=(
                "Proceed to escalate only if a reason was returned; otherwise "
                "the run ends here for this case."
            ),
            condition="escalation reason is not None",
        ),
        WorkflowStep(
            step_id="escalate-case",
            name="Escalate case",
            kind=StepKind.CANONICAL_OPERATION,
            operation="escalate_case",
            description=(
                "Move the case to ESCALATED, recording the reason business_process returned. "
                "Only reached when condition-escalate is true."
            ),
        ),
        WorkflowStep(
            step_id="map-to-dynamics",
            name="Map to Dynamics representation",
            kind=StepKind.ADAPTER_OPERATION,
            operation="to_dynamics_incident",
            description=(
                "Translate the escalated case, including current SLA fields, "
                "into a reference DynamicsIncident."
            ),
        ),
        WorkflowStep(
            step_id="sync-crm",
            name="Persist CRM representation",
            kind=StepKind.CONNECTOR_CALL,
            operation="sync_dynamics_representation",
            description="Push the updated representation to the CRM boundary.",
        ),
        WorkflowStep(
            step_id="notify-escalation",
            name="Notify queue owner of escalation",
            kind=StepKind.NOTIFICATION,
            description="Notify the case's owning team that it has escalated.",
        ),
        WorkflowStep(
            step_id="audit-escalation",
            name="Record escalation audit evidence",
            kind=StepKind.AUDIT_EVENT,
            description="Record the escalation with its reason, case_id, and correlation_id.",
        ),
    ),
    idempotency_strategy=(
        "Re-running this flow for the same case_id before its stage changes must not "
        "create a duplicate escalation. business_process.lifecycle provides a canonical "
        "backstop: ESCALATED -> ESCALATED is not in ALLOWED_TRANSITIONS, so a repeat "
        "escalate_case call on an already-escalated case raises "
        "InvalidLifecycleTransitionError rather than escalating twice."
    ),
    correlation_strategy=(
        "correlation_id = integrations.envelope.new_correlation_id("
        "f'sla-monitor:{case_id}:{run_timestamp}'), unique per scheduled run so each "
        "escalation attempt is independently traceable."
    ),
    failure_handling=(
        "If evaluate_sla or escalate_case raise for one case, that case's processing "
        "aborts, is recorded via an audit event with status=failed, and the scheduled "
        "run continues to the next case (partial failure isolation) rather than "
        "failing the entire batch."
    ),
    audit_events=("sla_evaluated", "escalation_raised", "escalation_notification_sent"),
)

APPROVAL_FLOW = WorkflowSpecification(
    flow_id="power-automate-approval-v1",
    name="Human Approval for a Consequential Action",
    description=(
        "Routes a consequential, non-clinical action (e.g. an elevated Dataverse "
        "security role grant) related to an existing case to a human approver, "
        "and records the outcome as immutable audit evidence regardless of decision."
    ),
    trigger_type=TriggerType.EVENT,
    trigger_detail=(
        "A Power Apps action or connector call requesting a consequential action "
        "against an existing canonical case"
    ),
    inputs=("case_id", "requested_action", "requester", "approver_role"),
    outputs=("approval_id", "decision", "decided_by", "decided_at"),
    steps=(
        WorkflowStep(
            step_id="get-case",
            name="Get related case",
            kind=StepKind.CONNECTOR_CALL,
            operation="get_case",
            description="Retrieve the canonical case this approval relates to.",
        ),
        WorkflowStep(
            step_id="create-approval-request",
            name="Create approval request",
            kind=StepKind.APPROVAL,
            description=(
                "System creates an ApprovalRequest (requester, approver_role, "
                "correlation_id, timeout_at) and routes it to the approver role's queue."
            ),
            requires_human=False,
        ),
        WorkflowStep(
            step_id="await-approval-decision",
            name="Await human decision",
            kind=StepKind.APPROVAL,
            description=(
                "A person holding approver_role reviews the request and records a "
                "decision (Approved/Rejected) with a reason, or the request times "
                "out per timeout_at."
            ),
            requires_human=True,
            on_failure=(
                "No decision by timeout_at is recorded as an explicit Timed Out "
                "decision, not a silent failure."
            ),
        ),
        WorkflowStep(
            step_id="record-approval-audit",
            name="Record approval audit evidence",
            kind=StepKind.AUDIT_EVENT,
            description=(
                "Persist the full ApprovalRecord — requester, approver role, decision, "
                "reason, timestamp, correlation id — regardless of outcome."
            ),
        ),
        WorkflowStep(
            step_id="notify-outcome",
            name="Notify requester and approver of outcome",
            kind=StepKind.NOTIFICATION,
            description="Notify both parties of the final decision and its reason.",
        ),
        WorkflowStep(
            step_id="condition-approved",
            name="Branch on decision",
            kind=StepKind.CONDITION,
            description=(
                "Only an Approved decision proceeds to apply the requested action; "
                "Rejected/Timed Out stop here — audit and notification are already "
                "recorded either way."
            ),
            condition="decision == Approved",
        ),
        WorkflowStep(
            step_id="apply-approved-action",
            name="Apply approved action",
            kind=StepKind.CONNECTOR_CALL,
            operation="transition_case",
            description=(
                "Only reached when Approved: move the related case forward via the "
                "connector boundary, so canonical lifecycle rules still govern "
                "whether that move is valid."
            ),
        ),
    ),
    idempotency_strategy=(
        "approval_id is generated once at request creation and is the idempotency key — "
        "a duplicate trigger (e.g. a retried Power Apps submission) must look up an "
        "existing ApprovalRequest by its natural key (case_id + requested_action + "
        "requester) before creating a new one."
    ),
    correlation_strategy=(
        "correlation_id ties the approval request to both case_id and any downstream "
        "notification/audit events: integrations.envelope.new_correlation_id("
        "f'approval:{case_id}:{requested_action}')."
    ),
    failure_handling=(
        "Approval timeout is treated as an explicit ApprovalDecision.TIMED_OUT outcome, "
        "audited and notified identically to a Rejected decision — a case is never left "
        "in an ungoverned, undecided state."
    ),
    audit_events=("approval_requested", "approval_decided", "approval_notification_sent"),
)

RESOLUTION_NOTIFICATION_FLOW = WorkflowSpecification(
    flow_id="power-automate-resolution-notification-v1",
    name="Resolution and Closure Notification",
    description=(
        "Once a case reaches RESOLVED, synchronizes its Dynamics representation, "
        "notifies the requestor, optionally invites feedback, and closes the case."
    ),
    trigger_type=TriggerType.EVENT,
    trigger_detail=(
        "Triggered once resolve_case has moved a case to RESOLVED (e.g. by a queue "
        "worker's Power Apps action)"
    ),
    inputs=("case_id", "resolution_outcome", "resolution_notes"),
    outputs=("dynamics_sync_status", "notification_status", "feedback_requested"),
    steps=(
        WorkflowStep(
            step_id="get-case",
            name="Get resolved case",
            kind=StepKind.CONNECTOR_CALL,
            operation="get_case",
            description="Retrieve current canonical case state.",
        ),
        WorkflowStep(
            step_id="confirm-resolved",
            name="Confirm case is still RESOLVED",
            kind=StepKind.CONDITION,
            description=(
                "Guard against a duplicate or late-delivered trigger re-processing "
                "an already-closed case."
            ),
            condition="case.stage == RESOLVED",
            on_failure=(
                "If the case is not in RESOLVED stage (e.g. duplicate/late trigger, "
                "or already CLOSED), abort without notifying again."
            ),
        ),
        WorkflowStep(
            step_id="map-to-dynamics",
            name="Map to Dynamics representation",
            kind=StepKind.ADAPTER_OPERATION,
            operation="to_dynamics_incident",
            description=(
                "Translate the resolved case, including its resolution, into a "
                "reference DynamicsIncident."
            ),
        ),
        WorkflowStep(
            step_id="map-timeline",
            name="Map audit timeline",
            kind=StepKind.ADAPTER_OPERATION,
            operation="to_dynamics_timeline",
            description=(
                "Translate the case's full audit history into reference Dynamics timeline entries."
            ),
        ),
        WorkflowStep(
            step_id="sync-crm",
            name="Persist CRM representation",
            kind=StepKind.CONNECTOR_CALL,
            operation="sync_dynamics_representation",
            description="Push the resolved representation to the CRM boundary.",
        ),
        WorkflowStep(
            step_id="notify-requestor",
            name="Notify requestor of resolution",
            kind=StepKind.NOTIFICATION,
            description=(
                "Notify the requestor that their case was resolved, including outcome and notes."
            ),
        ),
        WorkflowStep(
            step_id="request-feedback",
            name="Invite feedback",
            kind=StepKind.NOTIFICATION,
            description=(
                "Optionally invite the requestor to confirm the fix or provide feedback. "
                "Feedback is informational only — it does not itself change canonical "
                "state (see docs/architecture.md human-in-the-loop principle)."
            ),
        ),
        WorkflowStep(
            step_id="audit-resolution-notification",
            name="Record resolution-notification audit evidence",
            kind=StepKind.AUDIT_EVENT,
            description=(
                "Record requestor notified, feedback requested, timestamps, and correlation id."
            ),
        ),
        WorkflowStep(
            step_id="close-case",
            name="Close case",
            kind=StepKind.CANONICAL_OPERATION,
            operation="close_case",
            description=(
                "Move the case to CLOSED. Modelled here as the flow's final step to show the "
                "full Resolved -> Closed path; a real deployment might defer this to a later, "
                "scheduled follow-up flow to allow a feedback window first."
            ),
        ),
    ),
    idempotency_strategy=(
        "case_id + 'resolution-notification' is the natural idempotency key. The "
        "confirm-resolved condition step ensures a redelivered or duplicate trigger "
        "cannot send a second notification once close_case has already run, since a "
        "closed case's stage is no longer RESOLVED — the canonical lifecycle rules "
        "provide the backstop."
    ),
    correlation_strategy=(
        "correlation_id = integrations.envelope.new_correlation_id(f'resolution-notify:{case_id}')"
    ),
    failure_handling=(
        "If CRM sync fails after canonical resolution has already succeeded, the flow "
        "does not roll back canonical state — it raises a crm_sync_failed audit event "
        "and queues manual reconciliation, since canonical business state is the "
        "source of truth and must never be reverted to match a failed CRM write."
    ),
    audit_events=("case_resolved_notification_sent", "feedback_requested", "case_closed"),
)

ALL_FLOWS: tuple[WorkflowSpecification, ...] = (
    INTAKE_FLOW,
    SLA_MONITORING_FLOW,
    APPROVAL_FLOW,
    RESOLUTION_NOTIFICATION_FLOW,
)

__all__ = [
    "ALL_FLOWS",
    "APPROVAL_FLOW",
    "INTAKE_FLOW",
    "RESOLUTION_NOTIFICATION_FLOW",
    "SLA_MONITORING_FLOW",
]
