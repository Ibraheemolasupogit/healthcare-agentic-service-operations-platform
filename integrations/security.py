"""Conceptual authentication/authorization checks for local integration tests."""

from __future__ import annotations

from dataclasses import dataclass

from integrations.envelope import IntegrationEnvelope


@dataclass(frozen=True, slots=True)
class IntegrationPrincipal:
    """Service-to-service caller identity metadata without secrets."""

    principal_id: str
    source_system: str
    audience: str
    environment: str
    scopes: frozenset[str]


def authorize_envelope(envelope: IntegrationEnvelope, principal: IntegrationPrincipal) -> None:
    """Validate conceptual audience, source binding, and write scope."""
    if principal.environment not in {"dev", "test", "prod"}:
        raise PermissionError("unknown integration environment")
    if principal.audience != "healthcare-service-operations-integrations":
        raise PermissionError("invalid integration audience")
    if principal.source_system != envelope.source_system.value:
        raise PermissionError("principal source system does not match envelope")
    if "integration:deliver" not in principal.scopes:
        raise PermissionError("missing integration:deliver scope")


__all__ = ["IntegrationPrincipal", "authorize_envelope"]
