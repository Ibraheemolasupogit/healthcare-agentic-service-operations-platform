"""Deterministic portfolio evidence generation for the business process domain.

Running `generate_all()` (or `python -m business_process.evidence`) writes
small, deterministic JSON artefacts demonstrating the canonical service
operations model: service taxonomy/queue configuration, SLA configuration,
routing configuration, synthetic case fixtures, and a generated summary
report. All output is derived from fixed, in-repo data — nothing is fetched
from a live system, and none of it implies a production deployment.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from business_process.fixtures import build_synthetic_cases
from business_process.priority import PRIORITY_ORDER
from business_process.queues import DEFAULT_QUEUE_OWNERS, ROUTING_RULES
from business_process.serialization import case_to_dict
from business_process.sla import get_sla_target
from business_process.taxonomy import CASE_LIFECYCLE_ORDER, ServiceCategory

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = REPO_ROOT / "data" / "synthetic"
DEFAULT_REPORTS_DIR = REPO_ROOT / "reports"


def build_taxonomy_config() -> dict[str, Any]:
    """Service categories, case lifecycle, and priorities as plain config."""
    return {
        "service_categories": [category.value for category in ServiceCategory],
        "case_lifecycle": [stage.value for stage in CASE_LIFECYCLE_ORDER],
        "priorities": [priority.value for priority in PRIORITY_ORDER],
    }


def build_routing_config() -> dict[str, Any]:
    """Category -> queue routing rules and default queue owners."""
    return {
        "routing_rules": {category.value: queue.value for category, queue in ROUTING_RULES.items()},
        "queue_owners": {queue.value: owner for queue, owner in DEFAULT_QUEUE_OWNERS.items()},
    }


def build_sla_config() -> dict[str, Any]:
    """Full SLA target matrix, keyed by category then priority."""
    config: dict[str, Any] = {}
    for category in ServiceCategory:
        config[category.value] = {}
        for priority in PRIORITY_ORDER:
            target = get_sla_target(category, priority)
            config[category.value][priority.value] = {
                "response_minutes": target.response_minutes,
                "resolution_minutes": target.resolution_minutes,
            }
    return config


def build_case_fixtures_payload() -> list[dict[str, Any]]:
    """Serialize the deterministic synthetic case fixtures."""
    return [case_to_dict(case) for case in build_synthetic_cases()]


def build_summary_report() -> dict[str, Any]:
    """A small generated summary over the synthetic case fixtures."""
    cases = build_synthetic_cases()
    by_stage: dict[str, int] = {}
    by_category: dict[str, int] = {}
    for case in cases:
        by_stage[case.stage.value] = by_stage.get(case.stage.value, 0) + 1
        by_category[case.category.value] = by_category.get(case.category.value, 0) + 1
    return {
        "generated_from": "business_process.fixtures.build_synthetic_cases",
        "total_cases": len(cases),
        "cases_by_stage": by_stage,
        "cases_by_category": by_category,
        "note": "Synthetic portfolio evidence only. See README Portfolio & Simulation Disclaimer.",
    }


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def generate_all(
    *, data_dir: Path = DEFAULT_DATA_DIR, reports_dir: Path = DEFAULT_REPORTS_DIR
) -> dict[str, Path]:
    """Generate all Milestone 2 evidence artefacts and return their paths, by filename."""
    outputs: dict[Path, Any] = {
        data_dir / "service_taxonomy.json": build_taxonomy_config(),
        data_dir / "routing_config.json": build_routing_config(),
        data_dir / "sla_config.json": build_sla_config(),
        data_dir / "cases.json": build_case_fixtures_payload(),
        reports_dir / "case_summary.json": build_summary_report(),
    }
    for path, payload in outputs.items():
        _write_json(path, payload)
    return {path.name: path for path in outputs}


if __name__ == "__main__":  # pragma: no cover
    for name, path in generate_all().items():
        print(f"wrote {name} -> {path}")
