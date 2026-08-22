# Architecture Decisions

This is a lightweight reviewer index, not a full ADR programme. It captures the
decisions most important to understanding the repository.

| Decision | Rationale | Where to Review |
|---|---|---|
| Canonical service operations are independent of CRM platforms. | Lifecycle, priority, routing, SLA, escalation, and audit history must be consistent across channels. | [`business_process/`](../business_process/), [`docs/business_process.md`](business_process.md) |
| Dynamics 365 and Salesforce are adapters, not rule owners. | Platform mappings should translate canonical state without recreating business logic. | [`dynamics365/`](../dynamics365/), [`salesforce/`](../salesforce/), [`tests/test_adapter_boundary.py`](../tests/test_adapter_boundary.py) |
| Power Platform orchestrates canonical operations. | Flows/apps/portals coordinate intake, approvals, notifications, and evidence without becoming a rules engine. | [`power_platform/`](../power_platform/) |
| Reference workflow specifications are versioned instead of fabricating SaaS exports. | JSON/Markdown specs are reviewable and honest without implying a live tenant. | [`power_platform/power_automate/`](../power_platform/power_automate/) |
| AI interprets, summarizes, retrieves, and recommends; deterministic rules decide. | Bounded agentic AI must not own lifecycle validity, SLA math, routing, escalation, or case state. | [`ai/`](../ai/), [`copilot/`](../copilot/) |
| Consequential actions require human approval. | State-changing or high-impact actions need auditable human control before execution. | [`ai/tools.py`](../ai/tools.py), [`power_platform/approvals.py`](../power_platform/approvals.py) |
| Evidence is deterministic and synthetic. | Reviewers can inspect generated artefacts without mistaking them for live telemetry or customer data. | [`data/README.md`](../data/README.md), [`reports/README.md`](../reports/README.md) |
| Analytics is downstream of operations. | Fabric-style metrics should consume evidence and never become a transactional source of truth. | [`analytics/`](../analytics/) |
| Transport is separated from domain logic. | Integration code validates, correlates, retries, observes, and reconciles messages without owning canonical decisions. | [`integrations/`](../integrations/) |
| Governance provides reference assurance, not production certification. | The repository can be reviewed and released consistently without claiming live GRC, compliance, or operational controls. | [`governance/`](../governance/), [`reports/release_assurance.json`](../reports/release_assurance.json) |
