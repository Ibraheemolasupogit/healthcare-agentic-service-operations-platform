"""JSON-safe serialization for the Dynamics 365 reference models."""

from __future__ import annotations

from typing import Any

from dynamics365.models import DynamicsIncident, DynamicsIncidentResolution, DynamicsTimelineEntry


def dynamics_incident_resolution_to_dict(resolution: DynamicsIncidentResolution) -> dict[str, Any]:
    return {"subject": resolution.subject, "description": resolution.description}


def dynamics_timeline_entry_to_dict(entry: DynamicsTimelineEntry) -> dict[str, Any]:
    return {
        "annotationid": entry.annotationid,
        "regarding_incidentid": entry.regarding_incidentid,
        "subject": entry.subject,
        "notetext": entry.notetext,
        "createdon": entry.createdon.isoformat(),
        "createdby": entry.createdby,
    }


def dynamics_incident_to_dict(incident: DynamicsIncident) -> dict[str, Any]:
    return {
        "incidentid": incident.incidentid,
        "ticketnumber": incident.ticketnumber,
        "title": incident.title,
        "description": incident.description,
        "prioritycode": incident.prioritycode.value,
        "statecode": incident.statecode.value,
        "statuscode": incident.statuscode.value,
        "owning_team": incident.owning_team,
        "queue_name": incident.queue_name,
        "createdon": incident.createdon.isoformat(),
        "modifiedon": incident.modifiedon.isoformat(),
        "responsebyapplicable": (
            incident.responsebyapplicable.isoformat()
            if incident.responsebyapplicable is not None
            else None
        ),
        "resolvebyapplicable": (
            incident.resolvebyapplicable.isoformat()
            if incident.resolvebyapplicable is not None
            else None
        ),
        "sla_response_breached": incident.sla_response_breached,
        "sla_resolution_breached": incident.sla_resolution_breached,
        "resolution": (
            dynamics_incident_resolution_to_dict(incident.resolution)
            if incident.resolution is not None
            else None
        ),
    }
