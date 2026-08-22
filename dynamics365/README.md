# dynamics365/

Reference adapter for **Dynamics 365 Customer Service / Dataverse**.

**Status: implemented (Milestone 3) — pure, deterministic reference
mappings only.** No Dynamics SDK, no live tenant, no credentials, no
connected app. Every id in this package is a deterministic synthetic value
(`uuid5`-derived) — see [`docs/crm_schema_mapping.md`](../docs/crm_schema_mapping.md).

## Module map

| Module | Purpose |
|--------|---------|
| `models.py` | Typed reference shapes: `DynamicsIncident`, `DynamicsIncidentResolution`, `DynamicsTimelineEntry`, and the `DynamicsPriorityCode` / `DynamicsStateCode` / `DynamicsStatusReason` enums. |
| `mapping.py` | Explicit mapping tables (`PRIORITY_TO_DYNAMICS`, `STAGE_TO_DYNAMICS_STATUS`, `QUEUE_TO_DYNAMICS_NAME`, and their reverses) plus the pure translation functions `to_dynamics_incident()` / `to_dynamics_timeline()`, and `UnsupportedDynamicsValueError` for unmapped values. |
| `serialization.py` | JSON-safe dict conversion for the models above. |

## Architecture rule this package follows

This adapter **translates already-decided canonical state — it never
decides anything itself.** It does not import `business_process.lifecycle`,
`business_process.sla`, `business_process.service`, or
`business_process.queues.route_category`/`assign_owner`. Case stage,
priority, queue, and SLA due dates/breach flags must already have been
produced by `business_process` and are passed into `to_dynamics_incident()`
as plain values. `tests/test_adapter_boundary.py` enforces this at the
source-code level (not just by convention).

## What is and isn't mapped 1:1

See [`docs/crm_schema_mapping.md`](../docs/crm_schema_mapping.md) for the
full field-by-field table. The two most important non-1:1 points:

- Dataverse's native `statecode`/`statuscode` model has **no distinction
  between "resolved" and "closed"** — both canonical stages collapse onto
  the same Dynamics state, and the reverse mapping is a documented,
  deliberate, lossy choice.
- Out-of-the-box Dataverse ships only 3 `prioritycode` values — this
  reference adapter assumes a customized 4-value option set to avoid
  collapsing canonical priorities.

## Not implemented

Live Dataverse/Dynamics 365 connectivity, authentication, webhooks, Power
Automate, or any write-back to a real environment. See
[`docs/roadmap.md`](../docs/roadmap.md) and the root
[README's current implementation status](../README.md#9-current-implementation-status).
