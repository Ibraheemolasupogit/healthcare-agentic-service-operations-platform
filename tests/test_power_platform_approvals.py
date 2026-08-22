"""Tests for the human-approval pattern."""

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from power_platform.approvals import (
    ApprovalDecision,
    ApprovalRecord,
    ApprovalValidationError,
    build_example_approvals,
    validate_approval_record,
)


def test_build_example_approvals_returns_one_approved_one_rejected():
    approved, rejected = build_example_approvals()
    assert approved.decision is ApprovalDecision.APPROVED
    assert rejected.decision is ApprovalDecision.REJECTED


def test_build_example_approvals_is_deterministic():
    first = build_example_approvals()
    second = build_example_approvals()
    assert first == second


@pytest.mark.parametrize("index", [0, 1])
def test_every_example_approval_validates(index):
    record = build_example_approvals()[index]
    validate_approval_record(record)  # must not raise


def test_approval_record_carries_every_required_field():
    approved, _ = build_example_approvals()
    assert approved.request.requester
    assert approved.request.approver_role
    assert approved.decision
    assert approved.reason
    assert approved.decided_at
    assert approved.request.correlation_id
    assert approved.audit_event_id


def test_approval_record_to_dict_is_json_serializable():
    approved, _ = build_example_approvals()
    payload = approved.to_dict()
    reloaded = json.loads(json.dumps(payload))
    assert reloaded["decision"] == "Approved"
    assert reloaded["request"]["case_id"] == "SR-AI-1004"


def test_approval_scenario_is_not_a_clinical_treatment_decision():
    approved, rejected = build_example_approvals()
    text = " ".join(
        [approved.request.requested_action, rejected.request.requested_action, approved.reason]
    ).lower()
    for forbidden in ("treatment", "diagnos", "patient"):
        assert forbidden not in text


def test_validate_approval_record_rejects_empty_reason():
    approved, _ = build_example_approvals()
    broken = replace(approved, reason="")
    with pytest.raises(ApprovalValidationError, match="reason"):
        validate_approval_record(broken)


def test_validate_approval_record_rejects_empty_decided_by():
    approved, _ = build_example_approvals()
    broken = replace(approved, decided_by="")
    with pytest.raises(ApprovalValidationError, match="decided_by"):
        validate_approval_record(broken)


def test_validate_approval_record_rejects_empty_audit_event_id():
    approved, _ = build_example_approvals()
    broken = replace(approved, audit_event_id="")
    with pytest.raises(ApprovalValidationError, match="audit_event_id"):
        validate_approval_record(broken)


def test_validate_approval_record_rejects_decided_before_requested():
    approved, _ = build_example_approvals()
    broken = replace(approved, decided_at=approved.request.requested_at - timedelta(minutes=1))
    with pytest.raises(ApprovalValidationError, match="decided_at"):
        validate_approval_record(broken)


def test_validate_approval_record_rejects_missing_requester():
    approved, _ = build_example_approvals()
    broken_request = replace(approved.request, requester="")
    broken = ApprovalRecord(
        request=broken_request,
        decision=approved.decision,
        reason=approved.reason,
        decided_by=approved.decided_by,
        decided_at=approved.decided_at,
        audit_event_id=approved.audit_event_id,
    )
    with pytest.raises(ApprovalValidationError, match="requester"):
        validate_approval_record(broken)


def test_timed_out_is_a_valid_decision_value():
    approved, _ = build_example_approvals()
    timed_out = replace(
        approved,
        decision=ApprovalDecision.TIMED_OUT,
        decided_at=datetime(2026, 1, 12, 15, 0, tzinfo=UTC),
    )
    validate_approval_record(timed_out)  # must not raise
