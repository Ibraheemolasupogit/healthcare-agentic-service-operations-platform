"""Deterministic reference triage recommendations.

This is not an LLM and not a business-rule source of truth. It produces a
bounded recommendation from synthetic text; canonical category validation,
priority validation, and queue assignment remain authoritative elsewhere.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from business_process import Priority, ServiceCategory, route_category


@dataclass(frozen=True, slots=True)
class TriageRecommendation:
    """AI-assisted triage output used for review and evaluation."""

    suggested_category: ServiceCategory
    suggested_priority: Priority
    suggested_queue: str
    rationale: str
    confidence: float
    uncertainty_indicators: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "suggested_category": self.suggested_category.value,
            "suggested_priority": self.suggested_priority.value,
            "suggested_queue": self.suggested_queue,
            "rationale": self.rationale,
            "confidence": self.confidence,
            "uncertainty_indicators": list(self.uncertainty_indicators),
        }


_CATEGORY_KEYWORDS: dict[ServiceCategory, tuple[str, ...]] = {
    ServiceCategory.DIGITAL_SUPPORT: ("laptop", "wifi", "wi-fi", "workstation", "printer"),
    ServiceCategory.CLINICAL_EQUIPMENT: ("equipment", "pump", "firmware", "maintenance"),
    ServiceCategory.FACILITIES: ("room", "heating", "air", "conditioning", "facilities"),
    ServiceCategory.ACCESS_AND_IDENTITY: ("access", "password", "mfa", "starter", "account"),
    ServiceCategory.APPLICATION_SUPPORT: ("application", "app", "timeout", "outage", "error"),
    ServiceCategory.DATA_AND_REPORTING: ("report", "dashboard", "data", "analytics", "export"),
}

_PRIORITY_KEYWORDS: tuple[tuple[Priority, tuple[str, ...]], ...] = (
    (Priority.CRITICAL, ("critical", "urgent", "fleet", "advisory", "outage")),
    (Priority.HIGH, ("blocked", "new starter", "access", "multiple users")),
    (Priority.MEDIUM, ("intermittent", "repeatedly", "cannot", "failed")),
    (Priority.LOW, ("routine", "monthly", "minor", "single room")),
)


def _score_category(text: str) -> tuple[ServiceCategory, int, list[str]]:
    lowered = text.lower()
    matches: list[tuple[int, str, ServiceCategory]] = []
    for category, keywords in _CATEGORY_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in lowered)
        matches.append((score, category.value, category))
    matches.sort(key=lambda item: (-item[0], item[1]))
    best_score, _, best_category = matches[0]
    tied = [category for score, _, category in matches if score == best_score and score > 0]
    uncertainties: list[str] = []
    if best_score == 0:
        uncertainties.append("no category keyword match")
    if len(tied) > 1:
        uncertainties.append("multiple category matches")
    return best_category, best_score, uncertainties


def _recommend_priority(text: str) -> tuple[Priority, int]:
    lowered = text.lower()
    for priority, keywords in _PRIORITY_KEYWORDS:
        score = sum(1 for keyword in keywords if keyword in lowered)
        if score:
            return priority, score
    return Priority.MEDIUM, 0


def recommend_triage(title: str, description: str) -> TriageRecommendation:
    """Return a deterministic AI-triage recommendation for human/canonical review."""
    text = f"{title} {description}"
    category, category_score, uncertainties = _score_category(text)
    priority, priority_score = _recommend_priority(text)
    if priority_score == 0:
        uncertainties.append("no priority keyword match")
    queue = route_category(category)
    confidence = min(0.95, 0.45 + (category_score * 0.15) + (priority_score * 0.1))
    if uncertainties:
        confidence = min(confidence, 0.65)
    return TriageRecommendation(
        suggested_category=category,
        suggested_priority=priority,
        suggested_queue=queue.value,
        rationale=(
            "Recommendation from deterministic keyword evidence; canonical validation and "
            "routing remain authoritative."
        ),
        confidence=round(confidence, 2),
        uncertainty_indicators=tuple(uncertainties),
    )


__all__ = ["TriageRecommendation", "recommend_triage"]
