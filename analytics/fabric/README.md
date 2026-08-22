# analytics/fabric/

Fabric-style analytical transformation layer for Milestone 6. This is a
local, deterministic reference implementation only: no Microsoft Fabric
workspace, Lakehouse, Warehouse, Spark notebook, Data Factory pipeline, or
deployment exists.

## Medallion Design

| Layer | Implemented shape | Source |
|-------|-------------------|--------|
| Bronze | Raw/source-aligned records: cases, case events, CRM mapping examples, automation traces, approval records, Copilot conversations, agent tool traces, AI evaluation evidence, integration delivery traces, reconciliation cases | Existing generated JSON evidence under `data/synthetic/` and `reports/` |
| Silver | Conformed entities: service case, lifecycle event, queue, SLA event, escalation, automation execution, agent interaction, approval decision, integration delivery | `analytics.fabric.silver.build_silver_model()` |
| Gold | Business-ready outputs: case metrics, SLA summary, automation metrics, Copilot/AI usage, integration delivery metrics | `analytics.fabric.gold.build_gold_model()` |

Analytics remains downstream of the operational system. It never writes back
to `business_process`, CRM adapters, Power Platform specs, or AI tools.

## Lineage

```text
Synthetic operational fixture
-> canonical service domain
-> CRM / automation / agent / integration evidence
-> analytics Bronze ingestion
-> Silver conformed operational entities
-> Gold KPI outputs
-> semantic model measures
-> Power BI reference report
```

## Data Quality

`data_quality.py` validates required IDs, category/priority/status values,
duplicate case IDs, timestamp shape, non-negative durations, known queues,
referential integrity, and required correlation/idempotency IDs for automation,
agent, approval, and integration evidence.
