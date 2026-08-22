"""Tests for deterministic governance evidence generation."""

import json

from governance.audit import verify_audit_chain
from governance.evidence import build_governance_summary, generate_all


def test_governance_summary_contains_controls_and_policy_results():
    summary = build_governance_summary()
    assert summary["control_count"] >= 10
    assert summary["audit_chain_verified"] is True
    assert all(finding["status"] == "pass" for finding in summary["policy_findings"])
    assert "not a live GRC platform" in summary["note"]


def test_generate_all_writes_deterministic_assurance_evidence(tmp_path):
    first = generate_all(data_dir=tmp_path / "a" / "data", reports_dir=tmp_path / "a" / "reports")
    second = generate_all(data_dir=tmp_path / "b" / "data", reports_dir=tmp_path / "b" / "reports")
    assert set(first) == {
        "audit_evidence.json",
        "access_attestations.json",
        "governance_summary.json",
        "release_assurance.json",
        "operational_readiness.md",
        "final_assurance_report.md",
    }
    for name, path in first.items():
        assert path.is_file()
        assert path.read_text(encoding="utf-8") == second[name].read_text(encoding="utf-8")


def test_generated_audit_evidence_hash_chain_verifies(tmp_path):
    written = generate_all(data_dir=tmp_path / "data", reports_dir=tmp_path / "reports")
    payload = json.loads(written["audit_evidence.json"].read_text(encoding="utf-8"))
    assert verify_audit_chain(tuple(payload))


def test_release_assurance_evidence_uses_bounded_readiness_language(tmp_path):
    written = generate_all(data_dir=tmp_path / "data", reports_dir=tmp_path / "reports")
    payload = json.loads(written["release_assurance.json"].read_text(encoding="utf-8"))
    assert payload["ready"] is True
    assert payload["decision"] == "reference implementation release-assurance checks passed"
    assert (
        "production ready"
        not in written["final_assurance_report.md"].read_text(encoding="utf-8").lower()
    )
