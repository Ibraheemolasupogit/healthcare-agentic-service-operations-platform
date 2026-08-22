"""Lightweight integration envelope.

A small, platform-neutral metadata wrapper around a translated payload
exchanged between the canonical domain and a platform adapter (or, in a
later milestone, a real connector). This is a data shape only — there is no
transport, queue, retry, or delivery-guarantee logic here. See
integrations/README.md for how a future API connector would use it.
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


class IntegrationOperation(StrEnum):
    """What kind of change a payload represents."""

    CREATE = "create"
    UPDATE = "update"
    UPSERT = "upsert"
    SYNC = "sync"


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


def new_correlation_id(seed: str) -> str:
    """Deterministic correlation id derived from `seed` (e.g. a case id).

    Deterministic (not random) so examples and tests are reproducible; a
    real connector would typically use a random id per request instead.
    """
    return str(uuid.uuid5(_NAMESPACE, seed))


def envelope_to_dict(envelope: IntegrationEnvelope) -> dict[str, Any]:
    """Convert an `IntegrationEnvelope` to a JSON-safe dict."""
    return {
        "source_system": envelope.source_system.value,
        "source_record_id": envelope.source_record_id,
        "canonical_case_id": envelope.canonical_case_id,
        "correlation_id": envelope.correlation_id,
        "schema_version": envelope.schema_version,
        "timestamp": envelope.timestamp.isoformat(),
        "operation": envelope.operation.value,
    }
