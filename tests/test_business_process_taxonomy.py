"""Tests for the platform-neutral service taxonomy and case lifecycle types."""

from business_process import CASE_LIFECYCLE_ORDER, CaseStage, ServiceCategory


def test_service_category_has_six_synthetic_categories():
    assert len(ServiceCategory) == 6
    assert {member.value for member in ServiceCategory} == {
        "Digital Support",
        "Clinical Equipment",
        "Facilities",
        "Access and Identity",
        "Application Support",
        "Data and Reporting",
    }


def test_case_stage_has_eight_lifecycle_stages():
    assert len(CaseStage) == 8


def test_case_lifecycle_order_matches_conceptual_lifecycle():
    assert CASE_LIFECYCLE_ORDER == (
        CaseStage.SUBMITTED,
        CaseStage.CLASSIFIED,
        CaseStage.ROUTED,
        CaseStage.IN_PROGRESS,
        CaseStage.PENDING,
        CaseStage.ESCALATED,
        CaseStage.RESOLVED,
        CaseStage.CLOSED,
    )


def test_case_lifecycle_order_contains_every_stage_exactly_once():
    assert set(CASE_LIFECYCLE_ORDER) == set(CaseStage)
    assert len(CASE_LIFECYCLE_ORDER) == len(CaseStage)


def test_service_category_and_case_stage_are_string_enums():
    assert ServiceCategory.DIGITAL_SUPPORT == "Digital Support"
    assert CaseStage.SUBMITTED == "Submitted"
