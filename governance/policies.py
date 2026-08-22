"""Lightweight deterministic policy evaluation for release assurance."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from ai.tools import TOOL_REGISTRY, ToolRisk
from integrations.security import IntegrationPrincipal
from integrations.webhooks import SUPPORTED_SCHEMA_VERSION

REPO_ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {
    ".md",
    ".py",
    ".json",
    ".yml",
    ".yaml",
    ".toml",
    ".txt",
    ".flow",
}
EXCLUDED_DIRS = {".git", ".venv", ".mypy_cache", ".pytest_cache", ".ruff_cache", "__pycache__"}
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |)PRIVATE KEY-----"),
    re.compile(
        r"(?i)(?:secret|password|api[_-]?key|token)\s*[:=]\s*['\"][A-Za-z0-9_./+=-]{16,}['\"]"
    ),
)
PROHIBITED_PRODUCTION_CLAIMS = (
    "production ready",
    "regulatory compliant",
    "hipaa compliant",
    "nhs certified",
    "live tenant",
)


class PolicySeverity(StrEnum):
    """Policy finding severity."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class PolicyFinding:
    """One deterministic policy finding."""

    policy_id: str
    status: str
    severity: PolicySeverity
    message: str
    evidence: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "status": self.status,
            "severity": self.severity.value,
            "message": self.message,
            "evidence": self.evidence,
        }


def _text_files(repo_root: Path) -> tuple[Path, ...]:
    paths: list[Path] = []
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        if path.suffix in TEXT_SUFFIXES or path.name in {".gitignore", "Dockerfile"}:
            paths.append(path)
    return tuple(sorted(paths))


def _pass(policy_id: str, message: str, evidence: str) -> PolicyFinding:
    return PolicyFinding(policy_id, "pass", PolicySeverity.INFO, message, evidence)


def _critical(policy_id: str, message: str, evidence: str) -> PolicyFinding:
    return PolicyFinding(policy_id, "fail", PolicySeverity.CRITICAL, message, evidence)


def evaluate_secret_hygiene_policy(repo_root: Path = REPO_ROOT) -> PolicyFinding:
    """Check tracked-style text files for obvious live secret material."""
    hits: list[str] = []
    for path in _text_files(repo_root):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                hits.append(str(path.relative_to(repo_root)))
                break
    if hits:
        return _critical("POL-SEC-001", "Potential credential material detected.", ", ".join(hits))
    return _pass("POL-SEC-001", "No obvious credentials detected in repository text files.", ".")


def evaluate_agent_tool_policy() -> PolicyFinding:
    """Ensure state-changing/consequential agent tools are bounded."""
    violations = [
        tool.name
        for tool in TOOL_REGISTRY
        if tool.risk in {ToolRisk.STATE_CHANGING, ToolRisk.CONSEQUENTIAL}
        and not (
            tool.requires_human_approval or tool.name in {"create_case", "request_human_approval"}
        )
    ]
    if violations:
        return _critical(
            "POL-AI-001",
            "State-changing/consequential tools without approval controls.",
            ", ".join(violations),
        )
    return _pass("POL-AI-001", "Agent tool risk and approval gates are bounded.", "ai.tools")


def evaluate_integration_policy() -> PolicyFinding:
    """Check integration governance metadata remains explicit."""
    principal = IntegrationPrincipal(
        principal_id="policy-check",
        source_system="external",
        audience="healthcare-service-operations-integrations",
        environment="test",
        scopes=frozenset({"integration:deliver"}),
    )
    if principal.audience != "healthcare-service-operations-integrations":
        return _critical("POL-INT-001", "Unexpected integration audience.", principal.audience)
    if "integration:deliver" not in principal.scopes:
        return _critical(
            "POL-INT-001", "Integration delivery scope missing.", "IntegrationPrincipal"
        )
    if SUPPORTED_SCHEMA_VERSION != "1.0":
        return _critical(
            "POL-INT-001", "Unexpected integration schema version.", SUPPORTED_SCHEMA_VERSION
        )
    return _pass(
        "POL-INT-001",
        "Integration schema, audience, and delivery scope are explicitly governed.",
        "integrations.security + integrations.webhooks",
    )


