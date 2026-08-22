# power_platform/power_pages/

Reference architecture for a lightweight Power Pages self-service portal
over the canonical service operations model. **No site, page, or web role
configuration is built** — this is a documented architecture only.

## Capabilities

| Capability | Description |
|------------|--------------|
| Submit a service request | Authenticated portal user submits title/description/category/priority — same `create_case` connector call as the Power Apps submission screen, so canonical validation and classification behave identically regardless of which front end was used. |
| Track own request | View the status (canonical `CaseStage`) of requests the authenticated user submitted. |
| View permitted status information | A **deliberately reduced** view of case state — see "What the portal shows" below. |
| Provide resolution feedback | Once a case is `Resolved`, the portal offers a feedback prompt — mirrors the `request-feedback` step in the [resolution-notification flow](../power_automate/README.md); informational only. |
| Knowledge / self-service entry point | A static or lightly-templated knowledge area (FAQs, how-to-request guidance) — no dynamic case data, no canonical operation calls. |

## Privacy and authorization

- **Authentication is required** for every capability except the knowledge
  entry point. This portal is explicitly **not** an anonymous/public
  surface — no case, however trivial, is exposed without a logged-in
  session identifying the requestor.
- **Row-level scoping**: a portal user may only ever see cases where they
  are the requestor. This mirrors the "My Requests" data boundary in
  [`power_apps/README.md`](../power_apps/README.md) and is enforced the same
  way: `get_case`/tracking calls are always scoped to the authenticated
  user's own submissions, never a general case search.
- **No cross-case or cross-queue visibility.** A portal user never sees
  another requestor's case, a queue's full backlog, SLA internals, owner
  team identity beyond a generic "Digital Support" style label, or audit
  actor names beyond what's needed to show status changes (e.g. "Status
  changed to In Progress" — no internal team roster or individual names
  are surfaced).
- **What the portal shows** for a tracked case: title, category, priority,
  current stage (in plain language, e.g. "In Progress" rather than internal
  step names), and resolution outcome/notes once resolved. It does **not**
  show: the full internal audit/timeline detail, SLA due-date internals,
  escalation reasons, or any Dynamics-representation-specific fields (those
  are internal, operational detail — see
  [`docs/crm_schema_mapping.md`](../../docs/crm_schema_mapping.md)).
- **No unrestricted case data is ever publicly exposed** — this is an
  explicit non-goal of this architecture, consistent with the
  [portfolio scope statement](../../README.md#portfolio-scope)
  and the synthetic-data-only principle in
  [`docs/governance.md`](../../docs/governance.md).

## What calls what

Every write action (submit, feedback) and every read (track status) goes
through the same [connector boundary](../connectors/README.md) as Power
Apps — `create_case` and `get_case` respectively — so the portal makes no
independent decision about classification, routing, SLA, or escalation. The
knowledge/self-service entry point makes no canonical or connector calls at
all; it is static content.
