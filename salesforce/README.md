# salesforce/

Reference adapter for **Salesforce Service Cloud**.

**Status: implemented (Milestone 3) — pure, deterministic reference
mappings only.** No Salesforce SDK/API client, no live org, no credentials,
no connected app. Every id in this package is a deterministic synthetic
value (`sha256`-derived, Salesforce-key-prefix-shaped) — see
[`docs/crm_schema_mapping.md`](../docs/crm_schema_mapping.md).

## Module map

| Module | Purpose |
|--------|---------|
| `models.py` | Typed reference shapes: `SalesforceCase`, `SalesforceCaseMilestone`, `SalesforceFeedItem`, and the `SalesforcePriority` / `SalesforceStatus` enums. |
| `mapping.py` | Explicit mapping tables (`PRIORITY_TO_SALESFORCE`, `STAGE_TO_SALESFORCE_STATUS`, `QUEUE_TO_SALESFORCE_NAME`, and their reverses) plus the pure translation functions `to_salesforce_case()` / `to_salesforce_feed()`, and `UnsupportedSalesforceValueError` for unmapped values. |
| `serialization.py` | JSON-safe dict conversion for the models above. |

## Architecture rule this package follows

This adapter **translates already-decided canonical state — it never
decides anything itself.** It does not import `business_process.lifecycle`,
`business_process.sla`, `business_process.service`, or
`business_process.queues.route_category`/`assign_owner`. Case status,
priority, queue, and SLA milestone dates/breach flags must already have been
produced by `business_process` and are passed into `to_salesforce_case()`
as plain values. `tests/test_adapter_boundary.py` enforces this at the
source-code level (not just by convention).

## What is and isn't mapped 1:1

See [`docs/crm_schema_mapping.md`](../docs/crm_schema_mapping.md) for the
full field-by-field table. Two points worth noting:

- Salesforce's single flat `Status` picklist maps all 8 canonical stages to
  8 distinct values with **no lossy collapsing** — a genuinely cleaner fit
  than Dynamics' two-tier state/status model for this particular concept.
- Out-of-the-box Salesforce ships only 3 `Priority` values — this reference
  adapter assumes a customized 4-value picklist to avoid collapsing
  canonical priorities.
- SLA is modelled as `CaseMilestone`-style records (mirroring Salesforce's
  real Entitlement Management pattern), not flat due-date fields.

## Not implemented

Live Salesforce connectivity, authentication (OAuth/Connected App), Apex,
platform events/webhooks, or any write-back to a real org. See
[`docs/roadmap.md`](../docs/roadmap.md) and the root
[README's current implementation status](../README.md#9-current-implementation-status).
