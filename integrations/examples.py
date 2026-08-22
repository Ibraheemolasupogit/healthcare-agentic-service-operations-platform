"""Deterministic example generator: canonical case -> CRM representations.

This module is the one place in this milestone that plays the role of a
*future API connector*: it asks `business_process` for already-decided
canonical state (the synthetic fixtures and their current SLA status), then
calls each adapter's pure translation function and wraps the result in an
`IntegrationEnvelope`. It implements no transport, retry, or message-broker
behaviour — see integrations/README.md.

Neither `dynamics365` nor `salesforce` imports any business_process decision
function directly (see tests/test_adapter_boundary.py); this module is where
that decided state and the adapters' translations are brought together.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from business_process.models import Case
from business_process.sla import evaluate_sla, get_sla_target
from business_process.taxonomy import CaseStage
from dynamics365.mapping import to_dynamics_incident, to_dynamics_timeline
from dynamics365.serialization import dynamics_incident_to_dict, dynamics_timeline_entry_to_dict
from integrations.envelope import (
    IntegrationEnvelope,
    IntegrationOperation,
    SourceSystem,
    envelope_to_dict,
    new_correlation_id,
)
from salesforce.mapping import to_salesforce_case, to_salesforce_feed
from salesforce.serialization import salesforce_case_to_dict, salesforce_feed_item_to_dict

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = REPO_ROOT / "data" / "synthetic"

SCHEMA_VERSION = "1.0"


def _example_now() -> datetime:
    """Fixed, deterministic "now" for illustrating SLA breach state.

    Matches the reference date used by business_process.fixtures — see its
    module docstring. Not wall-clock time, so examples are reproducible.
    """
    return datetime(2026, 1, 12, 15, 0, tzinfo=UTC)


def _first_response_at(case: Case) -> datetime | None:
    """Timestamp of the first move to IN_PROGRESS, used as a first-response proxy.

    business_process does not model a distinct "first response" event in
    this milestone; this is a documented, illustrative stand-in used only
    by this example generator, not by either adapter.
    """
    for event in case.history:
        if event.to_stage == CaseStage.IN_PROGRESS:
            return event.timestamp
    return None


def _resolved_at(case: Case) -> datetime | None:
    for event in case.history:
        if event.to_stage == CaseStage.RESOLVED:
            return event.timestamp
    return None


def _import_fixtures() -> list[Case]:
    # Imported lazily so importing this module doesn't require fixtures.py
    # unless an example is actually being built.
    from business_process.fixtures import build_synthetic_cases

    return build_synthetic_cases()


def build_dynamics_examples() -> list[dict[str, Any]]:
    """Build deterministic Dynamics 365 examples for every synthetic fixture case."""
    now = _example_now()
    examples: list[dict[str, Any]] = []
    for case in _import_fixtures():
        target = get_sla_target(case.category, case.priority)
        status = evaluate_sla(
            target,
            created_at=case.created_at,
            now=now,
            first_response_at=_first_response_at(case),
            resolved_at=_resolved_at(case),
        )
        incident = to_dynamics_incident(
            case,
            response_due_at=status.response_due_at,
            resolve_by_at=status.resolution_due_at,
            response_breached=status.response_breached,
            resolution_breached=status.resolution_breached,
        )
        timeline = to_dynamics_timeline(case)
        envelope = IntegrationEnvelope(
            source_system=SourceSystem.DYNAMICS_365,
            source_record_id=incident.incidentid,
            canonical_case_id=case.case_id,
            correlation_id=new_correlation_id(f"dynamics365:{case.case_id}"),
            schema_version=SCHEMA_VERSION,
            timestamp=now,
            operation=IntegrationOperation.UPSERT,
        )
        examples.append(
            {
                "envelope": envelope_to_dict(envelope),
                "incident": dynamics_incident_to_dict(incident),
                "timeline": [dynamics_timeline_entry_to_dict(entry) for entry in timeline],
            }
        )
    return examples


def build_salesforce_examples() -> list[dict[str, Any]]:
    """Build deterministic Salesforce examples for every synthetic fixture case."""
    now = _example_now()
    examples: list[dict[str, Any]] = []
    for case in _import_fixtures():
        target = get_sla_target(case.category, case.priority)
        status = evaluate_sla(
            target,
            created_at=case.created_at,
            now=now,
            first_response_at=_first_response_at(case),
            resolved_at=_resolved_at(case),
        )
        sf_case = to_salesforce_case(
            case,
            first_response_target=status.response_due_at,
            resolution_target=status.resolution_due_at,
            first_response_breached=status.response_breached,
            resolution_breached=status.resolution_breached,
        )
        feed = to_salesforce_feed(case)
        envelope = IntegrationEnvelope(
            source_system=SourceSystem.SALESFORCE,
            source_record_id=sf_case.id,
            canonical_case_id=case.case_id,
            correlation_id=new_correlation_id(f"salesforce:{case.case_id}"),
            schema_version=SCHEMA_VERSION,
            timestamp=now,
            operation=IntegrationOperation.UPSERT,
        )
        examples.append(
            {
                "envelope": envelope_to_dict(envelope),
                "case": salesforce_case_to_dict(sf_case),
                "feed": [salesforce_feed_item_to_dict(item) for item in feed],
            }
        )
    return examples


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def generate_all(*, data_dir: Path = DEFAULT_DATA_DIR) -> dict[str, Path]:
    """Generate both CRM example artefacts and return their paths, by filename."""
    outputs: dict[Path, Any] = {
        data_dir / "dynamics365_examples.json": build_dynamics_examples(),
        data_dir / "salesforce_examples.json": build_salesforce_examples(),
    }
    for path, payload in outputs.items():
        _write_json(path, payload)
    return {path.name: path for path in outputs}


if __name__ == "__main__":  # pragma: no cover
    for name, path in generate_all().items():
        print(f"wrote {name} -> {path}")
