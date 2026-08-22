"""Tests for deterministic portfolio evidence generation.

Writes into a pytest tmp_path, never into the repository's real data/ or
reports/ directories, so running the test suite has no side effects on
tracked evidence files.
"""

import json

from business_process import ServiceCategory
from business_process.evidence import (
    build_case_fixtures_payload,
    build_routing_config,
    build_sla_config,
    build_summary_report,
    build_taxonomy_config,
    generate_all,
)


def test_build_taxonomy_config_lists_six_categories_and_eight_stages():
    config = build_taxonomy_config()
    assert len(config["service_categories"]) == 6
    assert len(config["case_lifecycle"]) == 8
    assert len(config["priorities"]) == 4


def test_build_routing_config_covers_every_category_and_queue():
    config = build_routing_config()
    assert len(config["routing_rules"]) == 6
    assert len(config["queue_owners"]) == 6


def test_build_sla_config_covers_every_category_priority_combination():
    config = build_sla_config()
    assert len(config) == 6
    for category_config in config.values():
        assert len(category_config) == 4
        for target in category_config.values():
            assert target["response_minutes"] > 0
            assert target["resolution_minutes"] > 0


def test_build_case_fixtures_payload_is_json_safe_and_covers_all_categories():
    payload = build_case_fixtures_payload()
    json.dumps(payload)  # must not raise
    categories = {case["category"] for case in payload}
    assert categories == {category.value for category in ServiceCategory}


def test_build_summary_report_counts_match_fixture_count():
    report = build_summary_report()
    assert report["total_cases"] == sum(report["cases_by_stage"].values())
    assert report["total_cases"] == sum(report["cases_by_category"].values())


def test_generate_all_writes_expected_files(tmp_path):
    data_dir = tmp_path / "data"
    reports_dir = tmp_path / "reports"

    written = generate_all(data_dir=data_dir, reports_dir=reports_dir)

    assert set(written.keys()) == {
        "service_taxonomy.json",
        "routing_config.json",
        "sla_config.json",
        "cases.json",
        "case_summary.json",
    }
    for path in written.values():
        assert path.is_file()
        json.loads(path.read_text(encoding="utf-8"))  # must be valid JSON

    assert (data_dir / "cases.json").exists()
    assert (reports_dir / "case_summary.json").exists()


def test_generate_all_is_deterministic(tmp_path):
    first = generate_all(data_dir=tmp_path / "a", reports_dir=tmp_path / "a-reports")
    second = generate_all(data_dir=tmp_path / "b", reports_dir=tmp_path / "b-reports")
    for name in first:
        assert first[name].read_text(encoding="utf-8") == second[name].read_text(encoding="utf-8")
