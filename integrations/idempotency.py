"""Reference idempotency store for deterministic webhook processing."""

from __future__ import annotations

from dataclasses import dataclass, field

from integrations.delivery import DeliveryRecord, DeliveryState


@dataclass(slots=True)
class IdempotencyStore:
    """Small in-memory store suitable for tests and portfolio evidence."""

    records: dict[str, DeliveryRecord] = field(default_factory=dict)

    def completed_duplicate(self, key: str) -> DeliveryRecord | None:
        """Return an already-delivered record that must not be repeated."""
        record = self.records.get(key)
        if record and record.state is DeliveryState.DELIVERED:
            return record
        return None

    def record(self, delivery: DeliveryRecord) -> None:
        """Store the latest delivery record for the idempotency key."""
        self.records[delivery.idempotency_key] = delivery


def derive_idempotency_key(
    *,
    source_system: str,
    source_record_id: str,
    operation: str,
    target_system: str,
    explicit_key: str | None = None,
) -> str:
    """Derive a deterministic idempotency key when the envelope lacks one."""
    if explicit_key:
        return explicit_key
    return f"{source_system}:{source_record_id}:{operation}:{target_system}"


__all__ = ["IdempotencyStore", "derive_idempotency_key"]
