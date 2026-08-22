"""Deterministic operational knowledge retrieval.

The corpus is synthetic operational support content only. It contains no
clinical diagnosis, treatment, patient-specific, or production organisation
information.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from business_process import ServiceCategory


@dataclass(frozen=True, slots=True)
class KnowledgeArticle:
    """Small synthetic knowledge article for grounded answers."""

    article_id: str
    title: str
    category: ServiceCategory
    tags: tuple[str, ...]
    answer: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "article_id": self.article_id,
            "title": self.title,
            "category": self.category.value,
            "tags": list(self.tags),
            "answer": self.answer,
        }


KNOWLEDGE_ARTICLES: tuple[KnowledgeArticle, ...] = (
    KnowledgeArticle(
        article_id="KA-ACCESS-001",
        title="Password reset and access request guidance",
        category=ServiceCategory.ACCESS_AND_IDENTITY,
        tags=("password", "access", "account", "mfa", "login"),
        answer=(
            "Use the access request route for account changes, MFA reset, and role-based "
            "access. Elevated or high-impact access must go through human approval."
        ),
    ),
    KnowledgeArticle(
        article_id="KA-DEVICE-001",
        title="Device and digital workplace support",
        category=ServiceCategory.DIGITAL_SUPPORT,
        tags=("laptop", "wifi", "workstation", "device", "printer"),
        answer=(
            "For device, Wi-Fi, printer, or collaboration-tool issues, capture the asset type, "
            "location, impact, and whether a workaround exists before submitting the request."
        ),
    ),
    KnowledgeArticle(
        article_id="KA-FAC-001",
        title="Facilities service request guidance",
        category=ServiceCategory.FACILITIES,
        tags=("heating", "air conditioning", "room", "estate", "facilities", "contractor"),
        answer=(
            "Facilities requests should include location, affected area, access constraints, "
            "and whether an external contractor may be needed."
        ),
    ),
    KnowledgeArticle(
        article_id="KA-APP-001",
        title="Application outage and timeout support",
        category=ServiceCategory.APPLICATION_SUPPORT,
        tags=("application", "outage", "timeout", "system", "error", "export"),
        answer=(
            "For application outages or timeouts, capture the application name, error text, "
            "approximate start time, affected users, and any repeatable steps."
        ),
    ),
    KnowledgeArticle(
        article_id="KA-EQUIP-001",
        title="Clinical equipment service routing",
        category=ServiceCategory.CLINICAL_EQUIPMENT,
        tags=("equipment", "pump", "device", "firmware", "advisory", "maintenance"),
        answer=(
            "Clinical equipment service requests should describe the equipment type, asset "
            "identifier if known, site, safety-adjacent impact, and whether the request is "
            "about maintenance, logistics, or manufacturer advisory review. Do not include "
            "patient details."
        ),
    ),
    KnowledgeArticle(
        article_id="KA-DATA-001",
        title="Reporting and data request guidance",
        category=ServiceCategory.DATA_AND_REPORTING,
        tags=("report", "dashboard", "data", "analytics", "export", "figures"),
        answer=(
            "Reporting requests should define the business question, date range, aggregate "
            "fields required, recipient role, and whether an existing scheduled report already "
            "covers the need."
        ),
    ),
)


def _tokens(text: str) -> set[str]:
    return {
        token.strip(".,:;!?()[]{}'\"").lower()
        for token in text.replace("-", " ").split()
        if token.strip(".,:;!?()[]{}'\"")
    }


def retrieve_knowledge(query: str, *, limit: int = 2) -> tuple[KnowledgeArticle, ...]:
    """Return the highest-scoring synthetic articles for `query`.

    Simple lexical scoring is sufficient here; this milestone does not need
    a vector database to demonstrate the boundary.
    """
    query_tokens = _tokens(query)
    scored: list[tuple[int, str, KnowledgeArticle]] = []
    for article in KNOWLEDGE_ARTICLES:
        haystack = _tokens(" ".join((article.title, article.answer, *article.tags)))
        score = len(query_tokens & haystack)
        if score:
            scored.append((score, article.article_id, article))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return tuple(item[2] for item in scored[:limit])


__all__ = ["KNOWLEDGE_ARTICLES", "KnowledgeArticle", "retrieve_knowledge"]
