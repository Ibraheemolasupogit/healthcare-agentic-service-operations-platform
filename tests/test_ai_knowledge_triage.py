"""Tests for deterministic knowledge retrieval and AI triage recommendations."""

from ai.knowledge import KNOWLEDGE_ARTICLES, retrieve_knowledge
from ai.triage import recommend_triage


def test_knowledge_corpus_is_operational_not_clinical():
    text = " ".join(article.answer for article in KNOWLEDGE_ARTICLES).lower()
    for forbidden in ("diagnosis", "diagnose", "treatment plan", "prescribe"):
        assert forbidden not in text


def test_retrieve_access_knowledge_is_grounded():
    articles = retrieve_knowledge("How do I request access or MFA reset?")
    assert articles
    assert articles[0].article_id == "KA-ACCESS-001"


def test_retrieve_device_knowledge_is_deterministic():
    assert retrieve_knowledge("laptop wifi problem") == retrieve_knowledge("laptop wifi problem")


def test_retrieve_knowledge_returns_empty_for_no_match():
    assert retrieve_knowledge("unrelated cafeteria menu") == ()


def test_triage_recommends_facilities_category():
    rec = recommend_triage("Room air conditioning fault", "Meeting room is not cooling")
    assert rec.suggested_category.value == "Facilities"
    assert rec.suggested_queue == "Facilities Operations"
    assert rec.confidence > 0


def test_triage_recommends_critical_equipment_advisory():
    rec = recommend_triage(
        "Critical firmware advisory",
        "Manufacturer advisory for equipment fleet requires review",
    )
    assert rec.suggested_category.value == "Clinical Equipment"
    assert rec.suggested_priority.value == "Critical"


def test_triage_surfaces_uncertainty_for_ambiguous_text():
    rec = recommend_triage("Help needed", "Something is wrong")
    assert rec.uncertainty_indicators
    assert rec.confidence <= 0.65


def test_triage_is_a_recommendation_not_authoritative_rule_text():
    rec = recommend_triage("Application timeout", "Rostering app intermittently times out")
    assert "Recommendation" in rec.rationale
    assert "canonical validation" in rec.rationale
