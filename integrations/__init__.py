"""API-first integration layer.

Holds the `IntegrationEnvelope` data shape, deterministic CRM example
generation, and a local/reference Milestone 7 transport layer. No live
message broker, public API, webhook endpoint, or SaaS connector is
implemented — see integrations/README.md.
"""

from integrations.delivery import DeliveryRecord, DeliveryState
from integrations.envelope import (
    IntegrationEnvelope,
    IntegrationOperation,
    SourceSystem,
    envelope_to_dict,
    new_correlation_id,
)
from integrations.idempotency import IdempotencyStore, derive_idempotency_key
from integrations.retry import RetryPolicy
from integrations.transport import StubOutboundTransport
from integrations.webhooks import WebhookProcessor, validate_envelope

__all__ = [
    "DeliveryRecord",
    "DeliveryState",
    "IdempotencyStore",
    "IntegrationEnvelope",
    "IntegrationOperation",
    "RetryPolicy",
    "SourceSystem",
    "StubOutboundTransport",
    "WebhookProcessor",
    "derive_idempotency_key",
    "envelope_to_dict",
    "new_correlation_id",
    "validate_envelope",
]
