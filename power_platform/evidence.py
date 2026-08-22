"""Deterministic portfolio evidence generation for Power Platform automation.

Writes the version-controlled flow specifications, the connector contract,
approval examples, a simulated execution trace, and a generated summary
report. Everything here is derived from fixed, in-repo data — nothing is
fetched from a live Power Platform environment, and no run history is
fabricated. Every execution-trace artefact is explicitly labelled as a
simulation. See power_platform/README.md.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from power_platform.approvals import build_example_approvals
from power_platform.connectors import CONNECTOR_OPERATIONS
from power_platform.flows import ALL_FLOWS, INTAKE_FLOW

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_POWER_AUTOMATE_DIR = REPO_ROOT / "power_platform" / "power_automate"
DEFAULT_CONNECTORS_DIR = REPO_ROOT / "power_platform" / "connectors"
DEFAULT_DATA_DIR = REPO_ROOT / "data" / "synthetic"
DEFAULT_REPORTS_DIR = REPO_ROOT / "reports"

_EXECUTION_TRACE_START = datetime(2026, 1, 15, 9, 0, tzinfo=UTC)


def build_flow_spec_files() -> dict[str, Any]:
    """One JSON-serializable payload per flow, keyed by filename."""
    return {f"{flow.flow_id}.flow.json": flow.to_dict() for flow in ALL_FLOWS}


def build_connector_operations_payload() -> list[dict[str, Any]]:
    return [operation.to_dict() for operation in CONNECTOR_OPERATIONS]


def build_approval_examples_payload() -> list[dict[str, Any]]:
    return [record.to_dict() for record in build_example_approvals()]


def build_execution_trace_example() -> dict[str, Any]:
    """A deterministic, simulated step-by-step run of the intake flow.

    This is a reference example only — it does not call any canonical or
    adapter function to produce it (the steps themselves already document
    what each one does); it exists to show what an execution trace/audit
    log for a flow run would look like. **Not a live Power Platform run
    history.**
    """
    steps: list[dict[str, Any]] = []
    for index, step in enumerate(INTAKE_FLOW.steps):
        steps.append(
            {
                "step_id": step.step_id,
                "name": step.name,
                "kind": step.kind.value,
                "operation": step.operation,
                "status": "simulated_success",
                "timestamp": (_EXECUTION_TRACE_START + timedelta(minutes=index)).isoformat(),
            }
        )
    return {
        "trace_type": "simulated_reference_example",
        "flow_id": INTAKE_FLOW.flow_id,
        "canonical_case_id": "SR-DS-9002",
        "correlation_id": "simulated-correlation-intake-SR-DS-9002",
        "note": "Deterministic simulation only — not a live Power Platform run history.",
        "steps": steps,
    }


def build_automation_summary() -> dict[str, Any]:
    steps_by_kind: dict[str, int] = {}
    total_steps = 0
    for flow in ALL_FLOWS:
        for step in flow.steps:
            steps_by_kind[step.kind.value] = steps_by_kind.get(step.kind.value, 0) + 1
            total_steps += 1

    human_steps = sum(1 for flow in ALL_FLOWS for step in flow.steps if step.requires_human)
    approvals = build_example_approvals()
    trace = build_execution_trace_example()

    return {
        "generated_from": "power_platform.evidence (deterministic, synthetic)",
        "flows": {
            "count": len(ALL_FLOWS),
            "flow_ids": [flow.flow_id for flow in ALL_FLOWS],
            "by_trigger_type": {flow.flow_id: flow.trigger_type.value for flow in ALL_FLOWS},
            "total_steps": total_steps,
            "steps_by_kind": steps_by_kind,
            "steps_requiring_human": human_steps,
        },
        "connector_operations": {
            "count": len(CONNECTOR_OPERATIONS),
            "idempotent_count": sum(1 for op in CONNECTOR_OPERATIONS if op.idempotent),
            "names": [op.name for op in CONNECTOR_OPERATIONS],
        },
        "approval_examples": {
            "count": len(approvals),
            "decisions": {record.decision.value: 1 for record in approvals},
        },
        "execution_trace_example": {
            "flow_id": trace["flow_id"],
            "step_count": len(trace["steps"]),
            "trace_type": trace["trace_type"],
        },
        "note": (
            "Synthetic portfolio evidence only — no live Power Platform environment, "
            "deployed flow, or run history. See README Portfolio & Simulation Disclaimer."
        ),
    }


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def generate_all(
    *,
    power_automate_dir: Path = DEFAULT_POWER_AUTOMATE_DIR,
    connectors_dir: Path = DEFAULT_CONNECTORS_DIR,
    data_dir: Path = DEFAULT_DATA_DIR,
    reports_dir: Path = DEFAULT_REPORTS_DIR,
) -> dict[str, Path]:
    """Generate all Milestone 4 evidence artefacts and return their paths, by filename."""
    outputs: dict[Path, Any] = {}

    for filename, payload in build_flow_spec_files().items():
        outputs[power_automate_dir / filename] = payload

    outputs[connectors_dir / "operations.json"] = build_connector_operations_payload()
    outputs[data_dir / "power_platform_approval_examples.json"] = build_approval_examples_payload()
    outputs[data_dir / "power_platform_execution_trace.json"] = build_execution_trace_example()
    outputs[reports_dir / "automation_summary.json"] = build_automation_summary()

    for path, payload in outputs.items():
        _write_json(path, payload)
    return {path.name: path for path in outputs}


if __name__ == "__main__":  # pragma: no cover
    for name, path in generate_all().items():
        print(f"wrote {name} -> {path}")
