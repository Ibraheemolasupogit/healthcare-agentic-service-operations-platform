# business_process/

Platform-neutral business process domain — the canonical service operations
model that [`dynamics365/`](../dynamics365/) and [`salesforce/`](../salesforce/)
now map onto as of Milestone 3 (see
[`docs/business_process.md`](../docs/business_process.md) §7 and
[`docs/crm_schema_mapping.md`](../docs/crm_schema_mapping.md)). This package
still has no dependency on, or knowledge of, either CRM.

## Module map

| Module | Purpose |
|--------|---------|
| `taxonomy.py` | `ServiceCategory` (6 synthetic categories), `CaseStage` (8-stage lifecycle), `CASE_LIFECYCLE_ORDER` (Milestone 1, unchanged). |
| `priority.py` | `Priority` (Low/Medium/High/Critical) and its ordering. |
| `lifecycle.py` | Explicit allowed `CaseStage -> CaseStage` transitions and `validate_transition()` / `can_transition()`. Not a workflow engine — pure validation. |
| `queues.py` | `Queue`, deterministic `ROUTING_RULES` (category → queue), and default queue owners. |
| `sla.py` | `SLATarget`, priority/category-driven `get_sla_target()`, and breach evaluation via `evaluate_sla()` / `SLAStatus`. |
| `escalation.py` | `EscalationReason` and deterministic `should_escalate()` / `determine_escalation_reason()`. |
| `models.py` | The `Case` aggregate and its `CaseEvent` audit trail; `ResolutionOutcome`. |
| `service.py` | Small orchestration functions (`create_case`, `classify_and_route`, `start_work`, `mark_pending`, `escalate_case`, `resolve_case`, `close_case`) that combine the above and append audit events. |
| `serialization.py` | JSON-safe `case_to_dict()` / `case_event_to_dict()`. |
| `fixtures.py` | Six deterministic synthetic case fixtures (one per category), demonstrating varied lifecycle outcomes. |
| `evidence.py` | Generates portfolio evidence (`data/synthetic/*.json`, `reports/case_summary.json`) from the fixtures and config above. Run via `python -m business_process.evidence`. |

## Scope (implemented in Milestone 2, unchanged in Milestone 3)

Implemented: case model, lifecycle transition rules, priority, deterministic
routing/queues, a configurable SLA model, deterministic escalation triggers,
audit history, resolution outcomes, serialization, and deterministic
synthetic fixtures/evidence.

Not implemented (by design — see [`docs/roadmap.md`](../docs/roadmap.md)):
persistence/a database, a workflow engine or scheduler, Power
Platform/Copilot Studio code, AI-assisted triage, or autonomous agents.
`should_escalate()` is a deterministic rule check callable by a human or a
future governed agent — it is not itself agentic. Dynamics 365 and
Salesforce reference adapters (Milestone 3) consume this package's types
and functions but add no code here — see
[`dynamics365/README.md`](../dynamics365/README.md) and
[`salesforce/README.md`](../salesforce/README.md).

See [`docs/business_process.md`](../docs/business_process.md) for the full
service operating model, lifecycle diagram, routing diagram, SLA model,
escalation model, roles/responsibilities, and the canonical-domain-vs-adapter
boundary.
