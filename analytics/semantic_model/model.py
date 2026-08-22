"""Reference semantic model metadata suitable for Power BI."""

from __future__ import annotations

from typing import Any

SEMANTIC_MODEL: dict[str, Any] = {
    "model_id": "service-operations-semantic-model-v1",
    "grain": {
        "fact_case": "one row per canonical service case",
        "fact_case_event": "one row per canonical case lifecycle event",
        "fact_sla_event": "one row per case SLA evaluation",
        "fact_automation_execution": "one row per simulated automation trace",
        "fact_agent_interaction": "one row per simulated agent tool trace",
        "fact_approval_decision": "one row per approval decision",
    },
    "dimensions": {
        "date": {"key": "date_key", "description": "Calendar date from event/case timestamps."},
        "service_category": {"key": "category", "source": "business_process.ServiceCategory"},
        "priority": {"key": "priority", "source": "business_process.Priority"},
        "queue": {"key": "queue", "source": "canonical queue assignment"},
        "case_status": {"key": "status", "source": "business_process.CaseStage"},
        "resolution_outcome": {
            "key": "resolution_outcome",
            "source": "business_process.ResolutionOutcome",
        },
        "automation_workflow": {"key": "flow_id", "source": "Power Automate spec id"},
        "agent": {"key": "agent_id", "source": "ai.agents.AgentDefinition"},
        "tool_risk_class": {"key": "risk", "source": "ai.tools.ToolRisk"},
    },
    "facts": {
        "fact_case": {
            "keys": ["case_id"],
            "relationships": ["service_category", "priority", "queue", "case_status"],
        },
        "fact_case_event": {
            "keys": ["case_id", "event_index"],
            "relationships": ["fact_case", "date"],
        },
        "fact_sla_event": {
            "keys": ["case_id"],
            "relationships": ["fact_case", "service_category", "priority"],
        },
        "fact_automation_execution": {
            "keys": ["flow_id", "correlation_id"],
            "relationships": ["automation_workflow"],
        },
        "fact_agent_interaction": {
            "keys": ["agent_id", "tool_name", "correlation_id"],
            "relationships": ["agent", "tool_risk_class"],
        },
        "fact_approval_decision": {
            "keys": ["approval_id"],
            "relationships": ["fact_case", "date"],
        },
    },
    "measures": {
        "Total Cases": "COUNTROWS(fact_case)",
        "Open Cases": "COUNTROWS(FILTER(fact_case, fact_case[is_open] = TRUE))",
        "SLA Compliance Rate": "DIVIDE([SLA Compliant Cases], [Total Cases])",
        "Escalation Rate": "DIVIDE([Escalated Cases], [Total Cases])",
        "Mean Resolution Minutes": "AVERAGE(fact_case[resolution_minutes])",
        "Automation Success Rate": (
            "DIVIDE([Successful Automation Executions], [Automation Executions])"
        ),
        "Agent Tool Invocations": "COUNTROWS(fact_agent_interaction)",
        "Approval Decisions": "COUNTROWS(fact_approval_decision)",
    },
    "filter_direction": "single direction from dimensions to facts unless explicitly reviewed",
    "slowly_changing_attributes": (
        "Not modelled for the synthetic fixture scale. Queue/category changes would be "
        "handled as event history plus current case attributes in a later warehouse."
    ),
}


def validate_semantic_model(model: dict[str, Any] = SEMANTIC_MODEL) -> None:
    """Raise if required semantic metadata is missing."""
    for section in ("model_id", "grain", "dimensions", "facts", "measures", "filter_direction"):
        if not model.get(section):
            raise ValueError(f"semantic model missing {section}")
    for fact_name, fact in model["facts"].items():
        if not fact.get("keys"):
            raise ValueError(f"{fact_name} missing keys")
        if "relationships" not in fact:
            raise ValueError(f"{fact_name} missing relationships")


__all__ = ["SEMANTIC_MODEL", "validate_semantic_model"]
