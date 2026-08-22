# power_platform/power_apps/

Reference architecture for a Power Apps application over the canonical
service operations model. **No `.msapp` file, canvas app, or model-driven
app is built** — this is a documented architecture only, deliberately
covering both canvas and model-driven patterns since the choice is a real
deployment decision, not an architectural one.

## Where Dataverse/Dynamics participates

A real deployment would have Dataverse hold the `incident` table (the
[`dynamics365`](../../dynamics365/) reference representation), kept current
by the intake/SLA-monitoring/resolution flows' `sync_dynamics_representation`
connector calls (see [`power_automate/README.md`](../power_automate/README.md)).

- **Model-driven forms/views** would bind directly to that Dataverse
  `incident` table — the natural fit for read-heavy, CRM-shaped screens
  (Service Operations Queue, Case Detail, SLA Status).
- **All write actions** (submit a request, start work, resolve, approve) go
  through the [connector boundary](../connectors/README.md) — never a
  direct Dataverse write — so `business_process` remains the sole decision
  authority regardless of which UI pattern a screen uses. Dataverse is the
  **read/display data plane**; `business_process` is the **write/decision
  plane**, reconciled by the sync step.

## User roles

| Role | Who | Scope |
|------|-----|-------|
| Requestor | Any staff member raising a request | Their own submitted requests only |
| Service Agent | Member of a queue's owning team (e.g. `digital-support-team`) | Cases in their queue(s) only |
| Approver | Holds an `approver_role` (e.g. `identity-access-team-lead`) | Approval requests addressed to their role, plus escalated cases in their queue for visibility |

No role in this reference architecture is a named individual —
consistent with `business_process`'s team/role-based ownership model (see
[`docs/business_process.md`](../../docs/business_process.md) §6). A
governance/audit-reviewer role is documented in
[`governance/README.md`](../../governance/README.md).

## Screens

| Screen | Role(s) | Purpose | Data boundary |
|--------|---------|---------|----------------|
| Service Request Submission | Requestor | Submit a new request (title, description, category, priority) | Write-only; no visibility into other requests |
| My Requests | Requestor | Track their own requests' status and history | Own requests only |
| Service Operations Queue | Service Agent | Work the queue: see cases routed to their team, by stage/priority | Own queue(s) only |
| Case Detail | Requestor (their case), Service Agent (their queue), Approver (escalated/related) | Full case view: fields, resolution, audit timeline | Role-scoped, per row above |
| SLA Status | Service Agent, Approver | Aggregate breach/at-risk view across a queue | Own queue(s) only |
| Escalation / Approval View | Approver | Escalated cases and pending `ApprovalRequest`s for their `approver_role` | Own `approver_role` only |

## Actions per screen, and what they call

| Screen | Action | Calls | Kind |
|--------|--------|-------|------|
| Service Request Submission | Submit | `create_case` connector operation | Canonical (decision: none beyond field presence — validation happens in the intake flow) |
| Service Request Submission | Populate category/priority pickers | `list_service_categories` connector operation + the static `Priority` enum | Read-only, no decision |
| My Requests | View status | `get_case` connector operation | Read-only *(no persistence layer yet — see `connectors/README.md` `get_case` caveat)* |
| My Requests | Provide feedback (post-resolution) | Notification-flow trigger only (see `resolution-notification` flow's `request-feedback` step) | Informational — never itself a canonical state change |
| Service Operations Queue | Start work / Mark pending / Resolve | `transition_case` / `resolve_case` connector operations | Canonical — the app never decides whether a move is legal; `business_process` does |
| Service Operations Queue | (Optional) Manually escalate | `transition_case` connector operation (`to_stage=Escalated`) | Canonical — even a manual escalation from the UI goes through the same `escalate_case`/`transition_case` path the scheduled SLA-monitoring flow uses, never a UI-side shortcut |
| Case Detail | View SLA status | `evaluate_sla` connector operation | Canonical decision, read-only from the app's perspective |
| Case Detail | View audit timeline | Rendered from `CaseEvent` history (via `get_case`) | Read-only |
| SLA Status | Aggregate view | `evaluate_sla` per case in scope | Canonical decision per case; the app performs no aggregation logic beyond display grouping |
| Escalation / Approval View | Approve / Reject | Records an `ApprovalRecord` (see [`approvals.py`](../approvals.py)); on Approved, `transition_case` connector operation | The decision (Approved/Rejected) is the **human's**, not the app's or `business_process`'s — see the approval flow's human-in-the-loop step |

No screen or action in this architecture computes a lifecycle transition's
validity, an SLA breach, an escalation reason, or a routing decision itself
— every one of those goes through the connector boundary to
`business_process` (or `dynamics365` for representation only). See
[`power_platform/README.md`](../README.md) "Architecture rule this package
follows".
