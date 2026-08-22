"""Reference access-review and attestation models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from ai.tools import TOOL_REGISTRY, ToolRisk


class AttestationDecision(StrEnum):
    """Reference attestation decision."""

    APPROVED = "approved_reference"
    APPROVED_WITH_FINDINGS = "approved_with_findings"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class AccessAttestation:
    """One synthetic access-review attestation."""

    attestation_id: str
    review_period: str
    subject: str
    subject_type: str
    reviewer_role: str
    decision: AttestationDecision
    rationale: str
    reviewed_permissions: tuple[str, ...]
    expires_on: str
    next_review_due: str
    unresolved_findings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "attestation_id": self.attestation_id,
            "review_period": self.review_period,
            "subject": self.subject,
            "subject_type": self.subject_type,
            "reviewer_role": self.reviewer_role,
            "decision": self.decision.value,
            "rationale": self.rationale,
            "reviewed_permissions": list(self.reviewed_permissions),
            "expires_on": self.expires_on,
            "next_review_due": self.next_review_due,
            "unresolved_findings": list(self.unresolved_findings),
            "synthetic": True,
            "provenance": "governance.attestations.build_reference_attestations",
        }


def build_reference_attestations() -> tuple[AccessAttestation, ...]:
    """Build deterministic reference attestations for privileged permissions."""
    state_changing_tools = tuple(
        tool.name
        for tool in TOOL_REGISTRY
        if tool.risk in {ToolRisk.STATE_CHANGING, ToolRisk.CONSEQUENTIAL}
    )
    return (
        AccessAttestation(
            "ATT-SERVICE-ROLES-Q1",
            "2026-Q1-reference",
            "privileged-service-roles",
            "role_group",
            "Governance reviewer",
            AttestationDecision.APPROVED,
            "Reference service roles are documented and scoped to synthetic operations.",
            (
                "operations-manager",
                "service-agent",
                "approval-manager",
                "integration-service",
            ),
            "2026-04-01",
            "2026-04-01",
            (),
        ),
        AccessAttestation(
            "ATT-AGENT-TOOLS-Q1",
            "2026-Q1-reference",
            "bounded-agent-tool-registry",
            "agent_permission_set",
            "AI governance owner",
            AttestationDecision.APPROVED,
            "State-changing and consequential tools are explicitly approval-gated.",
            state_changing_tools,
            "2026-04-01",
            "2026-04-01",
            (),
        ),
        AccessAttestation(
            "ATT-INTEGRATION-IDENTITIES-Q1",
            "2026-Q1-reference",
            "integration-service-identities",
            "service_identity_set",
            "Integration owner",
            AttestationDecision.APPROVED,
            "Reference identities require source binding, audience, environment, and scope.",
            (
                "audience:healthcare-service-operations-integrations",
                "scope:integration:deliver",
                "environments:dev/test/prod",
            ),
            "2026-04-01",
            "2026-04-01",
            (),
        ),
        AccessAttestation(
            "ATT-APPROVAL-ROLES-Q1",
            "2026-Q1-reference",
            "approval-roles",
            "approval_role_set",
            "Service operations owner",
            AttestationDecision.APPROVED,
            "Consequential non-clinical approval roles are explicit in Power Platform evidence.",
            ("access-approval-manager", "operations-approval-manager"),
            "2026-04-01",
            "2026-04-01",
            (),
        ),
    )


def validate_attestations(attestations: tuple[AccessAttestation, ...]) -> None:
    """Raise if attestations are incomplete or contain unresolved findings."""
    ids = [attestation.attestation_id for attestation in attestations]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate attestation_id")
    for attestation in attestations:
        if not attestation.reviewed_permissions:
            raise ValueError(f"{attestation.attestation_id}: no reviewed permissions")
        if attestation.decision is not AttestationDecision.APPROVED:
            raise ValueError(f"{attestation.attestation_id}: not approved")
        if attestation.unresolved_findings:
            raise ValueError(f"{attestation.attestation_id}: unresolved findings")


__all__ = [
    "AccessAttestation",
    "AttestationDecision",
    "build_reference_attestations",
    "validate_attestations",
]
