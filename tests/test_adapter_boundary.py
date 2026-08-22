"""Proves the critical architecture rule: CRM adapters never decide business rules.

`dynamics365/` and `salesforce/` may import canonical *types* (Case,
CaseEvent, CaseStage, Priority, Queue, ResolutionOutcome, ...) to translate
already-decided values, but must never import or call a business_process
*decision* function: whether a lifecycle transition is valid, whether an SLA
has breached, whether a case should escalate, or which category routes to
which queue. Those decisions belong to business_process alone (see
docs/business_process.md §7 and docs/crm_schema_mapping.md).

This is enforced here via static source inspection (not just behavioural
tests) so a future change that reintroduces a decision-function import fails
CI immediately, regardless of whether a test happens to exercise it.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

ADAPTER_PACKAGES = ("dynamics365", "salesforce")

# Decision-making functions/tables that must never be imported by an adapter.
# Adapters receive their outcomes (stage, priority, queue, SLA due dates and
# breach flags) as plain values from the caller instead.
FORBIDDEN_BUSINESS_PROCESS_NAMES = frozenset(
    {
        # lifecycle decisions
        "validate_transition",
        "can_transition",
        "ALLOWED_TRANSITIONS",
        "transition_case",
        # escalation decisions
        "should_escalate",
        "determine_escalation_reason",
        # SLA decisions
        "evaluate_sla",
        "get_sla_target",
        # routing decisions
        "route_category",
        "assign_owner",
        "classify_and_route",
        "ROUTING_RULES",
        # case mutation / orchestration (adapters must never build/mutate a canonical Case)
        "create_case",
        "start_work",
        "mark_pending",
        "escalate_case",
        "resolve_case",
        "close_case",
    }
)


def _iter_adapter_source_files() -> list[Path]:
    files: list[Path] = []
    for package in ADAPTER_PACKAGES:
        files.extend((REPO_ROOT / package).glob("*.py"))
    return files


def _imported_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                names.add((alias.asname or alias.name).split(".")[0])
    return names


def test_adapter_packages_are_not_empty():
    # Sanity check that the scan below is actually scanning real files.
    assert len(_iter_adapter_source_files()) >= 3


def test_no_adapter_file_imports_a_business_process_decision_function():
    violations: dict[str, set[str]] = {}
    for path in _iter_adapter_source_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported = _imported_names(tree)
        forbidden_hits = imported & FORBIDDEN_BUSINESS_PROCESS_NAMES
        if forbidden_hits:
            violations[str(path.relative_to(REPO_ROOT))] = forbidden_hits
    assert not violations, f"Adapter file(s) import business rule decisions: {violations}"


def test_no_adapter_file_imports_business_process_sla_or_lifecycle_or_service_modules():
    """A stronger check: adapters must not even import the *modules* that
    hold decision logic, not just avoid naming individual functions."""
    forbidden_modules = {
        "business_process.sla",
        "business_process.lifecycle",
        "business_process.service",
    }
    violations: dict[str, set[str]] = {}
    for path in _iter_adapter_source_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported_modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module is not None:
                imported_modules.add(node.module)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name)
        hits = imported_modules & forbidden_modules
        if hits:
            violations[str(path.relative_to(REPO_ROOT))] = hits
    assert not violations, f"Adapter file(s) import business-rule modules directly: {violations}"


def _attribute_root_name(node: ast.Attribute) -> str | None:
    target = node.value
    while isinstance(target, ast.Attribute):
        target = target.value
    return target.id if isinstance(target, ast.Name) else None


def test_no_adapter_file_calls_business_process_via_module_attribute_access():
    """Covers the indirection loophole: `import business_process` then
    `business_process.evaluate_sla(...)` would dodge the import-name checks
    above without this."""
    violations: dict[str, set[str]] = {}
    for path in _iter_adapter_source_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        hits = {
            node.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Attribute) and _attribute_root_name(node) == "business_process"
        }
        if hits:
            violations[str(path.relative_to(REPO_ROOT))] = hits
    assert not violations, (
        f"Adapter file(s) access business_process via attribute chain: {violations}"
    )
