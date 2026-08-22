# ai/

Bounded agentic-AI reference layer for Milestone 5.

**Status: implemented (Milestone 5) — deterministic reference architecture
only.** No live Copilot Studio tenant, Azure OpenAI/Foundry call,
production LLM deployment, autonomous case mutation, enterprise knowledge
connector, credential, or production telemetry exists here.
Explicitly: no autonomous case mutation is implemented.

## Module map

| Module | Purpose |
|--------|---------|
| `tools.py` | Allow-listed tool registry with risk classes (`read-only`, `recommendation`, `state-changing`, `consequential`) and approval enforcement. |
| `agents.py` | Five bounded agent definitions: Intake, Knowledge, Triage, Case Summary, and Service Operations Coordinator. |
| `knowledge.py` | Small synthetic operational support knowledge corpus and deterministic lexical retrieval. |
| `triage.py` | Deterministic AI-triage recommendation interface: suggested category, priority, queue, rationale, confidence, and uncertainty. |
| `prompts.py` | Versioned prompt/template metadata for triage, summarisation, knowledge answering, tool selection, and escalation explanation. |
| `safety.py` | Deterministic safety/refusal checks for clinical, secret, and unsupported/governance-bypassing requests. |
| `orchestration.py` | Small helpers for tool-call planning, grounded knowledge answers, case summaries, and triage wrapper calls. |
| `evaluation.py` | Synthetic evaluation harness and evidence generator. Run via `python -m ai.evaluation`. |

## Boundary

Agents can interpret, summarize, retrieve knowledge, recommend triage, and
propose tool calls. They do **not** decide lifecycle validity, routing, SLA
calculation, escalation logic, approval rules, or canonical case state.

State-changing tools (`transition_case`, `resolve_case`) require human
approval through the explicit tool registry gate. The canonical
`business_process` package still rejects invalid transitions even if an AI
recommendation is wrong.

As of Milestone 8, [`governance/policies.py`](../governance/policies.py)
also checks that state-changing and consequential tools remain approval-gated,
and [`governance/attestations.py`](../governance/attestations.py) produces a
synthetic access attestation for the bounded agent tool registry.

## Evidence

`python -m ai.evaluation` regenerates:

- `data/synthetic/copilot_conversations.json`
- `data/synthetic/agent_tool_traces.json`
- `data/synthetic/ai_evaluation_cases.json`
- `data/synthetic/service_knowledge_corpus.json`
- `copilot/copilot_studio/topics.json`
- `copilot/prompts/prompt_templates.json`
- `reports/agentic_ai_evaluation_summary.json`

All are synthetic/reference artefacts, not live telemetry.
