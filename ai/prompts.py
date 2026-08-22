"""Versioned prompt/template metadata for Milestone 5.

Prompts document intent, schemas, and safety constraints. They do not hide
business rules; lifecycle, routing, SLA, escalation, and approval decisions
remain in deterministic packages.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class PromptTemplate:
    """Reference prompt metadata."""

    prompt_id: str
    version: str
    purpose: str
    input_schema: dict[str, str]
    output_schema: dict[str, str]
    safety_constraints: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt_id": self.prompt_id,
            "version": self.version,
            "purpose": self.purpose,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "safety_constraints": list(self.safety_constraints),
        }


PROMPTS: tuple[PromptTemplate, ...] = (
    PromptTemplate(
        prompt_id="prompt-triage-recommendation",
        version="1.0",
        purpose="Recommend category, priority, queue, rationale, confidence, and uncertainty.",
        input_schema={"title": "string", "description": "string"},
        output_schema={
            "suggested_category": "ServiceCategory value",
            "suggested_priority": "Priority value",
            "suggested_queue": "Queue value from canonical route_category result",
            "confidence": "0.0-1.0 number",
        },
        safety_constraints=(
            "Do not decide canonical routing or SLA.",
            "Return a recommendation only.",
            "Surface uncertainty for human review.",
        ),
    ),
    PromptTemplate(
        prompt_id="prompt-case-summary",
        version="1.0",
        purpose="Summarize a canonical case for a service agent.",
        input_schema={"case": "canonical Case object"},
        output_schema={"summary": "string", "open_items": "array", "audit_reference": "string"},
        safety_constraints=(
            "Use only supplied case fields.",
            "Do not infer clinical facts.",
            "Do not create or change case state.",
        ),
    ),
    PromptTemplate(
        prompt_id="prompt-knowledge-answer",
        version="1.0",
        purpose="Answer from retrieved synthetic service-operations knowledge.",
        input_schema={"question": "string", "retrieved_articles": "array"},
        output_schema={"answer": "string", "article_ids": "array", "uncertainty": "string"},
        safety_constraints=(
            "Ground answer in retrieved article text.",
            "Refuse clinical diagnosis or treatment requests.",
            "Do not expose secrets or credentials.",
        ),
    ),
    PromptTemplate(
        prompt_id="prompt-tool-selection",
        version="1.0",
        purpose="Select an allow-listed tool or refuse unsupported action.",
        input_schema={"intent": "string", "agent_id": "string", "available_tools": "array"},
        output_schema={"tool_name": "string or null", "requires_approval": "boolean"},
        safety_constraints=(
            "Only select tools from TOOL_REGISTRY.",
            "State-changing tools require human approval.",
            "Unsupported tools must be refused.",
        ),
    ),
    PromptTemplate(
        prompt_id="prompt-escalation-explanation",
        version="1.0",
        purpose="Explain SLA/escalation status from canonical evaluation output.",
        input_schema={"case": "canonical Case", "sla_status": "SLAStatus", "reason": "string/null"},
        output_schema={"explanation": "string", "recommended_next_step": "string"},
        safety_constraints=(
            "Do not calculate SLA in prompt.",
            "Use supplied canonical evaluation only.",
            "Escalation execution remains deterministic and governed.",
        ),
    ),
)

PROMPTS_BY_ID: dict[str, PromptTemplate] = {prompt.prompt_id: prompt for prompt in PROMPTS}


def validate_prompt_template(prompt: PromptTemplate) -> None:
    """Raise `ValueError` if prompt metadata is incomplete."""
    if not prompt.prompt_id:
        raise ValueError("prompt_id is required")
    if not prompt.version:
        raise ValueError(f"{prompt.prompt_id}: version is required")
    if not prompt.purpose:
        raise ValueError(f"{prompt.prompt_id}: purpose is required")
    if not prompt.input_schema:
        raise ValueError(f"{prompt.prompt_id}: input_schema is required")
    if not prompt.output_schema:
        raise ValueError(f"{prompt.prompt_id}: output_schema is required")
    if not prompt.safety_constraints:
        raise ValueError(f"{prompt.prompt_id}: safety_constraints are required")


__all__ = ["PROMPTS", "PROMPTS_BY_ID", "PromptTemplate", "validate_prompt_template"]
