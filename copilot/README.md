# copilot/

Bounded context for **Copilot Studio** conversational AI patterns.

**Status: implemented (Milestone 5) as reference specifications only.** This
directory contains structured topic and prompt metadata; it does not contain
exported Copilot Studio solutions, deployed agents, screenshots, tenant IDs,
credentials, or live telemetry.

## Contents

- [`copilot_studio/`](copilot_studio/) — topic specs for service intake,
  status lookup, knowledge assistance, case summarisation support, suggested
  routing/triage, escalation explanation/request, and resolution feedback.
- [`prompts/`](prompts/) — versioned prompt/template metadata generated from
  [`ai/prompts.py`](../ai/prompts.py).

Conversational topics hand off to bounded orchestration and allow-listed
tools in [`ai/`](../ai/). They may interpret, summarize, classify, retrieve,
recommend, and propose actions; they do not become the source of truth for
case lifecycle, routing, SLA, escalation, approvals, or state.
