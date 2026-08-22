"""Bounded agentic-AI reference layer for Milestone 5.

Deterministic, provider-neutral reference implementation only: no live LLM
endpoint, no deployed agent, no production telemetry, and no autonomous case
mutation. Agents can interpret, summarize, retrieve, recommend, and propose
tool calls, but canonical decisions remain in `business_process` and
connector/tool permissions remain explicit.
"""

from ai.agents import AGENTS, AGENTS_BY_ID, AgentDefinition, AgentRole
from ai.knowledge import KNOWLEDGE_ARTICLES, KnowledgeArticle, retrieve_knowledge
from ai.prompts import PROMPTS, PROMPTS_BY_ID, PromptTemplate, validate_prompt_template
from ai.safety import SafetyDecision, assess_user_request
from ai.tools import (
    TOOL_REGISTRY,
    TOOL_REGISTRY_BY_NAME,
    ToolRisk,
    ToolSpec,
    ToolValidationError,
    validate_tool_call,
    validate_tool_registry,
)
from ai.triage import TriageRecommendation, recommend_triage

__all__ = [
    "AGENTS",
    "AGENTS_BY_ID",
    "KNOWLEDGE_ARTICLES",
    "PROMPTS",
    "PROMPTS_BY_ID",
    "TOOL_REGISTRY",
    "TOOL_REGISTRY_BY_NAME",
    "AgentDefinition",
    "AgentRole",
    "KnowledgeArticle",
    "PromptTemplate",
    "SafetyDecision",
    "ToolRisk",
    "ToolSpec",
    "ToolValidationError",
    "TriageRecommendation",
    "assess_user_request",
    "recommend_triage",
    "retrieve_knowledge",
    "validate_prompt_template",
    "validate_tool_call",
    "validate_tool_registry",
]
