"""Bronze ingestion over existing deterministic repository evidence."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = REPO_ROOT / "data" / "synthetic"
DEFAULT_REPORTS_DIR = REPO_ROOT / "reports"


@dataclass(frozen=True, slots=True)
class BronzeModel:
    """Raw/source-aligned records loaded from existing evidence."""

    cases: tuple[dict[str, Any], ...]
    case_events: tuple[dict[str, Any], ...]
    dynamics_examples: tuple[dict[str, Any], ...]
    salesforce_examples: tuple[dict[str, Any], ...]
    automation_traces: tuple[dict[str, Any], ...]
    approval_records: tuple[dict[str, Any], ...]
    agent_tool_traces: tuple[dict[str, Any], ...]
    copilot_conversations: tuple[dict[str, Any], ...]
    ai_evaluation_cases: tuple[dict[str, Any], ...]
    ai_evaluation_summary: dict[str, Any]


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_bronze_model(
    *, data_dir: Path = DEFAULT_DATA_DIR, reports_dir: Path = DEFAULT_REPORTS_DIR
) -> BronzeModel:
    """Load Bronze data from generated synthetic evidence files."""
    cases = tuple(_read_json(data_dir / "cases.json"))
    case_events: list[dict[str, Any]] = []
    for case in cases:
        for index, event in enumerate(case["history"]):
            case_events.append({"case_id": case["case_id"], "event_index": index, **event})

    return BronzeModel(
        cases=cases,
        case_events=tuple(case_events),
        dynamics_examples=tuple(_read_json(data_dir / "dynamics365_examples.json")),
        salesforce_examples=tuple(_read_json(data_dir / "salesforce_examples.json")),
        automation_traces=(_read_json(data_dir / "power_platform_execution_trace.json"),),
        approval_records=tuple(_read_json(data_dir / "power_platform_approval_examples.json")),
        agent_tool_traces=tuple(_read_json(data_dir / "agent_tool_traces.json")),
        copilot_conversations=tuple(_read_json(data_dir / "copilot_conversations.json")),
        ai_evaluation_cases=tuple(_read_json(data_dir / "ai_evaluation_cases.json")),
        ai_evaluation_summary=_read_json(reports_dir / "agentic_ai_evaluation_summary.json"),
    )


__all__ = ["BronzeModel", "load_bronze_model"]
