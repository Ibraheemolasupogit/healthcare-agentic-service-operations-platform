"""Tests for deterministic analytics evidence generation."""

import csv
import json

from analytics.fabric.evidence import (
    build_analytics_summary,
    build_service_operations_report,
    generate_all,
)


def test_analytics_summary_contains_kpis_and_lineage():
    summary = build_analytics_summary()
    assert summary["case_metrics"]["total_cases"] == 6
    assert summary["sla_summary"]["sla_compliance_rate_percent"] == 83.33
    assert summary["automation_metrics"]["automation_execution_count"] == 1
    assert summary["copilot_usage"]["agent_tool_invocation_count"] == 2
    assert summary["data_quality"]["issue_count"] == 0
    assert "Gold KPI outputs" in summary["lineage"]
    assert "no live Fabric workspace" in summary["note"]


def test_service_operations_report_is_concise_and_claim_disciplined():
    report = build_service_operations_report()
    assert "# Service Operations Analytics Report" in report
    assert "No production baseline exists" in report
    assert "improved SLA" not in report
    assert "not production telemetry" in report


def test_generate_all_writes_expected_files(tmp_path):
    written = generate_all(outputs_dir=tmp_path / "outputs", reports_dir=tmp_path / "reports")
    assert set(written) == {
        "analytics_summary.json",
        "service_operations_report.md",
        "case_metrics.csv",
        "sla_summary.csv",
        "automation_metrics.csv",
        "copilot_usage.csv",
    }
    for path in written.values():
        assert path.is_file()


def test_generate_all_is_deterministic(tmp_path):
    first = generate_all(outputs_dir=tmp_path / "a" / "outputs", reports_dir=tmp_path / "a")
    second = generate_all(outputs_dir=tmp_path / "b" / "outputs", reports_dir=tmp_path / "b")
    assert set(first) == set(second)
    for name in first:
        assert first[name].read_text(encoding="utf-8") == second[name].read_text(encoding="utf-8")


def test_generated_csv_files_are_readable(tmp_path):
    written = generate_all(outputs_dir=tmp_path / "outputs", reports_dir=tmp_path / "reports")
    for name in (
        "case_metrics.csv",
        "sla_summary.csv",
        "automation_metrics.csv",
        "copilot_usage.csv",
    ):
        with written[name].open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert rows


def test_generated_json_summary_is_json_safe(tmp_path):
    written = generate_all(outputs_dir=tmp_path / "outputs", reports_dir=tmp_path / "reports")
    payload = json.loads(written["analytics_summary.json"].read_text(encoding="utf-8"))
    assert payload["generated_from"] == "analytics.fabric.evidence (deterministic, synthetic)"
