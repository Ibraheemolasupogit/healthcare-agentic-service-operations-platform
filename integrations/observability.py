"""Integration observability metrics over deterministic delivery traces."""

from __future__ import annotations

from typing import Any


def build_integration_metrics(delivery_traces: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    """Aggregate reference delivery metrics for reports and analytics."""
    deliveries = [trace["delivery"] for trace in delivery_traces]
    total = len(deliveries)
    delivered = sum(1 for delivery in deliveries if delivery["state"] == "delivered")
    duplicates = sum(1 for delivery in deliveries if delivery["state"] == "duplicate")
    failures = sum(1 for delivery in deliveries if delivery["state"] == "failed")
    dead_lettered = sum(1 for delivery in deliveries if delivery["state"] == "dead_lettered")
    retried = sum(1 for delivery in deliveries if delivery["attempts"] > 1)
    return {
        "generated_from": "integrations.observability.build_integration_metrics",
        "envelopes_received": total,
        "delivered_count": delivered,
        "duplicate_count": duplicates,
        "failed_count": failures,
        "dead_letter_count": dead_lettered,
        "retry_delivery_count": retried,
        "delivery_success_rate_percent": round((delivered / total) * 100, 2) if total else 0.0,
        "duplicate_rate_percent": round((duplicates / total) * 100, 2) if total else 0.0,
        "retry_rate_percent": round((retried / total) * 100, 2) if total else 0.0,
        "by_source_system": _count_by(deliveries, "source_system"),
        "by_target_system": _count_by(deliveries, "target_system"),
        "by_operation": _count_by(deliveries, "operation"),
        "by_state": _count_by(deliveries, "state"),
        "note": "Synthetic/reference integration observability only; no live telemetry.",
    }


def _count_by(records: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        value = str(record.get(key) or "Unknown")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


__all__ = ["build_integration_metrics"]
