"""Boundary tests for Milestone 5 AI modules.

The AI layer may import canonical packages for examples, summaries, and
validation, but it must not define its own lifecycle/SLA/routing/escalation
tables or allow prompt/tool text to become the rule source.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AI_DIR = REPO_ROOT / "ai"

FORBIDDEN_ASSIGNMENT_NAMES = {
    "ALLOWED_TRANSITIONS",
    "ROUTING_RULES",
    "DEFAULT_QUEUE_OWNERS",
    "BASE_SLA_TARGETS",
    "CATEGORY_RESOLUTION_MULTIPLIER",
    "ESCALATION_RULES",
}


def _python_files() -> list[Path]:
    return sorted(path for path in AI_DIR.rglob("*.py") if path.name != "__init__.py")


def test_ai_modules_do_not_define_canonical_rule_tables():
    for path in _python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        assert target.id not in FORBIDDEN_ASSIGNMENT_NAMES, str(path)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                assert node.target.id not in FORBIDDEN_ASSIGNMENT_NAMES, str(path)


def test_ai_modules_do_not_import_crm_adapters_directly():
    for path in _python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                module = node.module if isinstance(node, ast.ImportFrom) else ""
                names = [alias.name for alias in getattr(node, "names", [])]
                imported = " ".join([module or "", *names])
                assert "dynamics365" not in imported
                assert "salesforce" not in imported


def test_boundary_docs_avoid_autonomous_case_mutation_claims():
    text = (AI_DIR / "README.md").read_text(encoding="utf-8").lower()
    assert "no autonomous case mutation" in text
