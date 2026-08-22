"""Boundary tests for analytics."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ANALYTICS_DIR = REPO_ROOT / "analytics"

FORBIDDEN_ASSIGNMENT_NAMES = {
    "ALLOWED_TRANSITIONS",
    "ROUTING_RULES",
    "BASE_SLA_TARGETS",
    "CATEGORY_RESOLUTION_MULTIPLIER",
    "ESCALATION_RULES",
}


def _python_files() -> list[Path]:
    return sorted(path for path in ANALYTICS_DIR.rglob("*.py") if path.name != "__init__.py")


def test_analytics_modules_do_not_define_operational_rule_tables():
    for path in _python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        assert target.id not in FORBIDDEN_ASSIGNMENT_NAMES, str(path)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                assert node.target.id not in FORBIDDEN_ASSIGNMENT_NAMES, str(path)


def test_analytics_does_not_import_crm_adapters_directly():
    for path in _python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                module = node.module if isinstance(node, ast.ImportFrom) else ""
                names = [alias.name for alias in getattr(node, "names", [])]
                imported = " ".join([module or "", *names])
                assert "dynamics365" not in imported
                assert "salesforce" not in imported


def test_analytics_readme_states_not_transactional_source_of_truth():
    text = (ANALYTICS_DIR / "README.md").read_text(encoding="utf-8").lower()
    assert "does not become a transactional source of truth" in text
