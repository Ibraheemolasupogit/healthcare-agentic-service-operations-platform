# Delivery Roadmap

This document expands on the roadmap summary in the
[root README](../README.md#7-delivery-roadmap). Scope and sequencing below are
indicative and may evolve as the portfolio project progresses — nothing past
Milestone 1 is committed or scheduled against dates.

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

## Milestone 3 — Dynamics 365 & Salesforce CRM Adapter Architecture *(this milestone)*

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

## Milestone 4 — Power Platform Automation *(planned)*

Deterministic workflow patterns (Power Automate flow designs, Dataverse
schema) for routing, notification, and escalation steps of the case
lifecycle.

## Milestone 5 — Copilot Studio & Agentic AI *(planned)*

Conversational triage patterns (Copilot Studio) and bounded autonomous case
actions ([`ai/`](../ai/)), with human-in-the-loop checkpoints defined per the
principles in [`docs/governance.md`](governance.md).

## Milestone 6 — Integration Layer *(planned)*

Live transport around the `IntegrationEnvelope` contract introduced in
Milestone 3 (`integrations/envelope.py`) — an actual API client/message
mechanism connecting the bounded contexts built in Milestones 3–5, with
retries and delivery guarantees. Milestone 3 deliberately stopped at the
data contract and a deterministic example generator; no transport exists
yet.

## Milestone 7 — Fabric / Power BI Analytics *(planned)*

Operational reporting over the synthetic case data from Milestone 2, designed
as portable evidence under [`reports/`](../reports/).

## Milestone 8 — Governance Hardening *(planned)*

Audit-trail implementation, access-policy design, and responsible-AI
guardrails for the agentic behaviour introduced in Milestone 5.
