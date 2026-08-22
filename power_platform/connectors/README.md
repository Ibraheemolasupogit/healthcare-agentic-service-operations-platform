# power_platform/connectors/

The intended connector/API boundary between Power Platform (Power
Automate/Power Apps) and the canonical service layer — a custom-connector-
style contract, documented as a reference. **No live HTTP endpoint, custom
connector definition, or Dataverse plugin exists.**

`operations.json` is generated (deterministically, from
`power_platform/connectors.py`) by running:

```
python -m power_platform.evidence
```

## Format

Each entry is the JSON form of a `power_platform.connector_spec.ConnectorOperation`:

| Field | Meaning |
|-------|---------|
| `name` | The operation name a flow's `connector_call` steps reference. |
| `description` | What it does and what it wraps. |
| `wraps_canonical` | The `business_process` function this operation is a facade over, or `null`. |
| `wraps_adapter` | The `dynamics365` function this operation is a facade over, or `null`. |
| `request_schema` / `response_schema` | Field name → informal type description. |
| `example_request` / `example_response` | A real, deterministic example — built by actually calling the wrapped function against a synthetic fixture, not hand-typed. |
| `idempotent` | Whether repeating the call with the same input is safe. |
| `requires_correlation_id` | Whether callers must supply/propagate a correlation id. |
| `caveat` | Anything a real implementation would need to know that this reference contract doesn't fully capture. |

## The nine operations

Eight match the Milestone 4 brief directly; a ninth,
`sync_dynamics_representation`, is an explicitly justified addition (see its
`caveat`/description in `operations.json`) because both the intake and
resolution-notification flows need a distinct step for "persist the
translated representation to the CRM boundary," which is CRM-facing rather
than canonical-facing.

| Operation | Wraps | Idempotent | Notes |
|-----------|-------|------------|-------|
| `create_case` | `business_process.create_case` | No | Caller must de-duplicate retried submissions — `create_case` has no natural idempotency key. |
| `transition_case` | `business_process.transition_case` | Yes (in effect) | A repeat call past a legal move raises `InvalidLifecycleTransitionError`, not a silent success. |
| `get_case` | *(none)* | Yes | **No persistence layer exists yet** — this contract is defined ahead of that milestone; its example is drawn from a synthetic fixture, not a live read. |
| `evaluate_sla` | `business_process.get_sla_target` + `evaluate_sla` | Yes | No breach-threshold maths performed by the connector. |
| `evaluate_escalation` | `business_process.determine_escalation_reason` | Yes | No escalation heuristic performed by the connector. |
| `resolve_case` | `business_process.resolve_case` | Yes (in effect) | Same idempotency mechanism as `transition_case`. |
| `list_service_categories` | *(none — static read)* | Yes | No decision involved. |
| `retrieve_queue_assignment` | `business_process.route_category` + `assign_owner` | Yes | Returns the **canonical** `Queue` value, not a platform display name. |
| `sync_dynamics_representation` | *(adapter)* `dynamics365.to_dynamics_incident` | Yes | No live Dataverse write occurs; `"upserted"` describes intended real behaviour only. |

## Idempotency and external IDs

See "Idempotency and external IDs" in
[`docs/crm_schema_mapping.md`](../../docs/crm_schema_mapping.md) — the same
pattern applies here: `business_process.models.Case.case_id` is the stable
key a real connector implementation would use for idempotent operations,
never a platform-issued or connector-generated id.
