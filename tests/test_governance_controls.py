"""Tests for governance control catalogue and attestations."""

import pytest

from governance.attestations import (
    AccessAttestation,
    AttestationDecision,
    build_reference_attestations,
    validate_attestations,
)
from governance.controls import CONTROL_CATALOG, ControlDomain, validate_control_catalog


def test_control_catalog_contains_required_domains_and_metadata():
    validate_control_catalog()
    domains = {control.domain for control in CONTROL_CATALOG}
    assert {
        ControlDomain.IDENTITY_ACCESS,
        ControlDomain.AI_AGENT,
        ControlDomain.DATA,
        ControlDomain.INTEGRATION,
        ControlDomain.CHANGE_RELEASE,
        ControlDomain.AUDITABILITY,
        ControlDomain.CLAIM_DISCIPLINE,
    } <= domains
    assert all(control.evidence_source for control in CONTROL_CATALOG)


def test_reference_attestations_are_approved_and_complete():
    attestations = build_reference_attestations()
    validate_attestations(attestations)
    subjects = {attestation.subject for attestation in attestations}
    assert "bounded-agent-tool-registry" in subjects
    assert "integration-service-identities" in subjects
    assert all(attestation.decision is AttestationDecision.APPROVED for attestation in attestations)


def test_attestation_validation_rejects_unresolved_findings():
    attestation = AccessAttestation(
        "ATT-BAD",
        "2026-Q1-reference",
        "bad-subject",
        "role",
        "Reviewer",
        AttestationDecision.APPROVED,
        "Has an unresolved finding.",
        ("permission",),
        "2026-04-01",
        "2026-04-01",
        ("remove stale permission",),
    )
    with pytest.raises(ValueError, match="unresolved findings"):
        validate_attestations((attestation,))
