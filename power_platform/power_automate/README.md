# power_platform/power_automate/

Version-controlled Power Automate flow **specifications** — not exported
`.zip` solutions, not live flows. Each `*.flow.json` file in this directory
is generated (deterministically, from `power_platform/flows.py`) by running:

```
python -m power_platform.evidence
```

## Format

Each file is the JSON form of a `power_platform.workflow_spec.WorkflowSpecification`:

| Field | Meaning |
|-------|---------|
| `flow_id`, `name`, `description`, `version` | Identity and intent. |
| `trigger_type` | `event`, `schedule`, or `manual`. |
| `trigger_detail` | What actually starts the flow. |
| `inputs` / `outputs` | The flow's conceptual parameters and results. |
| `steps` | Ordered list of `WorkflowStep` — see below. |
| `idempotency_strategy` | How a duplicate/retried trigger is handled without duplicating effects. |
| `correlation_strategy` | How a `correlation_id` is derived and threaded through the flow. |
| `failure_handling` | What happens when a step fails, including after a canonical success. |
| `audit_events` | The named audit evidence this flow is expected to produce. |

Each step (`WorkflowStep`) has a `kind`:

| `kind` | Meaning |
|--------|---------|
| `canonical_operation` | Invokes a named `business_process` function (from the closed `CanonicalOperation` vocabulary). Decides nothing itself. |
| `adapter_operation` | Invokes a named `dynamics365` translation function (from `AdapterOperation`). |
| `connector_call` | Invokes a named operation from the connector contract — see [`../connectors/README.md`](../connectors/README.md). |
| `condition` | A pure branch on state a prior step already produced. Never carries an `operation`. |
| `approval` | A human-approval step; `requires_human` distinguishes system-side request creation from the actual human decision wait. |
| `notification` | An outbound notification (email/Teams/etc.). |
| `audit_event` | Records audit evidence. |

`power_platform/flow_validation.py`'s `validate_workflow_spec()` enforces
that every `canonical_operation`/`adapter_operation`/`connector_call` step
references something real (see `power_platform/README.md` "Architecture
rule this package follows").

## The four flows

### 1. New Service Request Intake (`power-automate-intake-v1`)

Power Apps/Power Pages/integration event → validate → `create_case` →
`classify_and_route` → map to a Dynamics reference representation →
persist via the connector boundary → acknowledge the requestor. Routing and
classification are always canonical operations, never a condition step
guessing the queue.

### 2. SLA Monitoring and Escalation (`power-automate-sla-monitoring-v1`)

Scheduled (e.g. every 15 minutes) → get case → `get_sla_target` +
`evaluate_sla` → `determine_escalation_reason` → branch → `escalate_case`
(only if a reason was returned) → sync CRM → notify → audit. SLA breach and
escalation eligibility are always canonical operations, never computed in a
condition's free text.

### 3. Human Approval for a Consequential Action (`power-automate-approval-v1`)

An elevated Dataverse security-role request (never a clinical treatment
decision) → create `ApprovalRequest` → **await a human decision**
(`requires_human=True`) → record the full `ApprovalRecord` as audit evidence
regardless of outcome → notify both parties → only an Approved decision
proceeds to apply the action, via the connector boundary so canonical
lifecycle rules still govern it.

### 4. Resolution and Closure Notification (`power-automate-resolution-notification-v1`)

Case reaches RESOLVED → confirm it's still RESOLVED (duplicate-trigger
guard) → map to Dynamics → sync CRM → notify requestor → optionally invite
feedback (informational only, never itself a canonical state change) →
audit → `close_case`.

See [`power_platform/README.md`](../README.md) "Failure and retry
architecture" for the shared failure-handling pattern across all four.
