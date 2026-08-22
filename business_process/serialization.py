"""JSON-safe serialization for the canonical case model.

Kept separate from `models.py` so the domain types stay plain dataclasses
with no knowledge of any particular output format.
"""

from __future__ import annotations

from typing import Any

from business_process.models import Case, CaseEvent


def case_event_to_dict(event: CaseEvent) -> dict[str, Any]:
    """Convert a `CaseEvent` to a JSON-safe dict."""
    return {
        "timestamp": event.timestamp.isoformat(),
        "actor": event.actor,
        "event_type": event.event_type,
        "detail": event.detail,
        "from_stage": event.from_stage.value if event.from_stage is not None else None,
        "to_stage": event.to_stage.value if event.to_stage is not None else None,
    }


def case_to_dict(case: Case) -> dict[str, Any]:
    """Convert a `Case` (including its full history) to a JSON-safe dict."""
    return {
        "case_id": case.case_id,
        "title": case.title,
        "description": case.description,
        "category": case.category.value,
        "priority": case.priority.value,
        "stage": case.stage.value,
        "queue": case.queue.value if case.queue is not None else None,
        "owner": case.owner,
        "created_at": case.created_at.isoformat(),
        "updated_at": case.updated_at.isoformat(),
        "resolution": case.resolution.value if case.resolution is not None else None,
        "resolution_notes": case.resolution_notes,
        "history": [case_event_to_dict(event) for event in case.history],
    }
