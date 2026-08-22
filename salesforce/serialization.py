"""JSON-safe serialization for the Salesforce reference models."""

from __future__ import annotations

from typing import Any

from salesforce.models import SalesforceCase, SalesforceCaseMilestone, SalesforceFeedItem


def salesforce_milestone_to_dict(milestone: SalesforceCaseMilestone) -> dict[str, Any]:
    return {
        "milestone_type": milestone.milestone_type,
        "target_date": milestone.target_date.isoformat(),
        "is_violated": milestone.is_violated,
        "completion_date": (
            milestone.completion_date.isoformat() if milestone.completion_date is not None else None
        ),
    }


def salesforce_feed_item_to_dict(item: SalesforceFeedItem) -> dict[str, Any]:
    return {
        "feed_item_id": item.feed_item_id,
        "parent_id": item.parent_id,
        "body": item.body,
        "created_by": item.created_by,
        "created_date": item.created_date.isoformat(),
        "feed_item_type": item.feed_item_type,
    }


def salesforce_case_to_dict(case: SalesforceCase) -> dict[str, Any]:
    return {
        "id": case.id,
        "case_number": case.case_number,
        "canonical_case_id": case.canonical_case_id,
        "subject": case.subject,
        "description": case.description,
        "priority": case.priority.value,
        "status": case.status.value,
        "is_closed": case.is_closed,
        "owner_id": case.owner_id,
        "queue_name": case.queue_name,
        "created_date": case.created_date.isoformat(),
        "last_modified_date": case.last_modified_date.isoformat(),
        "entitlement_name": case.entitlement_name,
        "milestones": [salesforce_milestone_to_dict(m) for m in case.milestones],
        "resolution_code": case.resolution_code,
        "resolution_notes": case.resolution_notes,
        "closed_date": case.closed_date.isoformat() if case.closed_date is not None else None,
    }
