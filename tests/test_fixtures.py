"""Tests for the deterministic synthetic case fixtures."""

import re

from business_process import CaseStage, ServiceCategory
from business_process.fixtures import build_synthetic_cases

# Guards against accidentally-realistic identifiers or clinical content: a
# 10-digit NHS number, a named patient, or diagnosis/treatment language,
# which would violate the synthetic-data-only and no-clinical-content
# constraints for this portfolio project. "no patient data" / "non-patient"
# style disclaimers are legitimate and intentionally not flagged.
_NHS_NUMBER_PATTERN = re.compile(r"\b\d{10}\b")
_FORBIDDEN_PATTERNS = (
    re.compile(r"\bpatient name\b"),
    re.compile(r"\bdate of birth\b"),
    re.compile(r"\bdiagnos"),
    re.compile(r"\bnhs number\b"),
    re.compile(r"\btreatment plan\b"),
)


def test_build_synthetic_cases_covers_every_service_category_exactly_once():
    cases = build_synthetic_cases()
    categories = [case.category for case in cases]
    assert sorted(categories, key=str) == sorted(ServiceCategory, key=str)


def test_build_synthetic_cases_is_deterministic():
    first = build_synthetic_cases()
    second = build_synthetic_cases()
    assert [c.case_id for c in first] == [c.case_id for c in second]
    assert [c.stage for c in first] == [c.stage for c in second]
    assert [len(c.history) for c in first] == [len(c.history) for c in second]


def test_case_ids_are_unique():
    cases = build_synthetic_cases()
    ids = [case.case_id for case in cases]
    assert len(ids) == len(set(ids))


def test_fixtures_demonstrate_varied_lifecycle_states():
    cases = build_synthetic_cases()
    stages = {case.stage for case in cases}
    assert CaseStage.CLOSED in stages
    assert CaseStage.ESCALATED in stages
    assert CaseStage.PENDING in stages
    assert len(stages) > 1


def test_fixtures_contain_no_patient_identifiable_or_clinical_content():
    cases = build_synthetic_cases()
    for case in cases:
        text = " ".join([case.title, case.description] + [e.detail for e in case.history])
        assert not _NHS_NUMBER_PATTERN.search(text), case.case_id
        lowered = text.lower()
        for pattern in _FORBIDDEN_PATTERNS:
            assert not pattern.search(lowered), (
                f"{case.case_id} contains forbidden term {pattern.pattern!r}"
            )


def test_routed_or_later_cases_have_a_queue_and_owner():
    non_submitted_stages = {
        CaseStage.CLASSIFIED,
        CaseStage.ROUTED,
        CaseStage.IN_PROGRESS,
        CaseStage.PENDING,
        CaseStage.ESCALATED,
        CaseStage.RESOLVED,
        CaseStage.CLOSED,
    }
    for case in build_synthetic_cases():
        if case.stage in non_submitted_stages:
            assert case.queue is not None
            assert case.owner is not None
