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
