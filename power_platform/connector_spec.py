"""Typed model for a Power Platform connector operation contract.

`ConnectorOperation` documents the *intended* API boundary between Power
Platform (Power Automate/Power Apps) and the canonical service layer — a
custom-connector-style contract. It is a reference description only: no
live HTTP endpoint, custom connector definition, or Dataverse plugin is
built in this milestone. See power_platform/connectors/README.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class ConnectorOperationValidationError(ValueError):
    """Raised when a `ConnectorOperation` is structurally incomplete."""


@dataclass(frozen=True, slots=True)
class ConnectorOperation:
    """One representative operation on the intended Power Platform connector.

    `wraps_canonical` / `wraps_adapter` name the `business_process` /
    `dynamics365` callable this operation conceptually wraps, using the same
    closed `CanonicalOperation` / `AdapterOperation` vocabulary as workflow
    steps — kept as plain strings here (rather than importing those enums)
    to avoid a dependency cycle; `power_platform.flow_validation` is what
    actually checks the names resolve to real callables.
    """

    name: str
    description: str
    wraps_canonical: str | None
    wraps_adapter: str | None
    request_schema: dict[str, str]
    response_schema: dict[str, str]
    example_request: dict[str, Any]
    example_response: dict[str, Any]
    idempotent: bool
    requires_correlation_id: bool
    caveat: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "wraps_canonical": self.wraps_canonical,
            "wraps_adapter": self.wraps_adapter,
            "request_schema": self.request_schema,
            "response_schema": self.response_schema,
            "example_request": self.example_request,
            "example_response": self.example_response,
            "idempotent": self.idempotent,
            "requires_correlation_id": self.requires_correlation_id,
            "caveat": self.caveat,
        }


def validate_connector_operation(operation: ConnectorOperation) -> None:
    """Raise `ConnectorOperationValidationError` if `operation` is incomplete."""
    errors: list[str] = []
    if not operation.name:
        errors.append("name is required")
    if not operation.description:
        errors.append(f"{operation.name}: description is required")
    if operation.request_schema is None:
        errors.append(
            f"{operation.name}: request_schema is required "
            "(an empty dict is valid for a parameterless read)"
        )
    if not operation.response_schema:
        errors.append(f"{operation.name}: response_schema must not be empty")
    if operation.example_request is None:
        errors.append(f"{operation.name}: example_request is required")
    if operation.example_response is None:
        errors.append(f"{operation.name}: example_response is required")
    if not isinstance(operation.idempotent, bool):
        errors.append(f"{operation.name}: idempotent must be a bool")
    if not isinstance(operation.requires_correlation_id, bool):
        errors.append(f"{operation.name}: requires_correlation_id must be a bool")
    if errors:
        raise ConnectorOperationValidationError("; ".join(errors))


__all__ = [
    "ConnectorOperation",
    "ConnectorOperationValidationError",
    "validate_connector_operation",
]
