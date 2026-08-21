"""Sanity checks on the Milestone 1 repository scaffold.

These tests guard against the foundation structure (domain directories, their
placeholder documentation, and the top-level engineering baseline files)
being accidentally removed or renamed in later milestones.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

DOMAIN_DIRECTORIES = [
    "business_process",
    "dynamics365",
    "salesforce",
    "power_platform",
    "copilot",
    "ai",
    "analytics",
    "integrations",
    "governance",
    "data",
    "outputs",
    "reports",
    "docs",
    "tests",
]

TOP_LEVEL_FILES = [
    "README.md",
    "pyproject.toml",
    "requirements.txt",
    ".gitignore",
    "Dockerfile",
]


def test_all_domain_directories_exist():
    for name in DOMAIN_DIRECTORIES:
        assert (REPO_ROOT / name).is_dir(), f"expected directory missing: {name}"


def test_platform_placeholder_domains_have_readmes():
    placeholder_domains = [
        "dynamics365",
        "salesforce",
        "power_platform",
        "copilot",
        "ai",
        "analytics",
        "integrations",
        "governance",
    ]
    for name in placeholder_domains:
        readme = REPO_ROOT / name / "README.md"
        assert readme.is_file(), f"expected placeholder README missing: {readme}"


def test_top_level_engineering_baseline_files_exist():
    for name in TOP_LEVEL_FILES:
        assert (REPO_ROOT / name).is_file(), f"expected top-level file missing: {name}"


def test_ci_workflow_exists():
    assert (REPO_ROOT / ".github" / "workflows" / "ci.yml").is_file()
