"""Proves power_platform orchestrates canonical rules without reimplementing them.

`power_platform`'s Python modules legitimately import `business_process`
and `dynamics365` — unlike the CRM adapters (see test_adapter_boundary.py),
its job is partly to *introspect* those packages (confirm a named operation
exists) and to build realistic example payloads for documentation by
actually calling canonical functions. So the blanket "must never import
these modules" rule from test_adapter_boundary.py does not apply here.

What must still hold, and what this file checks:

1. Every `CanonicalOperation`/`AdapterOperation` enum member resolves to a
   real, callable `business_process`/`dynamics365` attribute (checked in
   test_power_platform_flows.py) — a flow spec cannot invent a decision
   that doesn't exist in the canonical layer.
2. A `CONDITION`-kind workflow step (a pure branch) never carries an
   `operation` — enforced structurally by `validate_workflow_spec` and
   checked here directly against every real flow.
3. `power_platform/flow_validation.py` — the module that decides whether a
   flow spec is valid — never *calls* a business_process/dynamics365
   decision function itself, only inspects (`getattr`) whether one exists.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FLOW_VALIDATION_FILE = REPO_ROOT / "power_platform" / "flow_validation.py"

# Decision-making functions that flow_validation must never *call* (as
# opposed to merely referencing by name via getattr/CanonicalOperation).
FORBIDDEN_CALLS = frozenset(
    {
        "validate_transition",
        "should_escalate",
        "determine_escalation_reason",
        "evaluate_sla",
        "get_sla_target",
        "route_category",
        "assign_owner",
        "classify_and_route",
        "create_case",
        "transition_case",
        "start_work",
        "mark_pending",
        "escalate_case",
        "resolve_case",
        "close_case",
        "to_dynamics_incident",
        "to_dynamics_timeline",
    }
)


def _called_function_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                names.add(func.id)
            elif isinstance(func, ast.Attribute):
                names.add(func.attr)
    return names


def test_flow_validation_never_calls_a_canonical_or_adapter_decision_function():
    tree = ast.parse(
        FLOW_VALIDATION_FILE.read_text(encoding="utf-8"), filename=str(FLOW_VALIDATION_FILE)
    )
    called = _called_function_names(tree)
    violations = called & FORBIDDEN_CALLS
    assert not violations, f"flow_validation.py calls decision function(s): {violations}"


def test_flow_validation_only_uses_getattr_to_check_business_process_and_dynamics365():
    """`business_process`/`dynamics365` may only be accessed via `getattr(module, name, ...)`
    in flow_validation.py — never `module.some_function(...)`."""
    tree = ast.parse(
        FLOW_VALIDATION_FILE.read_text(encoding="utf-8"), filename=str(FLOW_VALIDATION_FILE)
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            target = node.value
            if isinstance(target, ast.Name) and target.id in ("business_process", "dynamics365"):
                raise AssertionError(
                    f"flow_validation.py accesses {target.id}.{node.attr} directly — "
                    "must use getattr() for introspection only"
                )


def test_no_condition_step_in_any_real_flow_carries_an_operation():
    from power_platform.flows import ALL_FLOWS
    from power_platform.workflow_spec import StepKind

    for flow in ALL_FLOWS:
        for step in flow.steps:
            if step.kind is StepKind.CONDITION:
                assert step.operation is None, f"{flow.flow_id}/{step.step_id}"


def test_canonical_and_adapter_operation_vocabularies_are_closed_enums():
    """A flow step cannot reference an operation name outside the closed
    CanonicalOperation/AdapterOperation vocabularies — validate_workflow_spec
    checks membership, not just existence, preventing an invented name that
    happens to collide with something else."""
    from power_platform.workflow_spec import AdapterOperation, CanonicalOperation

    assert "delete_case" not in {op.value for op in CanonicalOperation}
    assert "delete_case" not in {op.value for op in AdapterOperation}
