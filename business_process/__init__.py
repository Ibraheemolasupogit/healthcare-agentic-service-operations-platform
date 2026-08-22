"""Platform-neutral business process domain: canonical service operations model.

This package is the single source of truth for what a healthcare service
request is, what stage it is in, how it is prioritised, routed, and
resolved — independent of any CRM/SaaS platform. Future Dynamics 365 and
Salesforce adapters are expected to map onto these types, not redefine them.
See docs/business_process.md for the full model and its boundaries.
"""

from business_process.escalation import (
    EscalationReason,
    determine_escalation_reason,
    should_escalate,
)
from business_process.lifecycle import (
    ALLOWED_TRANSITIONS,
    InvalidLifecycleTransitionError,
    can_transition,
    validate_transition,
)
from business_process.models import Case, CaseEvent, ResolutionOutcome
from business_process.priority import PRIORITY_ORDER, Priority, priority_rank
from business_process.queues import (
    DEFAULT_QUEUE_OWNERS,
    ROUTING_RULES,
    Queue,
    assign_owner,
    route_category,
)
from business_process.serialization import case_event_to_dict, case_to_dict
from business_process.service import (
    classify_and_route,
    close_case,
    create_case,
    escalate_case,
    mark_pending,
    resolve_case,
    start_work,
    transition_case,
)
from business_process.sla import SLAStatus, SLATarget, evaluate_sla, get_sla_target
from business_process.taxonomy import CASE_LIFECYCLE_ORDER, CaseStage, ServiceCategory

__all__ = [
    "ALLOWED_TRANSITIONS",
    "CASE_LIFECYCLE_ORDER",
    "DEFAULT_QUEUE_OWNERS",
    "PRIORITY_ORDER",
    "ROUTING_RULES",
    "Case",
    "CaseEvent",
    "CaseStage",
    "EscalationReason",
    "InvalidLifecycleTransitionError",
    "Priority",
    "Queue",
    "ResolutionOutcome",
    "SLAStatus",
    "SLATarget",
    "ServiceCategory",
    "assign_owner",
    "can_transition",
    "case_event_to_dict",
    "case_to_dict",
    "classify_and_route",
    "close_case",
    "create_case",
    "determine_escalation_reason",
    "escalate_case",
    "evaluate_sla",
    "get_sla_target",
    "mark_pending",
    "priority_rank",
    "resolve_case",
    "route_category",
    "should_escalate",
    "start_work",
    "transition_case",
    "validate_transition",
]
