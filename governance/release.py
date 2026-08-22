"""Release-assurance model for the reference implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.attestations import AccessAttestation
from governance.controls import GovernanceControl
from governance.policies import PolicyFinding, PolicySeverity


@dataclass(frozen=True, slots=True)
class QualityGate:
    """One required release quality gate."""

    gate_id: str
    command: str
    status: str
    evidence: str

    def to_dict(self) -> dict[str, str]:
        return {
            "gate_id": self.gate_id,
            "command": self.command,
            "status": self.status,
            "evidence": self.evidence,
        }


@dataclass(frozen=True, slots=True)
class ReleaseAssurance:
    """Deterministic reference release-readiness result."""

    release_id: str
    status: str
    ready: bool
    quality_gates: tuple[QualityGate, ...]
    policy_findings: tuple[PolicyFinding, ...]
    controls: tuple[GovernanceControl, ...]
    attestations: tuple[AccessAttestation, ...]
    unresolved_critical_findings: int
    decision: str
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "release_id": self.release_id,
            "status": self.status,
            "ready": self.ready,
            "quality_gates": [gate.to_dict() for gate in self.quality_gates],
            "policy_findings": [finding.to_dict() for finding in self.policy_findings],
            "control_count": len(self.controls),
            "controls_by_domain": _controls_by_domain(self.controls),
            "attestations": [attestation.to_dict() for attestation in self.attestations],
            "unresolved_critical_findings": self.unresolved_critical_findings,
            "decision": self.decision,
            "limitations": list(self.limitations),
            "synthetic": True,
            "provenance": "governance.release.build_release_assurance",
        }


def required_quality_gates(status: str = "passed_reference") -> tuple[QualityGate, ...]:
    """Return the repository's required release gates."""
    return (
        QualityGate("QG-RUFF-CHECK", "python3 -m ruff check .", status, "local/CI command"),
        QualityGate(
            "QG-RUFF-FORMAT", "python3 -m ruff format --check .", status, "local/CI command"
        ),
        QualityGate(
            "QG-MYPY",
            "python3 -m mypy business_process dynamics365 salesforce integrations "
            "power_platform ai copilot analytics governance",
            status,
            "local/CI command",
        ),
        QualityGate("QG-PYTEST-COV", "python3 -m pytest --cov", status, "local/CI command"),
        QualityGate(
            "QG-GOVERNANCE-POLICY",
            "python3 -m governance.policies",
            status,
            "local/CI command",
        ),
        QualityGate(
            "QG-EVIDENCE-REPRODUCIBLE",
            "python3 -m governance.evidence",
            status,
            "deterministic generated evidence",
        ),
    )


def build_release_assurance(
    *,
    controls: tuple[GovernanceControl, ...],
    attestations: tuple[AccessAttestation, ...],
    policy_findings: tuple[PolicyFinding, ...],
    quality_gates: tuple[QualityGate, ...] | None = None,
) -> ReleaseAssurance:
    """Calculate bounded reference release assurance."""
    gates = quality_gates or required_quality_gates()
    unresolved = sum(
        1 for finding in policy_findings if finding.severity is PolicySeverity.CRITICAL
    )
    failed_gates = sum(1 for gate in gates if not gate.status.startswith("passed"))
    unresolved_attestations = sum(
        1 for attestation in attestations if attestation.unresolved_findings
    )
    ready = unresolved == 0 and failed_gates == 0 and unresolved_attestations == 0
    return ReleaseAssurance(
        release_id="REL-M8-REFERENCE",
        status="reference_assurance_passed" if ready else "blocked",
        ready=ready,
        quality_gates=gates,
        policy_findings=policy_findings,
        controls=controls,
        attestations=attestations,
        unresolved_critical_findings=unresolved,
        decision="reference implementation release-assurance checks passed"
        if ready
        else "reference implementation release assurance blocked",
        limitations=(
            "No live tenant deployment.",
            "No production IAM, SIEM, secrets manager, or immutable enterprise audit store.",
            "No regulatory certification or production support commitment is claimed.",
        ),
    )


def _controls_by_domain(controls: tuple[GovernanceControl, ...]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for control in controls:
        domain = control.domain.value
        counts[domain] = counts.get(domain, 0) + 1
    return dict(sorted(counts.items()))


__all__ = ["QualityGate", "ReleaseAssurance", "build_release_assurance", "required_quality_gates"]
