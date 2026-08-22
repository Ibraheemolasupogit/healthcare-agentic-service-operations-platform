"""Deterministic analytics evidence generation."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from analytics.fabric.data_quality import run_data_quality_checks
from analytics.fabric.gold import GoldModel, build_gold_model
from analytics.fabric.ingestion import DEFAULT_DATA_DIR, DEFAULT_REPORTS_DIR, load_bronze_model
from analytics.fabric.silver import build_silver_model

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUTS_DIR = REPO_ROOT / "outputs"


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_markdown(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _metric_rows(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, value in metrics.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                rows.append({"metric": f"{key}.{sub_key}", "value": sub_value})
        elif key not in {"note", "generated_from"}:
            rows.append({"metric": key, "value": value})
    return rows


def build_analytics_summary(gold: GoldModel | None = None) -> dict[str, Any]:
    """Build deterministic summary JSON for tracked portfolio evidence."""
    if gold is None:
        bronze = load_bronze_model()
        silver = build_silver_model(bronze)
        gold = build_gold_model(silver)
        quality_issues = run_data_quality_checks(silver)
    else:
        bronze = load_bronze_model()
        silver = build_silver_model(bronze)
        quality_issues = run_data_quality_checks(silver)

    return {
        "generated_from": "analytics.fabric.evidence (deterministic, synthetic)",
        "case_metrics": gold.case_metrics,
        "sla_summary": gold.sla_summary,
        "automation_metrics": gold.automation_metrics,
        "copilot_usage": gold.copilot_usage,
        "integration_metrics": gold.integration_metrics,
        "data_quality": {
            "issue_count": len(quality_issues),
            "issues": [issue.to_dict() for issue in quality_issues],
        },
        "lineage": [
            "Synthetic operational fixture",
            "canonical service domain",
            "CRM / automation / agent evidence",
            "integration transport evidence",
            "analytics Bronze ingestion",
            "Silver conformed operational entities",
            "Gold KPI outputs",
            "semantic model measures",
            "Power BI reference report",
        ],
        "note": (
            "Synthetic/generated portfolio evidence only — no live Fabric workspace, "
            "Lakehouse/Warehouse deployment, Spark job, semantic-model deployment, "
            "Power BI report, or production telemetry."
        ),
    }


def build_service_operations_report(summary: dict[str, Any] | None = None) -> str:
    """Concise generated executive report with proportional claims."""
    if summary is None:
        summary = build_analytics_summary()
    case_metrics = summary["case_metrics"]
    sla = summary["sla_summary"]
    automation = summary["automation_metrics"]
    ai = summary["copilot_usage"]
    integration = summary["integration_metrics"]
    return (
        "# Service Operations Analytics Report\n\n"
        "Synthetic/generated portfolio evidence only. This report is derived from "
        "repository fixtures and generated CRM, automation, approval, and AI evidence. "
        "It is not production telemetry.\n\n"
        "## Service Volume\n\n"
        f"- Total cases: {case_metrics['total_cases']}\n"
        f"- Open cases: {case_metrics['open_cases']}\n"
        f"- Resolved/closed cases: {case_metrics['resolved_cases']}\n"
        f"- Case volume by category: {case_metrics['case_volume_by_category']}\n"
        f"- Case volume by priority: {case_metrics['case_volume_by_priority']}\n\n"
        "## SLA and Escalation\n\n"
        f"- SLA compliance rate: {sla['sla_compliance_rate_percent']}%\n"
        f"- SLA breach count: {sla['sla_breach_count']}\n"
        f"- Escalation count: {case_metrics['escalation_count']}\n"
        f"- Escalation rate: {case_metrics['escalation_rate_percent']}%\n\n"
        "## Resolution Performance\n\n"
        f"- Mean resolution minutes: {case_metrics['mean_resolution_minutes']}\n"
        f"- Median resolution minutes: {case_metrics['median_resolution_minutes']}\n"
        f"- Resolution outcomes: {case_metrics['resolution_outcomes']}\n\n"
        "## Automation Observations\n\n"
        f"- Automation executions: {automation['automation_execution_count']}\n"
        f"- Simulated success rate: {automation['automation_success_rate_percent']}%\n"
        f"- Approval decisions: {automation['approval_decision_count']}\n\n"
        "## AI-Assistance Observations\n\n"
        f"- Agent/tool invocations: {ai['agent_tool_invocation_count']}\n"
        f"- Tool invocation mix by risk: {ai['tool_invocations_by_risk']}\n"
        f"- Approval-required AI actions: {ai['approval_required_action_count']}\n\n"
        "## Integration Observations\n\n"
        f"- Integration deliveries: {integration['integration_delivery_count']}\n"
        f"- Delivered envelopes: {integration['delivered_count']}\n"
        f"- Duplicate deliveries suppressed: {integration['duplicate_count']}\n"
        f"- Dead-letter/manual-review count: {integration['dead_letter_count']}\n\n"
        "## Limitations and Provenance\n\n"
        "- Dataset is intentionally tiny and synthetic.\n"
        "- No production baseline exists, so no improvement claim is made.\n"
        "- SLA calculations are delegated to `business_process.sla`.\n"
        "- Analytics is downstream only and is not a transactional source of truth.\n"
    )


def generate_all(
    *,
    data_dir: Path = DEFAULT_DATA_DIR,
    source_reports_dir: Path = DEFAULT_REPORTS_DIR,
    reports_dir: Path = DEFAULT_REPORTS_DIR,
    outputs_dir: Path = DEFAULT_OUTPUTS_DIR,
) -> dict[str, Path]:
    """Generate Milestone 6 analytics evidence and return paths by filename."""
    bronze = load_bronze_model(data_dir=data_dir, reports_dir=source_reports_dir)
    silver = build_silver_model(bronze)
    gold = build_gold_model(silver)
    summary = build_analytics_summary(gold)

    outputs: dict[Path, Any] = {
        reports_dir / "analytics_summary.json": summary,
        reports_dir / "service_operations_report.md": build_service_operations_report(summary),
    }
    csv_outputs = {
        outputs_dir / "case_metrics.csv": _metric_rows(gold.case_metrics),
        outputs_dir / "sla_summary.csv": _metric_rows(gold.sla_summary),
        outputs_dir / "automation_metrics.csv": _metric_rows(gold.automation_metrics),
        outputs_dir / "copilot_usage.csv": _metric_rows(gold.copilot_usage),
        outputs_dir / "integration_metrics.csv": _metric_rows(gold.integration_metrics),
    }

    for path, payload in outputs.items():
        if path.suffix == ".md":
            _write_markdown(path, str(payload))
        else:
            _write_json(path, payload)
    for path, rows in csv_outputs.items():
        _write_csv(path, rows)
        outputs[path] = rows
    return {path.name: path for path in outputs}


if __name__ == "__main__":  # pragma: no cover
    for name, path in generate_all().items():
        print(f"wrote {name} -> {path}")


__all__ = ["build_analytics_summary", "build_service_operations_report", "generate_all"]
