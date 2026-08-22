"""Reference governance control catalogue for Milestone 8."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class ControlDomain(StrEnum):
    """Governance domains covered by the reference control catalogue."""

    IDENTITY_ACCESS = "identity_and_access"
    AI_AGENT = "ai_agent_governance"
    DATA = "data_governance"
    INTEGRATION = "integration_governance"
    CHANGE_RELEASE = "change_release"
    OBSERVABILITY = "observability"
    HUMAN_APPROVAL = "human_approval"
    SECRETS_CONFIGURATION = "secrets_configuration"
    AUDITABILITY = "auditability"
    RESILIENCE = "resilience"
    CLAIM_DISCIPLINE = "synthetic_data_portfolio_claims"


class ControlStatus(StrEnum):
    """Reference implementation control status."""

    IMPLEMENTED_REFERENCE = "implemented_reference"
    DOCUMENTED_REFERENCE = "documented_reference"
    FUTURE_LIVE_CONTROL = "future_live_control"


@dataclass(frozen=True, slots=True)
class GovernanceControl:
    """One release-assurance control definition."""

    control_id: str
    objective: str
    domain: ControlDomain
    applicability: str
    evidence_source: str
    status: ControlStatus
    owner_role: str
    review_frequency: str
    requires_attestation: bool
    exception_handling: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "control_id": self.control_id,
            "objective": self.objective,
            "domain": self.domain.value,
            "applicability": self.applicability,
            "evidence_source": self.evidence_source,
            "status": self.status.value,
            "owner_role": self.owner_role,
            "review_frequency": self.review_frequency,
            "requires_attestation": self.requires_attestation,
            "exception_handling": self.exception_handling,
        }


CONTROL_CATALOG: tuple[GovernanceControl, ...] = (
    GovernanceControl(
        "GOV-IA-001",
        "Privileged service, agent, integration, and approval roles are reviewable.",
        ControlDomain.IDENTITY_ACCESS,
        "Reference roles and permissions in AI, integration, and approval contexts.",
        "data/synthetic/access_attestations.json",
        ControlStatus.IMPLEMENTED_REFERENCE,
        "Governance reviewer",
        "Quarterly in a live implementation; per release in this repository.",
        True,
        "Unresolved access findings block reference release assurance.",
    ),
    GovernanceControl(
        "GOV-AI-001",
        "Bounded agents cannot acquire unrestricted or unapproved state-changing tools.",
        ControlDomain.AI_AGENT,
        "ai.tools and ai.agents",
        "governance.policies.evaluate_agent_tool_policy",
        ControlStatus.IMPLEMENTED_REFERENCE,
        "AI governance owner",
        "Per release and whenever prompts/tools change.",
        True,
        "Remove or gate the tool before release evidence can pass.",
    ),
    GovernanceControl(
        "GOV-DATA-001",
        "Repository evidence is synthetic and labelled as reference evidence.",
        ControlDomain.DATA,
        "data/synthetic and reports",
        "governance.policies.evaluate_synthetic_evidence_policy",
        ControlStatus.IMPLEMENTED_REFERENCE,
        "Data governance owner",
        "Per release.",
        False,
        "Relabel evidence or remove unverified data before release.",
    ),
    GovernanceControl(
        "GOV-INT-001",
        "Integration delivery uses schema, auth, idempotency, retry, "
        "dead-letter, and reconciliation controls.",
        ControlDomain.INTEGRATION,
        "integrations package and Milestone 7 evidence",
        "reports/integration_operations_summary.json",
        ControlStatus.IMPLEMENTED_REFERENCE,
        "Integration owner",
        "Per release and before any live connector work.",
        True,
        "Block live transport design until the missing control is remediated.",
    ),
    GovernanceControl(
        "GOV-REL-001",
        "Release readiness requires passing quality gates, policy checks, and evidence checks.",
        ControlDomain.CHANGE_RELEASE,
        "CI workflow, pyproject, tests, and governance evidence",
        "reports/release_assurance.json",
        ControlStatus.IMPLEMENTED_REFERENCE,
        "Release owner",
        "Per release candidate.",
        True,
        "Any critical finding blocks reference release assurance.",
    ),
    GovernanceControl(
        "GOV-OBS-001",
        "Automation, AI, analytics, and integration evidence preserve provenance "
        "and observability.",
        ControlDomain.OBSERVABILITY,
        "reports/*.json and data/synthetic/*.json",
        "reports/governance_summary.json",
        ControlStatus.IMPLEMENTED_REFERENCE,
        "Operations owner",
        "Per release.",
        False,
        "Regenerate or fix missing provenance before release evidence can pass.",
    ),
    GovernanceControl(
        "GOV-HITL-001",
        "Consequential and state-changing actions require human approval gates.",
        ControlDomain.HUMAN_APPROVAL,
        "ai.tools and power_platform.approvals",
        "data/synthetic/access_attestations.json",
        ControlStatus.IMPLEMENTED_REFERENCE,
        "Service operations owner",
        "Per release and whenever action risk changes.",
        True,
        "Disable the action or add approval evidence before release.",
    ),
    GovernanceControl(
        "GOV-SEC-001",
        "Tracked files must not contain live credentials, secret files, or production endpoints.",
        ControlDomain.SECRETS_CONFIGURATION,
        "repository policy scan",
        "governance.policies.evaluate_secret_hygiene_policy",
        ControlStatus.IMPLEMENTED_REFERENCE,
        "Security reviewer",
        "Per release and every CI run.",
        False,
        "Remove secret material and rotate externally if live data was exposed.",
    ),
    GovernanceControl(
        "GOV-AUD-001",
        "Audit evidence has stable identifiers, provenance, correlation, and "
        "tamper-evidence digests.",
        ControlDomain.AUDITABILITY,
        "governance.audit",
        "data/synthetic/audit_evidence.json",
        ControlStatus.IMPLEMENTED_REFERENCE,
        "Audit reviewer",
        "Per release.",
        False,
        "Regenerate evidence and investigate any digest-chain mismatch.",
    ),
    GovernanceControl(
        "GOV-RES-001",
        "Retry, dead-letter, reconciliation, and manual-review controls are "
        "visible before release.",
        ControlDomain.RESILIENCE,
        "integrations and reports/reconciliation_report.md",
        "reports/operational_readiness.md",
        ControlStatus.IMPLEMENTED_REFERENCE,
        "Operations owner",
        "Per release.",
        True,
        "Unresolved dead-letter/reconciliation gaps block live integration work.",
    ),
    GovernanceControl(
        "GOV-CLAIM-001",
        "Portfolio claims distinguish reference implementation from live deployment or compliance.",
        ControlDomain.CLAIM_DISCIPLINE,
        "README and docs",
        "governance.policies.evaluate_claim_discipline_policy",
        ControlStatus.IMPLEMENTED_REFERENCE,
        "Portfolio owner",
        "Per release.",
        False,
        "Rewrite claim before publishing portfolio evidence.",
    ),
)


def validate_control_catalog(controls: tuple[GovernanceControl, ...] = CONTROL_CATALOG) -> None:
    """Raise if required control catalogue metadata is incomplete."""
    ids = [control.control_id for control in controls]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate control_id")
    for control in controls:
        if not control.control_id.startswith("GOV-"):
            raise ValueError(f"{control.control_id}: invalid control id")
        if not control.objective or not control.evidence_source or not control.owner_role:
            raise ValueError(f"{control.control_id}: missing required metadata")
        if control.status is ControlStatus.FUTURE_LIVE_CONTROL and control.requires_attestation:
            raise ValueError(
                f"{control.control_id}: future-only controls cannot require release attestation"
            )


__all__ = [
    "CONTROL_CATALOG",
    "ControlDomain",
    "ControlStatus",
    "GovernanceControl",
    "validate_control_catalog",
]
