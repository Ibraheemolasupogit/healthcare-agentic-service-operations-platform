"""Reference Salesforce Service Cloud adapter for the canonical service operations model.

Pure, deterministic translation only — no SDK/API client, no live org, no
credentials, no business-rule decisions. See docs/crm_schema_mapping.md and
`salesforce/README.md`.
"""

from salesforce.mapping import (
    PRIORITY_TO_SALESFORCE,
    QUEUE_TO_SALESFORCE_NAME,
    SALESFORCE_NAME_TO_QUEUE,
    SALESFORCE_STATUS_TO_STAGE,
    SALESFORCE_TO_PRIORITY,
    STAGE_TO_SALESFORCE_STATUS,
    UnsupportedSalesforceValueError,
    priority_from_salesforce,
    queue_from_salesforce_name,
    salesforce_priority_from,
    salesforce_queue_name_from,
    salesforce_status_from,
    stage_from_salesforce,
    to_salesforce_case,
    to_salesforce_feed,
)
from salesforce.models import (
    SalesforceCase,
    SalesforceCaseMilestone,
    SalesforceFeedItem,
    SalesforcePriority,
    SalesforceStatus,
)
from salesforce.serialization import (
    salesforce_case_to_dict,
    salesforce_feed_item_to_dict,
    salesforce_milestone_to_dict,
)

__all__ = [
    "PRIORITY_TO_SALESFORCE",
    "QUEUE_TO_SALESFORCE_NAME",
    "SALESFORCE_NAME_TO_QUEUE",
    "SALESFORCE_STATUS_TO_STAGE",
    "SALESFORCE_TO_PRIORITY",
    "STAGE_TO_SALESFORCE_STATUS",
    "SalesforceCase",
    "SalesforceCaseMilestone",
    "SalesforceFeedItem",
    "SalesforcePriority",
    "SalesforceStatus",
    "UnsupportedSalesforceValueError",
    "priority_from_salesforce",
    "queue_from_salesforce_name",
    "salesforce_case_to_dict",
    "salesforce_feed_item_to_dict",
    "salesforce_milestone_to_dict",
    "salesforce_priority_from",
    "salesforce_queue_name_from",
    "salesforce_status_from",
    "stage_from_salesforce",
    "to_salesforce_case",
    "to_salesforce_feed",
]
