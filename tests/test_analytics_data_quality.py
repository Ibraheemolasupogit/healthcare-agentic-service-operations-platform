"""Tests for analytical data-quality rules."""

from dataclasses import replace

from analytics.fabric.data_quality import run_data_quality_checks
from analytics.fabric.ingestion import load_bronze_model
from analytics.fabric.silver import build_silver_model


def test_data_quality_passes_current_generated_evidence():
    issues = run_data_quality_checks(build_silver_model(load_bronze_model()))
    assert issues == ()


def test_data_quality_detects_duplicate_case_ids():
    silver = build_silver_model(load_bronze_model())
    duplicate = replace(silver, service_cases=(*silver.service_cases, silver.service_cases[0]))
    issues = run_data_quality_checks(duplicate)
    assert any(issue.check_id == "duplicate-case-id" for issue in issues)


def test_data_quality_detects_unknown_case_event_reference():
    silver = build_silver_model(load_bronze_model())
    bad_event = {**silver.lifecycle_events[0], "case_id": "SR-UNKNOWN"}
    broken = replace(silver, lifecycle_events=(bad_event, *silver.lifecycle_events[1:]))
    issues = run_data_quality_checks(broken)
    assert any(issue.check_id == "event-case-integrity" for issue in issues)


def test_data_quality_detects_missing_correlation_id():
    silver = build_silver_model(load_bronze_model())
    bad_execution = {**silver.automation_executions[0], "correlation_id": ""}
    broken = replace(silver, automation_executions=(bad_execution,))
    issues = run_data_quality_checks(broken)
    assert any(issue.check_id == "automation-correlation" for issue in issues)


def test_data_quality_detects_negative_duration():
    silver = build_silver_model(load_bronze_model())
    bad_case = {**silver.service_cases[0], "resolution_minutes": -1}
    broken = replace(silver, service_cases=(bad_case, *silver.service_cases[1:]))
    issues = run_data_quality_checks(broken)
    assert any(issue.check_id == "non-negative-duration" for issue in issues)
