# power_platform/

Power Platform automation architecture for the canonical service operations
model.

**Status: implemented (Milestone 4) — version-controlled, deterministic
reference specifications only.** No live Power Platform environment,
deployed flow, Dataverse connection, or credential. See
[`docs/architecture.md`](../docs/architecture.md) for the end-to-end diagram
and the [root README](../README.md) for what
is/isn't implemented.

## Module map

| Module | Purpose |
|--------|---------|
| `workflow_spec.py` | Typed models: `WorkflowStep`, `WorkflowSpecification`, `TriggerType`, `StepKind`, and the closed `CanonicalOperation`/`AdapterOperation` vocabularies a step may reference. |
| `flows.py` | The four concrete reference flows: `INTAKE_FLOW`, `SLA_MONITORING_FLOW`, `APPROVAL_FLOW`, `RESOLUTION_NOTIFICATION_FLOW`. |
| `flow_validation.py` | `validate_workflow_spec()` — structural completeness plus the canonical-domain boundary rule (see below). |
| `connector_spec.py` | Typed `ConnectorOperation` model + `validate_connector_operation()`. |
| `connectors.py` | The nine representative connector operations, with example payloads built from real synthetic fixtures. |
| `approvals.py` | The human-approval pattern: `ApprovalRequest`/`ApprovalRecord`/`ApprovalDecision`, `validate_approval_record()`, and two deterministic examples. |
| `evidence.py` | Generates all Milestone 4 evidence — flow spec JSON, the connector contract, approval examples, a simulated execution trace, and `reports/automation_summary.json`. Run via `python -m power_platform.evidence`. |

Subdirectories: [`power_automate/`](power_automate/) (flow spec JSON +
README), [`power_apps/`](power_apps/) (reference app architecture doc),
[`power_pages/`](power_pages/) (reference portal architecture doc),
[`connectors/`](connectors/) (connector contract JSON + README).

## Architecture rule this package follows

```
Power Platform interaction/workflow → canonical service operations → CRM adapter
```

`business_process` remains the sole source of truth for lifecycle validity,
priority, routing, SLA evaluation, and escalation decisions.
[`dynamics365`](../dynamics365/) remains responsible only for translation.
Power Platform artefacts **orchestrate** these — they never redefine them:

- Every `CANONICAL_OPERATION`/`ADAPTER_OPERATION` workflow step names a real
  `business_process`/`dynamics365` callable from a **closed enum**
  (`CanonicalOperation`/`AdapterOperation`), checked by introspection
  (`getattr`, never called) in `flow_validation.py`. A flow spec cannot
  invent a decision that doesn't exist in the canonical layer, and cannot
  silently drift from it either — see `tests/test_power_platform_flows.py`'s
  drift guards.
- A `CONDITION`-kind step (a pure branch) may never carry an `operation` —
  enforced structurally by `validate_workflow_spec()`. A condition can only
  branch on state a prior canonical/adapter/connector step already produced.
- SLA due dates and breach flags are never computed inside `power_platform`
  — they are supplied as plain values by whatever calls the connector
  operations (in the Milestone 4 reference examples,
  [`integrations/examples.py`](../integrations/examples.py)-style
  orchestration inside `power_platform/connectors.py`'s own example builders,
  which call `business_process.sla` only to build **documentation examples**,
  never to make a workflow-time decision).
- `tests/test_power_platform_boundary.py` and
  `tests/test_power_platform_flows.py` enforce all of the above
  automatically, not just by convention. Note this package's boundary rule
  differs from `dynamics365`/`salesforce`'s (see `tests/test_adapter_boundary.py`):
  those adapters must never import `business_process` decision modules at
  all, because they only ever translate already-decided values. This
  package's job is partly to *validate that flows reference real decisions*,
  so it legitimately imports `business_process`/`dynamics365` for
  introspection and example-building — what it must never do is *call* a
  decision function to decide something on a flow's behalf.

## Human-in-the-loop

Exactly one step across all four flows sets `requires_human=True`: the
approval flow's `await-approval-decision` step. See "Human approval" in
[`docs/architecture.md`](../docs/architecture.md) and
[`docs/governance.md`](../docs/governance.md).

## Failure and retry architecture

See each flow's `idempotency_strategy`, `correlation_strategy`, and
`failure_handling` fields (in `power_platform/flows.py` and the generated
`power_platform/power_automate/*.flow.json`) for the concrete, per-flow
answers to: idempotency, duplicate triggers, correlation ids, partial
failure, CRM-update-failure-after-canonical-success, notification failure,
and approval timeout. The general pattern used throughout: canonical
business state (in `business_process`) is always the source of truth and is
**never rolled back** to match a failed downstream write (CRM sync,
notification); failures downstream of a canonical success are surfaced as
audit events and queued for manual reconciliation instead.

## Not implemented

Live Power Platform environment, deployed flows, live Dataverse connection,
Copilot Studio, LLM triage, autonomous agents, or production deployment. See
[`docs/roadmap.md`](../docs/roadmap.md).
