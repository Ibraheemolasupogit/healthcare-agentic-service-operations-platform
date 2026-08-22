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

## Milestone 2 — Business Process Modelling & Platform-Neutral Service Operations Model *(this milestone)*

Turned the Milestone 1 taxonomy/lifecycle types into an actual (still
platform-neutral) case model: the `Case`/`CaseEvent` aggregate, enforced
lifecycle transition rules, priority, deterministic queue/routing, a
configurable SLA model, deterministic escalation triggers, resolution
outcomes, serialization, and a deterministic synthetic dataset generator
under [`data/synthetic/`](../data/synthetic/) and
[`reports/`](../reports/). See [`docs/business_process.md`](business_process.md).
Still no persistence, workflow engine, or scheduler — and still no CRM,
Power Platform, Copilot Studio, or agent code.

## Milestone 3 — Dynamics 365 & Salesforce Bounded Contexts *(planned)*

Reference design artefacts (schema/entity modelling, illustrative
configuration, and adapter functions per
[`docs/business_process.md`](business_process.md) §7) showing how the
Milestone 2 canonical case model maps onto each platform. Not a live tenant
or connected app in either case.

## Milestone 4 — Power Platform Automation *(planned)*

Deterministic workflow patterns (Power Automate flow designs, Dataverse
schema) for routing, notification, and escalation steps of the case
lifecycle.

## Milestone 5 — Copilot Studio & Agentic AI *(planned)*

Conversational triage patterns (Copilot Studio) and bounded autonomous case
actions ([`ai/`](../ai/)), with human-in-the-loop checkpoints defined per the
principles in [`docs/governance.md`](governance.md).

## Milestone 6 — Integration Layer *(planned)*

API-first service contracts connecting the bounded contexts built in
Milestones 3–5, replacing any direct coupling assumed in earlier milestones.

## Milestone 7 — Fabric / Power BI Analytics *(planned)*

Operational reporting over the synthetic case data from Milestone 2, designed
as portable evidence under [`reports/`](../reports/).

## Milestone 8 — Governance Hardening *(planned)*

Audit-trail implementation, access-policy design, and responsible-AI
guardrails for the agentic behaviour introduced in Milestone 5.
