"""Tests for the integration envelope and the deterministic CRM example generator."""

import json
from datetime import UTC, datetime

from business_process import ServiceCategory
from integrations.envelope import (
    IntegrationEnvelope,
    IntegrationOperation,
    SourceSystem,
    envelope_to_dict,
    new_correlation_id,
)
from integrations.examples import build_dynamics_examples, build_salesforce_examples, generate_all

_NOW = datetime(2026, 1, 12, 15, 0, tzinfo=UTC)


def _envelope(**overrides):
    defaults = dict(
        source_system=SourceSystem.DYNAMICS_365,
        source_record_id="abc-123",
        canonical_case_id="SR-DS-1001",
        correlation_id="corr-1",
        schema_version="1.0",
        timestamp=_NOW,
        operation=IntegrationOperation.UPSERT,
    )
    defaults.update(overrides)
    return IntegrationEnvelope(**defaults)


# --- Envelope ---------------------------------------------------------------


def test_new_correlation_id_is_deterministic_for_the_same_seed():
    assert new_correlation_id("dynamics365:SR-DS-1001") == new_correlation_id(
        "dynamics365:SR-DS-1001"
    )


def test_new_correlation_id_differs_by_seed():
    assert new_correlation_id("dynamics365:SR-DS-1001") != new_correlation_id(
        "salesforce:SR-DS-1001"
    )


def test_envelope_to_dict_is_json_serializable():
    envelope = _envelope()
    payload = envelope_to_dict(envelope)
    reloaded = json.loads(json.dumps(payload))
    assert reloaded["source_system"] == "dynamics365"
    assert reloaded["operation"] == "upsert"
    assert reloaded["canonical_case_id"] == "SR-DS-1001"


# --- Example generator -------------------------------------------------------


def test_build_dynamics_examples_covers_every_synthetic_fixture():
    examples = build_dynamics_examples()
    assert len(examples) == 6
    categories = {example["incident"]["ticketnumber"].split("-")[1] for example in examples}
    assert len(categories) == 6  # one per category prefix (DS, CE, FA, AI, AS, DR)


def test_build_dynamics_examples_preserve_canonical_case_identity():
    examples = build_dynamics_examples()
    for example in examples:
        assert example["envelope"]["canonical_case_id"] == example["incident"]["ticketnumber"]
        assert example["envelope"]["source_record_id"] == example["incident"]["incidentid"]
        assert example["envelope"]["source_system"] == "dynamics365"


def test_build_dynamics_examples_is_deterministic():
    assert build_dynamics_examples() == build_dynamics_examples()


def test_build_dynamics_examples_computes_sla_breach_for_escalated_case():
    examples = build_dynamics_examples()
    escalated = next(e for e in examples if e["incident"]["ticketnumber"] == "SR-CE-1002")
    assert escalated["incident"]["sla_resolution_breached"] is True


def test_build_salesforce_examples_covers_every_synthetic_fixture():
    examples = build_salesforce_examples()
    assert len(examples) == 6


def test_build_salesforce_examples_preserve_canonical_case_identity():
    examples = build_salesforce_examples()
    for example in examples:
        assert example["envelope"]["canonical_case_id"] == example["case"]["canonical_case_id"]
        assert example["envelope"]["source_record_id"] == example["case"]["id"]
        assert example["envelope"]["source_system"] == "salesforce"


def test_build_salesforce_examples_is_deterministic():
    assert build_salesforce_examples() == build_salesforce_examples()


def test_dynamics_and_salesforce_examples_share_the_same_canonical_case_ids():
    dynamics_ids = {e["envelope"]["canonical_case_id"] for e in build_dynamics_examples()}
    salesforce_ids = {e["envelope"]["canonical_case_id"] for e in build_salesforce_examples()}
    assert dynamics_ids == salesforce_ids


def test_examples_cover_every_service_category_via_queue():
    examples = build_dynamics_examples()
    queues = {ex["incident"]["queue_name"] for ex in examples}
    assert len(queues) == len(ServiceCategory)


def test_generate_all_writes_expected_files(tmp_path):
    written = generate_all(data_dir=tmp_path)
    assert set(written.keys()) == {"dynamics365_examples.json", "salesforce_examples.json"}
    for path in written.values():
        assert path.is_file()
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert len(payload) == 6


def test_generate_all_is_deterministic(tmp_path):
    first = generate_all(data_dir=tmp_path / "a")
    second = generate_all(data_dir=tmp_path / "b")
    for name in first:
        assert first[name].read_text(encoding="utf-8") == second[name].read_text(encoding="utf-8")
