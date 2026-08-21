# ai/

Bounded context for **agentic AI** patterns.

**Status: placeholder — not implemented.** This directory currently contains no
agent implementation, prompts, or model configuration, because none has been
built yet.

**Intended scope (future milestone):** bounded, auditable autonomous actions
over the [`business_process`](../business_process/) case lifecycle — e.g.
classification or first-pass triage — with explicit scoping of what an agent
may do unsupervised versus what requires human approval. Every agent action is
designed to be logged via [`governance/`](../governance/) and to hold no more
access than it needs (least privilege). See
[`docs/architecture.md`](../docs/architecture.md) for the deterministic-
automation-vs-agentic-behaviour distinction and
[`docs/governance.md`](../docs/governance.md) for the responsible-AI
principles this domain must follow.
