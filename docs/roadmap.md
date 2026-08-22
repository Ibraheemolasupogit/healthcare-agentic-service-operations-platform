# Delivery Roadmap

This document expands on the roadmap summary in the
[root README](../README.md#7-delivery-roadmap). Scope and sequencing below are
indicative and may evolve as the portfolio project progresses. Milestones 1-7
are implemented in this repository; later milestones are not committed or
scheduled against dates.

## Milestone 1 — Repository Foundation *(done)*

Architecture-first repository scaffold: bounded-context directories for every
target domain, a platform-neutral service taxonomy and case lifecycle
(types only, in [`business_process/`](../business_process/)), and an
engineering baseline (packaging, lint, type-check, tests, Docker, CI).
No platform integration, agent, or analytics code.

## Milestone 2 — Business Process Modelling & Platform-Neutral Service Operations Model *(done)*

Turned the Milestone 1 taxonomy/lifecycle types into an actual (still
platform-neutral) case model: the `Case`/`CaseEvent` aggregate, enforced
lifecycle transition rules, priority, deterministic queue/routing, a
configurable SLA model, deterministic escalation triggers, resolution
outcomes, serialization, and a deterministic synthetic dataset generator
under [`data/synthetic/`](../data/synthetic/) and
[`reports/`](../reports/). See [`docs/business_process.md`](business_process.md).
Still no persistence, workflow engine, or scheduler — and still no CRM,
Power Platform, Copilot Studio, or agent code.

## Milestone 3 — Dynamics 365 & Salesforce CRM Adapter Architecture *(done)*

Built reference adapters — [`dynamics365/`](../dynamics365/) and
[`salesforce/`](../salesforce/) — mapping the Milestone 2 canonical case
model onto each platform's concepts (`incident`/`Case`, queue/ownership,
priority, lifecycle/status, SLA metadata, audit timeline, resolution) via
pure, typed, deterministic translation functions and explicit mapping
tables. Added a lightweight `IntegrationEnvelope` contract and a
deterministic cross-CRM example generator under
[`integrations/`](../integrations/). Full field-by-field mapping and
caveats are in [`docs/crm_schema_mapping.md`](crm_schema_mapping.md).
Neither adapter imports a `business_process` decision function — enforced
by `tests/test_adapter_boundary.py`. Not a live tenant, connected app, SDK
session, or credential in either case.

## Milestone 4 — Power Platform Automation Architecture *(done)*

Deterministic Power Platform orchestration around the canonical service
operations model: version-controlled Power Automate reference workflow
specifications, Power Apps service-operations application architecture,
Power Pages self-service portal architecture, connector/API contracts,
human approval pattern, reliability/security guidance, and deterministic
synthetic automation evidence. This milestone deliberately stops at
reference specifications and generated evidence — no live Microsoft tenant,
exported Power Automate solution, `.msapp`, deployed portal, custom
connector, Dataverse API call, credential, Copilot Studio, LLM triage, or
autonomous agent is implemented.

## Milestone 5 — Copilot Studio & Bounded Agentic AI *(done)*

Reference Copilot Studio topics, bounded agent definitions, an explicit
tool allow-list, deterministic knowledge retrieval, AI-triage recommendations,
prompt/version metadata, safety controls, human approval gates, deterministic
evaluation, and synthetic evidence. This milestone deliberately uses local
deterministic behaviour only: no live Copilot Studio tenant, Azure OpenAI or
Foundry call, production LLM deployment, autonomous case mutation, live
enterprise knowledge connector, or production telemetry.

## Milestone 6 — Fabric Analytics and Operational Intelligence *(done)*

Fabric-style analytical modelling over existing generated evidence:
Bronze/Silver/Gold local transformations, operational KPIs, data-quality
checks, semantic-model metadata, Power BI report specification, lineage
documentation, and deterministic analytics reports/CSV exports. This milestone
does not deploy Fabric, Spark, Lakehouse/Warehouse, semantic model, Power BI,
or production telemetry.

## Milestone 7 — Integration Transport, Reliability and Observability *(done)*

Local/reference transport around the `IntegrationEnvelope` contract introduced
in Milestone 3 (`integrations/envelope.py`): inbound webhook/API request
handling, conceptual authentication/authorization checks, idempotency,
retry/backoff metadata, delivery states, outbound transport stubs,
reconciliation, integration observability, and deterministic synthetic
evidence. It preserves the existing connector/tool/canonical boundary and
does not make live SaaS calls.

Still not implemented: public production API, live Dynamics/Salesforce/Power
Platform webhooks, production OAuth/token exchange, broker deployment, Azure
Service Bus/Event Grid, live monitoring backend, or production integration
deployment.

## Milestone 8 — Governance Hardening *(planned)*

Audit-trail implementation, access-policy design, and responsible-AI
guardrails for the agentic behaviour introduced in Milestone 5.
