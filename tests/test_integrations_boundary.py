"""Boundary tests for Milestone 7 transport architecture."""

import ast
from pathlib import Path

INTEGRATIONS_DIR = Path(__file__).resolve().parents[1] / "integrations"
TRANSPORT_MODULES = (
    "delivery.py",
    "idempotency.py",
    "reconciliation.py",
    "retry.py",
    "security.py",
    "transport.py",
    "webhooks.py",
)

FORBIDDEN_RULE_IDENTIFIERS = {
    "ALLOWED_TRANSITIONS",
    "ROUTING_RULES",
    "BASE_SLA_TARGETS",
    "CATEGORY_RESOLUTION_MULTIPLIER",
    "ESCALATION_RULES",
    "TOOL_REGISTRY",
    "TOOL_REGISTRY_BY_NAME",
}

FORBIDDEN_RULE_IMPORT_PREFIXES = (
    "business_process.lifecycle",
    "business_process.routing",
    "business_process.sla",
    "business_process.escalation",
    "ai.tools",
)


def _tree(module_name: str) -> ast.AST:
    return ast.parse((INTEGRATIONS_DIR / module_name).read_text(encoding="utf-8"))


def test_transport_modules_do_not_redefine_canonical_or_ai_rule_tables():
    for module_name in TRANSPORT_MODULES:
        names = {node.id for node in ast.walk(_tree(module_name)) if isinstance(node, ast.Name)}
        assert names.isdisjoint(FORBIDDEN_RULE_IDENTIFIERS), module_name


def test_transport_modules_do_not_import_canonical_rule_or_ai_permission_modules():
    for module_name in TRANSPORT_MODULES:
        tree = _tree(module_name)
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        assert not any(
            imported.startswith(prefix)
            for imported in imports
            for prefix in FORBIDDEN_RULE_IMPORT_PREFIXES
        ), module_name
