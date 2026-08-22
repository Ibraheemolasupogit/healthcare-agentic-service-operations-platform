"""API-first integration layer.

Currently holds the `IntegrationEnvelope` data shape and a deterministic
example generator (`integrations.examples`) that shows how a future
connector would sit around the `dynamics365` and `salesforce` adapters. No
transport, message broker, or live connector is implemented — see
integrations/README.md.
"""

from integrations.envelope import (
    IntegrationEnvelope,
    IntegrationOperation,
    SourceSystem,
    envelope_to_dict,
    new_correlation_id,
)

__all__ = [
    "IntegrationEnvelope",
    "IntegrationOperation",
    "SourceSystem",
    "envelope_to_dict",
    "new_correlation_id",
]
