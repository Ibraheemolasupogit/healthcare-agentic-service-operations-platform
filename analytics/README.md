# analytics/

Bounded context for **Microsoft Fabric / Power BI** analytics patterns.

**Status: implemented (Milestone 6) as deterministic reference analytics.**
No live Fabric workspace, Lakehouse, Warehouse, Spark job, semantic-model
deployment, Power BI report, workspace, or production telemetry exists.

## Contents

| Area | Purpose |
|------|---------|
| [`fabric/`](fabric/) | Bronze/Silver/Gold-style local transformations over existing repository evidence. |
| [`semantic_model/`](semantic_model/) | Reference semantic model metadata for a future Power BI dataset. |
| [`powerbi/`](powerbi/) | Reference dashboard/report page specification. |

## Evidence

Run:

```text
python -m analytics.fabric.evidence
```

This regenerates tracked reports:

- `reports/analytics_summary.json`
- `reports/service_operations_report.md`

It also regenerates ignored, reproducible CSV exports under `outputs/`:

- `outputs/case_metrics.csv`
- `outputs/sla_summary.csv`
- `outputs/automation_metrics.csv`
- `outputs/copilot_usage.csv`

Analytics consumes existing canonical, CRM, automation, approval, Copilot,
agent, and AI-evaluation evidence. It does not invent live telemetry and
does not become a transactional source of truth.
