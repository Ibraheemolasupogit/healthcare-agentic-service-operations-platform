"""Reference Dynamics 365 / Dataverse adapter for the canonical service operations model.

Pure, deterministic translation only — no SDK, no live tenant, no
credentials, no business-rule decisions. See docs/crm_schema_mapping.md and
`dynamics365/README.md`.
"""

from dynamics365.mapping import (
    DYNAMICS_NAME_TO_QUEUE,
    DYNAMICS_STATUS_TO_STAGE,
    DYNAMICS_TO_PRIORITY,
    PRIORITY_TO_DYNAMICS,
    QUEUE_TO_DYNAMICS_NAME,
    STAGE_TO_DYNAMICS_STATUS,
    UnsupportedDynamicsValueError,
    dynamics_priority_from,
    dynamics_queue_name_from,
    dynamics_status_from,
    priority_from_dynamics,
    queue_from_dynamics_name,
    stage_from_dynamics,
    to_dynamics_incident,
    to_dynamics_timeline,
)
from dynamics365.models import (
    DynamicsIncident,
    DynamicsIncidentResolution,
    DynamicsPriorityCode,
    DynamicsStateCode,
    DynamicsStatusReason,
    DynamicsTimelineEntry,
)
from dynamics365.serialization import (
    dynamics_incident_resolution_to_dict,
    dynamics_incident_to_dict,
    dynamics_timeline_entry_to_dict,
)

__all__ = [
    "DYNAMICS_NAME_TO_QUEUE",
    "DYNAMICS_STATUS_TO_STAGE",
    "DYNAMICS_TO_PRIORITY",
    "PRIORITY_TO_DYNAMICS",
    "QUEUE_TO_DYNAMICS_NAME",
    "STAGE_TO_DYNAMICS_STATUS",
    "DynamicsIncident",
    "DynamicsIncidentResolution",
    "DynamicsPriorityCode",
    "DynamicsStateCode",
    "DynamicsStatusReason",
    "DynamicsTimelineEntry",
    "UnsupportedDynamicsValueError",
    "dynamics_incident_resolution_to_dict",
    "dynamics_incident_to_dict",
    "dynamics_priority_from",
    "dynamics_queue_name_from",
    "dynamics_status_from",
    "dynamics_timeline_entry_to_dict",
    "priority_from_dynamics",
    "queue_from_dynamics_name",
    "stage_from_dynamics",
    "to_dynamics_incident",
    "to_dynamics_timeline",
]