def evaluate_synthetic_evidence_policy(repo_root: Path = REPO_ROOT) -> PolicyFinding:
    """Require generated evidence to carry provenance and synthetic/reference labels."""
    required_files = (
        repo_root / "reports" / "case_summary.json",
        repo_root / "reports" / "automation_summary.json",
        repo_root / "reports" / "agentic_ai_evaluation_summary.json",
        repo_root / "reports" / "analytics_summary.json",
        repo_root / "reports" / "integration_operations_summary.json",
    )
    missing_labels: list[str] = []
    for path in required_files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        text = json.dumps(payload).lower()
        if "generated" not in text and "synthetic" not in text:
            missing_labels.append(str(path.relative_to(repo_root)))
    if missing_labels:
        return _critical(
            "POL-DATA-001",
            "Generated evidence is missing synthetic/provenance labels.",
            ", ".join(missing_labels),
        )
    return _pass(
        "POL-DATA-001",
        "Tracked generated evidence carries synthetic/provenance labelling.",
        "reports/*.json",
    )


def evaluate_claim_discipline_policy(repo_root: Path = REPO_ROOT) -> PolicyFinding:
    """Reject unbounded production/compliance claims in docs."""
    hits: list[str] = []
    claim_paths = (repo_root / "README.md", *(repo_root / "docs").glob("*.md"))
    for path in claim_paths:
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for phrase in PROHIBITED_PRODUCTION_CLAIMS:
            for line in text.splitlines():
                if phrase in line and not _is_negated_claim(line):
                    hits.append(f"{path.relative_to(repo_root)}:{phrase}")
    if hits:
        return _critical(
            "POL-CLAIM-001", "Unbounded production/compliance claim found.", "; ".join(hits)
        )
    return _pass(
        "POL-CLAIM-001",
        "Documentation avoids unbounded production, deployment, and compliance claims.",
        "README.md + docs/",
    )


def _is_negated_claim(line: str) -> bool:
    return any(
        marker in line
        for marker in (
            "no ",
            "not ",
            "without ",
            "does not ",
            "do not ",
            "not a ",
            "not live",
            "no live",
        )
    )


def evaluate_release_evidence_policy(repo_root: Path = REPO_ROOT) -> PolicyFinding:
    """Check governance/release reports are either present or generatable."""
    required_sources = (
        repo_root / "governance" / "controls.py",
        repo_root / "governance" / "audit.py",
        repo_root / "governance" / "attestations.py",
        repo_root / "governance" / "release.py",
    )
    missing = [str(path.relative_to(repo_root)) for path in required_sources if not path.exists()]
    if missing:
        return _critical("POL-REL-001", "Release assurance source is missing.", ", ".join(missing))
    return _pass(
        "POL-REL-001",
        "Release assurance source modules are present and deterministic.",
        "governance/",
    )


def evaluate_policies(repo_root: Path = REPO_ROOT) -> tuple[PolicyFinding, ...]:
    """Evaluate the compact Milestone 8 policy set."""
    return (
        evaluate_secret_hygiene_policy(repo_root),
        evaluate_agent_tool_policy(),
        evaluate_integration_policy(),
        evaluate_synthetic_evidence_policy(repo_root),
        evaluate_claim_discipline_policy(repo_root),
        evaluate_release_evidence_policy(repo_root),
    )


def has_critical_findings(findings: tuple[PolicyFinding, ...]) -> bool:
    """Return whether any policy finding blocks release assurance."""
    return any(finding.severity is PolicySeverity.CRITICAL for finding in findings)


if __name__ == "__main__":  # pragma: no cover
    findings = evaluate_policies()
    print(json.dumps([finding.to_dict() for finding in findings], indent=2))
    raise SystemExit(1 if has_critical_findings(findings) else 0)


__all__ = [
    "PolicyFinding",
    "PolicySeverity",
    "evaluate_agent_tool_policy",
    "evaluate_claim_discipline_policy",
    "evaluate_integration_policy",
    "evaluate_policies",
    "evaluate_release_evidence_policy",
    "evaluate_secret_hygiene_policy",
    "evaluate_synthetic_evidence_policy",
    "has_critical_findings",
]
