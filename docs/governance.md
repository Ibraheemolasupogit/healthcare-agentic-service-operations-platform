# Governance & Responsible AI

This document expands on the governance summary in the
[root README](../README.md#8-governance--responsible-ai-principles).

## Why governance is designed in from Milestone 1

A common failure mode in real service-operations platforms is treating audit,
access control, and responsible-AI guardrails as something added after a
system works. This repository instead reserves a first-class bounded context,
[`governance/`](../governance/), from the very first milestone — even though
it currently holds only a placeholder — so that every later milestone has a
defined place to plug audit logging and access-policy design into.

## Human-in-the-loop vs. autonomous action

Two categories of system behaviour are kept explicitly distinct throughout
this repository:

- **Deterministic automation** ([`power_platform/`](../power_platform/)) —
  fixed rules produce fixed, predictable outcomes for a given input. No model
  inference is involved in the decision.
- **Agentic AI behaviour** ([`ai/`](../ai/), [`copilot/`](../copilot/)) —
  model-driven decisions that may vary for the same input. Any such decision
  that would change case state, notify a person, or take another real-world
  action is designed to require a human checkpoint before it takes effect,
  unless a future milestone explicitly documents a narrower, reviewed
  exception.

## Least privilege and auditable activity

Every integration ([`integrations/`](../integrations/)) and every agent
([`ai/`](../ai/)) is designed against the minimum access it needs for its
specific task. Every agent action is designed to be logged in a form that can
be reviewed after the fact — who/what triggered it, what it did, and what
approved it — rather than being opaque.

As of Milestone 2, the *data model* for this exists: every case carries a
`CaseEvent` history (`business_process/models.py`) recording who (`actor`),
what (`event_type`/`detail`), and when for every lifecycle move, resolution,
and escalation. This is the audit data shape only — durable storage,
tamper-evidence, and cross-case audit review/reporting remain
[`governance/`](../governance/) responsibilities for a later milestone.

As of Milestone 3, "least privilege" is also concretely demonstrated at the
integration boundary: [`dynamics365/`](../dynamics365/) and
[`salesforce/`](../salesforce/) hold no credentials, no SDK client, and no
network access at all — they are pure functions over data already in
memory. Least privilege for a *live* connector (what it may read/write, and
under what identity) remains a later production concern.

As of Milestone 4, Power Platform controls are documented but not operated:
[`power_platform/`](../power_platform/) contains reference specifications,
connector contracts, approval examples, and synthetic evidence only. A real
tenant implementation would need:

- Separate development, test, and production Power Platform environments,
  with solution-aware configuration promoted between them.
- Least-privilege connection references and service identities scoped to the
  connector operations they call; no maker or administrator identity should
  be embedded in a flow definition.
- Secrets stored outside flow specifications, for example in managed
  connection configuration or a governed secret store; this repository must
  never contain tenant IDs, client secrets, certificates, or passwords.
- DLP policies that prevent service-operation flows from mixing healthcare
  case data connectors with unmanaged consumer connectors.
- Human approval for consequential actions such as elevated access grants,
  recorded with requester, approver role, decision, reason, timestamp,
  correlation id, audit result, and timeout/exception outcome.
- Manual-review/dead-letter handling for failed canonical-to-CRM sync,
  notification failure, duplicate trigger ambiguity, and partial failure
  after canonical state has already changed.
- Reconciliation reporting that treats `business_process` canonical state
  as the source of truth and Dataverse/CRM records as synchronized
  representations.

These are design controls only in Milestone 4. There is no deployed
environment, DLP policy, connection reference, service principal, custom
connector, or live audit store in this repository.

As of Milestone 5, Copilot/agentic controls are implemented as deterministic
reference artefacts:

- Grounded responses use the synthetic operational knowledge corpus in
  [`ai/knowledge.py`](../ai/knowledge.py); no clinical diagnosis/treatment
  content is included.
- Tool selection is allow-listed in [`ai/tools.py`](../ai/tools.py), with
  read-only, recommendation, state-changing, and consequential risk classes.
- State-changing tools require human approval before invocation, and
  canonical `business_process` validation still rejects invalid operations.
- Prompt assets in [`ai/prompts.py`](../ai/prompts.py) carry prompt id,
  version, purpose, input schema, output schema, and safety constraints.
  They explicitly avoid embedding lifecycle, routing, SLA, escalation, or
  approval rules.
- Safety checks refuse clinical diagnosis/treatment, secret/credential
  disclosure, and unsupported/governance-bypassing actions.
- Synthetic agent traces and evaluations are generated by
  [`ai/evaluation.py`](../ai/evaluation.py); they are not live telemetry.

There is no live Copilot Studio tenant, Azure OpenAI/Foundry endpoint,
production LLM deployment, autonomous case mutation, enterprise knowledge
connector, or production telemetry in Milestone 5.

As of Milestone 6, analytics governance is implemented as reference metadata
and deterministic checks:

- All analytics inputs are synthetic generated evidence from this repository.
- Lineage is documented from fixture/source evidence through Bronze, Silver,
  Gold, semantic measures, and report pages.
- Metric definitions live in [`analytics/fabric/gold.py`](../analytics/fabric/gold.py)
  and the semantic-model metadata, with tests covering KPI outputs.
- Data-quality checks validate IDs, canonical enum values, timestamps,
  duplicate case IDs, queue references, referential integrity, non-negative
  durations, and required correlation IDs.
- Analytics ownership is separated from operations: analytics can summarize
  and report, but must not update canonical cases, CRM mappings, Power
  Platform workflow specs, or AI tool decisions.
- Reproducibility is enforced through deterministic generators and tracked
  summaries under [`reports/`](../reports/); CSV exports under `outputs/`
  are reproducible and ignored by default.
- Semantic-model and Power BI artefacts are specifications only. There is no
  live Fabric workspace, Lakehouse/Warehouse, Spark job, deployed semantic
  model, deployed Power BI report, live CRM telemetry ingestion, production
  monitoring, or production deployment.

As of Milestone 7, integration transport governance is implemented as local,
deterministic reference logic:

- `IntegrationEnvelope` carries source, target, correlation, causation,
  idempotency, and trace metadata without becoming a business-rule owner.
- Conceptual service-to-service authorization validates source binding,
  audience, environment, and the `integration:deliver` scope. The repository
  does not issue tokens and contains no webhook secrets, client secrets,
  certificates, tenant IDs, or production endpoints.
- Idempotency suppresses already delivered duplicates while allowing failed
  deliveries to be retried after recovery.
- Retry/backoff logic records metadata only; tests do not sleep and no
  network call is made.
- Dead-letter/manual-review outcomes are explicit for exhausted retries and
  non-recoverable delivery failures.
- Reconciliation detects downstream inconsistency without mutating canonical
  case state.
- Synthetic delivery traces and metrics are generated by
  [`integrations/evidence.py`](../integrations/evidence.py); they are not
  live webhook runs, production telemetry, or evidence of deployed
  monitoring.

## Data governance

All data anywhere in this repository — code fixtures, docs examples, anything
under [`data/`](../data/) — must be synthetic. See
[`data/README.md`](../data/README.md) for the specific rules. No file in this
repository should be presented, formatted, or named in a way that could be
mistaken for a real NHS or healthcare-provider data export.

## Portfolio scope

This document describes governance *principles* that the repository's
architecture is designed around. It does not claim that governance controls
are implemented, certified, or operating — see
[Current Implementation Status](../README.md#9-current-implementation-status)
and the [disclaimer](../README.md#10-portfolio--simulation-disclaimer).
