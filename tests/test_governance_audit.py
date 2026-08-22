"""Tests for audit evidence tamper-evidence concepts."""

from dataclasses import replace
from datetime import UTC, datetime

from governance.audit import (
    AuditEvidence,
    build_reference_audit_evidence,
    chain_audit_evidence,
    verify_audit_chain,
)


def test_audit_evidence_chain_verifies():
    events = build_reference_audit_evidence()
    assert verify_audit_chain(tuple(event.to_dict() for event in events))
    assert events[0].previous_hash is None
    assert events[1].previous_hash == events[0].evidence_hash


def test_audit_evidence_chain_detects_tampering():
    events = tuple(event.to_dict() for event in build_reference_audit_evidence())
    tampered = ({**events[0], "outcome": "tampered"}, *events[1:])
    assert not verify_audit_chain(tampered)


def test_chained_hash_changes_when_event_content_changes():
    now = datetime(2026, 1, 12, 15, 0, tzinfo=UTC)
    base = AuditEvidence(
        "AUD-TEST",
        "policy_evaluation",
        "tester",
        "system",
        now,
        "corr",
        "governance.tests",
        "evaluate",
        "passed",
        "synthetic test",
    )
    changed = replace(base, outcome="failed")
    assert (
        chain_audit_evidence((base,))[0].evidence_hash
        != chain_audit_evidence((changed,))[0].evidence_hash
    )
