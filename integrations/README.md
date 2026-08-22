# integrations/

Bounded context for the **API-first integration layer** connecting
case-management platforms, automation, agentic AI, and analytics.

**Status: implemented as a local/reference transport architecture through
Milestone 7.** This directory holds a lightweight data contract,
deterministic example generation, and a provider-neutral webhook/delivery
simulation. It is **not** a public API, message broker, event platform, or
live connector. Milestone 4's intended
Power Platform API/custom-connector boundary lives under
[`power_platform/connectors/`](../power_platform/connectors/).

## What's implemented

| Module | Purpose |
|--------|---------|
| `envelope.py` | `IntegrationEnvelope` — a small, platform-neutral metadata wrapper (source system, source record id, canonical case id, correlation id, schema version, timestamp, operation, optional envelope/idempotency/trace metadata) for a translated payload. |
| `examples.py` | Deterministic example generator: reads canonical fixture cases and their current SLA status from `business_process`, calls the `dynamics365`/`salesforce` adapters' translation functions, and writes the wrapped results to `data/synthetic/{dynamics365,salesforce}_examples.json`. This is the one place in the repository that plays the role of a *future API connector* — see [`docs/crm_schema_mapping.md`](../docs/crm_schema_mapping.md) "How a future API connector would sit around these adapters". |
| `webhooks.py` | Local/reference webhook processor: validates envelope schema, applies conceptual auth, checks idempotency, dispatches to an allow-listed operation, retries through the outbound transport abstraction, and returns delivery state. |
| `delivery.py` | Integration delivery-state model (`received`, `validated`, `processing`, `delivered`, `retry_pending`, `failed`, `dead_lettered`, `duplicate`). This state machine is separate from canonical case lifecycle. |
| `idempotency.py` | In-memory deterministic idempotency store used by tests and synthetic evidence; delivered duplicates are suppressed while failed deliveries can be retried safely. |
| `retry.py` | Retryable/non-retryable error types and bounded exponential backoff metadata; tests never sleep. |
| `transport.py` | Provider-neutral outbound transport protocol plus deterministic stub. No HTTP calls or SDK credentials. |
| `security.py` | Conceptual service-to-service principal checks for source binding, audience, environment, and scope. No token issuance or secrets. |
| `reconciliation.py` | Deterministic reconciliation checks for failed/stuck deliveries, missing CRM representation, duplicate external mapping, and correlation mismatch. |
| `observability.py` | Aggregates synthetic delivery metrics for reports and analytics. |
| `evidence.py` | Generates deterministic Milestone 7 envelopes, delivery traces, reconciliation findings, and tracked reports. |

## Transport architecture

```text
External / SaaS System
        ↓
Webhook / API Boundary
        ↓
IntegrationEnvelope
        ↓
Canonical Service Operations
        ↓
CRM / Power Platform Adapters
```

Transport is responsible for moving, validating, correlating, retrying, and
observing messages. It does not own lifecycle rules, SLA calculations,
routing rules, escalation decisions, AI/tool permissions, or CRM-specific
business semantics.

As of Milestone 8, [`governance/policies.py`](../governance/policies.py)
checks the reference integration schema version, expected audience, and
`integration:deliver` scope. [`governance/attestations.py`](../governance/attestations.py)
adds a synthetic access attestation for integration service identities.

## What's still not implemented

No public production API, live webhook endpoint, HTTP client, message queue,
event bus, production OAuth/token exchange, Azure Service Bus/Event Grid,
live monitoring backend, production custom connector implementation, or
connection to a live Dynamics 365, Salesforce, Power Platform, or Dataverse
environment. See
[`docs/roadmap.md`](../docs/roadmap.md) and the root
[README's current implementation status](../README.md#9-current-implementation-status).

## How idempotency and external IDs fit in

`IntegrationEnvelope.canonical_case_id` is always
`business_process.models.Case.case_id` — the one identity a future connector
would use to resolve "which canonical case is this?" regardless of which
CRM's record id (`source_record_id`) also appears. See "Idempotency and
external IDs" in [`docs/crm_schema_mapping.md`](../docs/crm_schema_mapping.md)
for the full pattern.

## Evidence

Run:

```text
python -m integrations.evidence
```

This regenerates tracked synthetic/reference evidence:

- `data/synthetic/integration_envelopes.json`
- `data/synthetic/integration_delivery_traces.json`
- `data/synthetic/reconciliation_cases.json`
- `reports/integration_operations_summary.json`
- `reports/reconciliation_report.md`

The scenarios cover successful delivery, duplicate webhook suppression,
transient retry success, non-retryable validation failure, exhausted retries
to dead-letter/manual review, and reconciliation detecting downstream
inconsistency. None of this is live telemetry.
