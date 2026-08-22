"""Tests for governance policy evaluation and release assurance."""

from governance.attestations import build_reference_attestations
from governance.controls import CONTROL_CATALOG
from governance.policies import (
    PolicyFinding,
    PolicySeverity,
    evaluate_policies,
    has_critical_findings,
)
from governance.release import QualityGate, build_release_assurance, required_quality_gates


def test_policy_evaluation_passes_current_repository():
    findings = evaluate_policies()
    assert {finding.policy_id for finding in findings} >= {
        "POL-SEC-001",
        "POL-AI-001",
        "POL-INT-001",
        "POL-DATA-001",
        "POL-CLAIM-001",
        "POL-REL-001",
    }
    assert not has_critical_findings(findings)


def test_release_assurance_is_ready_when_gates_and_policies_pass():
    assurance = build_release_assurance(
        controls=CONTROL_CATALOG,
        attestations=build_reference_attestations(),
        policy_findings=evaluate_policies(),
    )
    payload = assurance.to_dict()
    assert assurance.ready is True
    assert assurance.status == "reference_assurance_passed"
    assert payload["decision"] == "reference implementation release-assurance checks passed"


def test_release_assurance_blocks_unresolved_critical_findings():
    critical = PolicyFinding(
        "POL-TEST",
        "fail",
        PolicySeverity.CRITICAL,
        "Synthetic critical finding.",
        "test",
    )
    assurance = build_release_assurance(
        controls=CONTROL_CATALOG,
        attestations=build_reference_attestations(),
        policy_findings=(critical,),
    )
    assert assurance.ready is False
    assert assurance.unresolved_critical_findings == 1


def test_release_assurance_blocks_failed_quality_gate():
    failed_gate = QualityGate("QG-TEST", "pytest", "failed", "synthetic failure")
    assurance = build_release_assurance(
        controls=CONTROL_CATALOG,
        attestations=build_reference_attestations(),
        policy_findings=(),
        quality_gates=(failed_gate,),
    )
    assert assurance.ready is False


def test_required_quality_gates_include_governance_and_evidence_checks():
    gate_ids = {gate.gate_id for gate in required_quality_gates()}
    assert "QG-GOVERNANCE-POLICY" in gate_ids
    assert "QG-EVIDENCE-REPRODUCIBLE" in gate_ids
