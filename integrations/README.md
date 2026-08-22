# integrations/

Bounded context for the **API-first integration layer** connecting
case-management platforms, automation, agentic AI, and analytics.

**Status: partially implemented (Milestone 3).** This directory now holds a
lightweight data contract and a deterministic example generator — it is
**not** a message broker, event platform, or live connector.

## What's implemented

| Module | Purpose |
|--------|---------|
| `envelope.py` | `IntegrationEnvelope` — a small, platform-neutral metadata wrapper (source system, source record id, canonical case id, correlation id, schema version, timestamp, operation) for a translated payload. Data shape only; no transport. |
| `examples.py` | Deterministic example generator: reads canonical fixture cases and their current SLA status from `business_process`, calls the `dynamics365`/`salesforce` adapters' translation functions, and writes the wrapped results to `data/synthetic/{dynamics365,salesforce}_examples.json`. This is the one place in the repository that plays the role of a *future API connector* — see [`docs/crm_schema_mapping.md`](../docs/crm_schema_mapping.md) "How a future API connector would sit around these adapters". |

## What's still a placeholder

No transport (HTTP client, message queue, event bus), no retries or
delivery guarantees, no authentication, no webhook ingestion, and no
connection to a live Dynamics 365 or Salesforce environment. See
[`docs/roadmap.md`](../docs/roadmap.md) and the root
[README's current implementation status](../README.md#9-current-implementation-status).

## How idempotency and external IDs fit in

`IntegrationEnvelope.canonical_case_id` is always
`business_process.models.Case.case_id` — the one identity a future connector
would use to resolve "which canonical case is this?" regardless of which
CRM's record id (`source_record_id`) also appears. See "Idempotency and
external IDs" in [`docs/crm_schema_mapping.md`](../docs/crm_schema_mapping.md)
for the full pattern.
