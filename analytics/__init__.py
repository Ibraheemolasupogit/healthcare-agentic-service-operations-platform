"""Fabric-style analytics and operational intelligence for Milestone 6.

Deterministic local transformations only: no live Fabric workspace, Spark
job, semantic-model deployment, Power BI report, or production telemetry.
"""

from analytics.fabric.data_quality import DataQualityIssue, run_data_quality_checks
from analytics.fabric.gold import (
    build_automation_metrics,
    build_case_metrics,
    build_copilot_usage,
    build_gold_model,
    build_sla_summary,
)
from analytics.fabric.ingestion import BronzeModel, load_bronze_model
from analytics.fabric.silver import SilverModel, build_silver_model

__all__ = [
    "BronzeModel",
    "DataQualityIssue",
    "SilverModel",
    "build_automation_metrics",
    "build_case_metrics",
    "build_copilot_usage",
    "build_gold_model",
    "build_silver_model",
    "build_sla_summary",
    "load_bronze_model",
    "run_data_quality_checks",
]
