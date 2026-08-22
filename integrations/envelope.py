"""Lightweight integration envelope.

A small, platform-neutral metadata wrapper around a translated payload
exchanged between the canonical domain and a platform adapter (or, in a
later milestone, a real connector). The envelope is still only metadata:
transport, retry, delivery state, and observability live in adjacent
Milestone 7 modules rather than inside this data contract.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

_NAMESPACE = uuid.uuid5(
    uuid.NAMESPACE_DNS, "integrations.synthetic.healthcare-agentic-service-operations-platform"
)


class SourceSystem(StrEnum):
    """Which system a payload's data currently originates from."""

    CANONICAL = "business_process"
    DYNAMICS_365 = "dynamics365"
    SALESFORCE = "salesforce"
    POWER_PLATFORM = "power_platform"
    COPILOT = "copilot"
    EXTERNAL = "external"


class IntegrationOperation(StrEnum):
    """What kind of change a payload represents."""

    CREATE = "create"
    UPDATE = "update"
    UPSERT = "upsert"
    SYNC = "sync"
    WEBHOOK = "webhook"
    APPROVAL_DECISION = "approval_decision"
    AUTOMATION_EVENT = "automation_event"


@dataclass(frozen=True, slots=True)
class IntegrationEnvelope:
    """Metadata carried alongside (not inside) a translated payload.

    `canonical_case_id` (`business_process.models.Case.case_id`) is the
    stable identity used for idempotent upserts across every system — see
    "Idempotency and external IDs" in docs/crm_schema_mapping.md.
    `source_record_id` is the identifier of the record *in* `source_system`
    (e.g. a Dynamics `incidentid` or a Salesforce `Id`); for a canonical
    payload it equals `canonical_case_id`.
    """

    source_system: SourceSystem
    source_record_id: str
    canonical_case_id: str
    correlation_id: str
    schema_version: str
    timestamp: datetime
    operation: IntegrationOperation
    envelope_id: str | None = None
    target_system: SourceSystem | None = None
    causation_id: str | None = None
    idempotency_key: str | None = None
    trace: dict[str, str] | None = None


def new_correlation_id(seed: str) -> str:
    """Deterministic correlation id derived from `seed` (e.g. a case id).

    Deterministic (not random) so examples and tests are reproducible; a
    real connector would typically use a random id per request instead.
    """
    return str(uuid.uuid5(_NAMESPACE, seed))


def envelope_to_dict(envelope: IntegrationEnvelope) -> dict[str, Any]:
    """Convert an `IntegrationEnvelope` to a JSON-safe dict."""
    payload: dict[str, Any] = {
        "source_system": envelope.source_system.value,
        "source_record_id": envelope.source_record_id,
        "canonical_case_id": envelope.canonical_case_id,
        "correlation_id": envelope.correlation_id,
        "schema_version": envelope.schema_version,
        "timestamp": envelope.timestamp.isoformat(),
        "operation": envelope.operation.value,
    }
    optional = {
        "envelope_id": envelope.envelope_id,
        "target_system": envelope.target_system.value if envelope.target_system else None,
        "causation_id": envelope.causation_id,
        "idempotency_key": envelope.idempotency_key,
        "trace": envelope.trace,
    }
    payload.update({key: value for key, value in optional.items() if value is not None})
    return payload
