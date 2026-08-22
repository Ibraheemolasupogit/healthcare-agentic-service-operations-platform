# Evidence Index

This index points reviewers to the strongest generated portfolio artefacts.
All evidence is synthetic, deterministic, and generated from repository code.
It is not live tenant telemetry, production monitoring, or customer data.

| Evidence | Location | Demonstrates |
|---|---|---|
| Service taxonomy and lifecycle | [`data/synthetic/service_taxonomy.json`](../data/synthetic/service_taxonomy.json) | Canonical service categories, lifecycle stages, and priority concepts. |
| Synthetic service cases | [`data/synthetic/cases.json`](../data/synthetic/cases.json) | Six deterministic service-operation fixtures with audit history. |
| Service case summary | [`reports/case_summary.json`](../reports/case_summary.json) | Compact generated summary of canonical fixtures and service categories. |
| Dynamics 365 mapping examples | [`data/synthetic/dynamics365_examples.json`](../data/synthetic/dynamics365_examples.json) | Canonical cases translated to deterministic Dynamics-style incident/timeline records. |
| Salesforce mapping examples | [`data/synthetic/salesforce_examples.json`](../data/synthetic/salesforce_examples.json) | The same canonical cases translated to deterministic Salesforce-style case/feed records. |
| Power Platform workflow specs | [`power_platform/power_automate/`](../power_platform/power_automate/) | Reference Power Automate flow specifications without exported SaaS solution packages. |
| Power Platform automation evidence | [`reports/automation_summary.json`](../reports/automation_summary.json) | Simulated workflow, connector, approval, retry, and audit-evidence counts. |
| Approval examples | [`data/synthetic/power_platform_approval_examples.json`](../data/synthetic/power_platform_approval_examples.json) | Human-in-the-loop approval examples for consequential non-clinical actions. |
| Copilot conversations | [`data/synthetic/copilot_conversations.json`](../data/synthetic/copilot_conversations.json) | Reference conversational intake, status, knowledge, escalation, and feedback examples. |
| Agent/tool traces | [`data/synthetic/agent_tool_traces.json`](../data/synthetic/agent_tool_traces.json) | Allow-listed bounded-agent tool usage with risk and approval controls. |
| AI evaluation cases | [`data/synthetic/ai_evaluation_cases.json`](../data/synthetic/ai_evaluation_cases.json) | Deterministic scenarios for intent, triage, refusal, tool safety, and canonical enforcement. |
| AI evaluation summary | [`reports/agentic_ai_evaluation_summary.json`](../reports/agentic_ai_evaluation_summary.json) | Summary of deterministic bounded-agent evaluation results. |
| Analytics summary | [`reports/analytics_summary.json`](../reports/analytics_summary.json) | Fabric-style KPI, data-quality, lineage, and integration-observability summary. |
| Service operations report | [`reports/service_operations_report.md`](../reports/service_operations_report.md) | Concise generated executive report over the small synthetic dataset. |
| Integration envelopes | [`data/synthetic/integration_envelopes.json`](../data/synthetic/integration_envelopes.json) | Reference envelopes carrying source, target, correlation, idempotency, and trace metadata. |
| Integration delivery traces | [`data/synthetic/integration_delivery_traces.json`](../data/synthetic/integration_delivery_traces.json) | Success, duplicate, retry, validation failure, dead-letter, and reconciliation scenarios. |
| Integration operations summary | [`reports/integration_operations_summary.json`](../reports/integration_operations_summary.json) | Delivery, duplicate, retry, failure, and dead-letter metrics. |
| Reconciliation report | [`reports/reconciliation_report.md`](../reports/reconciliation_report.md) | Deterministic findings for downstream delivery/representation inconsistency. |
| Audit evidence | [`data/synthetic/audit_evidence.json`](../data/synthetic/audit_evidence.json) | Reference audit records with correlation/provenance fields and chained SHA-256 digests. |
| Access attestations | [`data/synthetic/access_attestations.json`](../data/synthetic/access_attestations.json) | Reference attestations for service roles, agent tools, integration identities, and approvals. |
| Governance summary | [`reports/governance_summary.json`](../reports/governance_summary.json) | Control catalogue, policy findings, attestation count, and audit-chain verification. |
| Release assurance | [`reports/release_assurance.json`](../reports/release_assurance.json) | Bounded release-assurance result for the reference implementation. |
| Operational readiness | [`reports/operational_readiness.md`](../reports/operational_readiness.md) | Checklist separating implemented reference controls from future live operations. |
| Final assurance report | [`reports/final_assurance_report.md`](../reports/final_assurance_report.md) | Repository-level assurance summary, limitations, and release decision language. |

Regenerate evidence with the relevant module entry points:

```text
python3 -m business_process.evidence
python3 -m integrations.examples
python3 -m power_platform.evidence
python3 -m ai.evaluation
python3 -m integrations.evidence
python3 -m analytics.fabric.evidence
python3 -m governance.evidence
```
