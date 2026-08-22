"""Delivery-state model for local/reference integration transport."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any


class DeliveryState(StrEnum):
    """Integration delivery state, separate from canonical case lifecycle."""

    RECEIVED = "received"
    VALIDATED = "validated"
    PROCESSING = "processing"
    DELIVERED = "delivered"
    RETRY_PENDING = "retry_pending"
    FAILED = "failed"
    DEAD_LETTERED = "dead_lettered"
    DUPLICATE = "duplicate"


ALLOWED_DELIVERY_TRANSITIONS: dict[DeliveryState, frozenset[DeliveryState]] = {
    DeliveryState.RECEIVED: frozenset({DeliveryState.VALIDATED, DeliveryState.FAILED}),
    DeliveryState.VALIDATED: frozenset({DeliveryState.PROCESSING, DeliveryState.DUPLICATE}),
    DeliveryState.PROCESSING: frozenset(
        {DeliveryState.DELIVERED, DeliveryState.RETRY_PENDING, DeliveryState.FAILED}
    ),
    DeliveryState.RETRY_PENDING: frozenset({DeliveryState.PROCESSING, DeliveryState.DEAD_LETTERED}),
    DeliveryState.FAILED: frozenset({DeliveryState.RETRY_PENDING, DeliveryState.DEAD_LETTERED}),
    DeliveryState.DELIVERED: frozenset(),
    DeliveryState.DEAD_LETTERED: frozenset(),
    DeliveryState.DUPLICATE: frozenset(),
}


@dataclass(frozen=True, slots=True)
class DeliveryRecord:
    """One deterministic delivery outcome."""

    envelope_id: str
    idempotency_key: str
    correlation_id: str
    source_system: str
    target_system: str
    operation: str
    state: DeliveryState
    attempts: int
    created_at: datetime
    updated_at: datetime
    outcome: str
    error: str | None = None
    retryable: bool = False
    next_backoff_seconds: int | None = None
    manual_review_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert the record to deterministic JSON-safe evidence."""
        return {
            "envelope_id": self.envelope_id,
            "idempotency_key": self.idempotency_key,
            "correlation_id": self.correlation_id,
            "source_system": self.source_system,
            "target_system": self.target_system,
            "operation": self.operation,
            "state": self.state.value,
            "attempts": self.attempts,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "outcome": self.outcome,
            "error": self.error,
            "retryable": self.retryable,
            "next_backoff_seconds": self.next_backoff_seconds,
            "manual_review_required": self.manual_review_required,
        }


def is_valid_delivery_transition(from_state: DeliveryState, to_state: DeliveryState) -> bool:
    """Return whether the delivery-state transition is allowed."""
    return to_state in ALLOWED_DELIVERY_TRANSITIONS[from_state]


__all__ = [
    "ALLOWED_DELIVERY_TRANSITIONS",
    "DeliveryRecord",
    "DeliveryState",
    "is_valid_delivery_transition",
]
