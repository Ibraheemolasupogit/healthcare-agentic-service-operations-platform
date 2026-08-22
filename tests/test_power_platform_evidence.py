"""Tests for deterministic Power Platform automation evidence generation.

Writes into pytest tmp_path directories, never into the repository's real
power_platform/power_automate, power_platform/connectors, data/, or
reports/ directories.
"""

import json

from power_platform.evidence import (
    build_automation_summary,
    build_connector_operations_payload,
    build_execution_trace_example,
    build_flow_spec_files,
    generate_all,
)
from power_platform.flows import ALL_FLOWS


def test_build_flow_spec_files_covers_every_flow():
    files = build_flow_spec_files()
    assert len(files) == len(ALL_FLOWS)
    for flow in ALL_FLOWS:
        assert f"{flow.flow_id}.flow.json" in files
        json.dumps(files[f"{flow.flow_id}.flow.json"])  # must not raise


def test_build_connector_operations_payload_is_json_safe_and_complete():
    payload = build_connector_operations_payload()
    json.dumps(payload)
    assert len(payload) == 9


def test_build_execution_trace_example_is_clearly_labelled_as_simulation():
    trace = build_execution_trace_example()
    assert trace["trace_type"] == "simulated_reference_example"
    assert "not a live power platform run history" in trace["note"].lower()
    assert len(trace["steps"]) > 0
    assert all(step["status"] == "simulated_success" for step in trace["steps"])


def test_build_execution_trace_example_is_deterministic():
    assert build_execution_trace_example() == build_execution_trace_example()


def test_build_automation_summary_counts_match_actual_flow_and_step_counts():
    summary = build_automation_summary()
    total_steps = sum(len(flow.steps) for flow in ALL_FLOWS)
    assert summary["flows"]["count"] == len(ALL_FLOWS)
    assert summary["flows"]["total_steps"] == total_steps
    assert sum(summary["flows"]["steps_by_kind"].values()) == total_steps
    assert summary["connector_operations"]["count"] == 9
    assert summary["approval_examples"]["count"] == 2


def test_build_automation_summary_notes_no_live_environment():
    summary = build_automation_summary()
    assert "no live power platform environment" in summary["note"].lower()


def test_generate_all_writes_expected_files(tmp_path):
    written = generate_all(
        power_automate_dir=tmp_path / "power_automate",
        connectors_dir=tmp_path / "connectors",
        data_dir=tmp_path / "data",
        reports_dir=tmp_path / "reports",
    )
    expected_names = {f"{flow.flow_id}.flow.json" for flow in ALL_FLOWS} | {
        "operations.json",
        "power_platform_approval_examples.json",
        "power_platform_execution_trace.json",
        "automation_summary.json",
    }
    assert set(written.keys()) == expected_names
    for path in written.values():
        assert path.is_file()
        json.loads(path.read_text(encoding="utf-8"))  # must be valid JSON


def test_generate_all_is_deterministic(tmp_path):
    first = generate_all(
        power_automate_dir=tmp_path / "a" / "power_automate",
        connectors_dir=tmp_path / "a" / "connectors",
        data_dir=tmp_path / "a" / "data",
        reports_dir=tmp_path / "a" / "reports",
    )
    second = generate_all(
        power_automate_dir=tmp_path / "b" / "power_automate",
        connectors_dir=tmp_path / "b" / "connectors",
        data_dir=tmp_path / "b" / "data",
        reports_dir=tmp_path / "b" / "reports",
    )
    for name in first:
        assert first[name].read_text(encoding="utf-8") == second[name].read_text(encoding="utf-8")
