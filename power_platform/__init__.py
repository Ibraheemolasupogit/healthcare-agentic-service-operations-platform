"""Power Platform automation architecture for the canonical service operations model.

Version-controlled, deterministic reference specifications only — no live
Power Platform environment, deployed flow, Dataverse connection, or
credential. Power Automate flow specs, a connector contract, an approval
pattern, and simulated automation evidence orchestrate the existing
`business_process` canonical domain and `dynamics365` adapter without
redefining any of their rules. See power_platform/README.md and
docs/architecture.md.
"""

from power_platform.approvals import (
    ApprovalDecision,
    ApprovalRecord,
    ApprovalRequest,
    ApprovalValidationError,
    build_example_approvals,
    validate_approval_record,
)
from power_platform.connector_spec import (
    ConnectorOperation,
    ConnectorOperationValidationError,
    validate_connector_operation,
)
from power_platform.connectors import CONNECTOR_OPERATIONS, CONNECTOR_OPERATIONS_BY_NAME
from power_platform.flow_validation import WorkflowValidationError, validate_workflow_spec
from power_platform.flows import (
    ALL_FLOWS,
    APPROVAL_FLOW,
    INTAKE_FLOW,
    RESOLUTION_NOTIFICATION_FLOW,
    SLA_MONITORING_FLOW,
)
from power_platform.workflow_spec import (
    AdapterOperation,
    CanonicalOperation,
    StepKind,
    TriggerType,
    WorkflowSpecification,
    WorkflowStep,
)

__all__ = [
    "ALL_FLOWS",
    "APPROVAL_FLOW",
    "CONNECTOR_OPERATIONS",
    "CONNECTOR_OPERATIONS_BY_NAME",
    "INTAKE_FLOW",
    "RESOLUTION_NOTIFICATION_FLOW",
    "SLA_MONITORING_FLOW",
    "AdapterOperation",
    "ApprovalDecision",
    "ApprovalRecord",
    "ApprovalRequest",
    "ApprovalValidationError",
    "CanonicalOperation",
    "ConnectorOperation",
    "ConnectorOperationValidationError",
    "StepKind",
    "TriggerType",
    "WorkflowSpecification",
    "WorkflowStep",
    "WorkflowValidationError",
    "build_example_approvals",
    "validate_approval_record",
    "validate_connector_operation",
    "validate_workflow_spec",
]
