"""Tests for the Power Platform connector operation contract."""

import json
from dataclasses import replace

import pytest

import business_process
import dynamics365
from power_platform.connector_spec import (
    ConnectorOperationValidationError,
    validate_connector_operation,
)
from power_platform.connectors import CONNECTOR_OPERATIONS, CONNECTOR_OPERATIONS_BY_NAME

_EXPECTED_NAMES = {
    "create_case",
    "transition_case",
    "get_case",
    "evaluate_sla",
    "evaluate_escalation",
    "resolve_case",
    "list_service_categories",
    "retrieve_queue_assignment",
    "sync_dynamics_representation",
}


def test_connector_operations_match_expected_names():
    assert {op.name for op in CONNECTOR_OPERATIONS} == _EXPECTED_NAMES


def test_connector_operations_by_name_covers_every_operation():
    assert set(CONNECTOR_OPERATIONS_BY_NAME.keys()) == _EXPECTED_NAMES
    assert all(CONNECTOR_OPERATIONS_BY_NAME[op.name] is op for op in CONNECTOR_OPERATIONS)


@pytest.mark.parametrize("operation", CONNECTOR_OPERATIONS, ids=lambda op: op.name)
def test_every_connector_operation_validates(operation):
    validate_connector_operation(operation)  # must not raise


@pytest.mark.parametrize("operation", CONNECTOR_OPERATIONS, ids=lambda op: op.name)
def test_every_connector_operation_example_is_json_serializable(operation):
    json.dumps(operation.example_request)
    json.dumps(operation.example_response)


def test_operations_that_wrap_canonical_functions_resolve_on_business_process():
    for operation in CONNECTOR_OPERATIONS:
        if operation.wraps_canonical is not None:
            assert callable(getattr(business_process, operation.wraps_canonical, None)), (
                operation.name
            )


def test_operations_that_wrap_adapter_functions_resolve_on_dynamics365():
    for operation in CONNECTOR_OPERATIONS:
        if operation.wraps_adapter is not None:
            assert callable(getattr(dynamics365, operation.wraps_adapter, None)), operation.name


def test_get_case_and_list_service_categories_have_no_canonical_decision_wrapped():
    # Neither is backed by a persistence layer / decision function — documented via caveat.
    get_case = CONNECTOR_OPERATIONS_BY_NAME["get_case"]
    list_categories = CONNECTOR_OPERATIONS_BY_NAME["list_service_categories"]
    assert get_case.wraps_canonical is None
    assert get_case.caveat
    assert list_categories.wraps_canonical is None


def test_evaluate_sla_example_reflects_a_real_breach_for_the_escalated_fixture():
    operation = CONNECTOR_OPERATIONS_BY_NAME["evaluate_sla"]
    assert operation.example_request["case_id"] == "SR-CE-1002"
    assert operation.example_response["resolution_breached"] is True


def test_evaluate_escalation_example_reports_a_reason_for_the_escalated_fixture():
    operation = CONNECTOR_OPERATIONS_BY_NAME["evaluate_escalation"]
    assert operation.example_response["should_escalate"] is True
    assert operation.example_response["reason"]


def test_transition_case_example_shows_both_success_and_a_rejected_repeat():
    operation = CONNECTOR_OPERATIONS_BY_NAME["transition_case"]
    assert operation.example_response["case"]["stage"] == "In Progress"
    assert "InvalidLifecycleTransitionError" in operation.caveat


def test_list_service_categories_example_covers_all_six_categories():
    operation = CONNECTOR_OPERATIONS_BY_NAME["list_service_categories"]
    assert len(operation.example_response["categories"]) == 6


def test_retrieve_queue_assignment_returns_canonical_queue_value():
    operation = CONNECTOR_OPERATIONS_BY_NAME["retrieve_queue_assignment"]
    assert operation.example_response["queue"] == "Clinical Technology"
    assert operation.example_response["owner"] == "clinical-technology-team"


def test_sync_dynamics_representation_wraps_the_dynamics_adapter_not_canonical():
    operation = CONNECTOR_OPERATIONS_BY_NAME["sync_dynamics_representation"]
    assert operation.wraps_canonical is None
    assert operation.wraps_adapter == "to_dynamics_incident"


def test_idempotent_flag_matches_documented_expectations():
    assert CONNECTOR_OPERATIONS_BY_NAME["create_case"].idempotent is False
    assert CONNECTOR_OPERATIONS_BY_NAME["get_case"].idempotent is True
    assert CONNECTOR_OPERATIONS_BY_NAME["list_service_categories"].idempotent is True


def test_validate_connector_operation_rejects_incomplete_operation():
    broken = replace(CONNECTOR_OPERATIONS[0], description="")
    with pytest.raises(ConnectorOperationValidationError, match="description is required"):
        validate_connector_operation(broken)


def test_validate_connector_operation_rejects_missing_name():
    broken = replace(CONNECTOR_OPERATIONS[0], name="")
    with pytest.raises(ConnectorOperationValidationError, match="name is required"):
        validate_connector_operation(broken)


def test_validate_connector_operation_rejects_none_request_schema():
    broken = replace(CONNECTOR_OPERATIONS[0], request_schema=None)
    with pytest.raises(ConnectorOperationValidationError, match="request_schema is required"):
        validate_connector_operation(broken)


def test_validate_connector_operation_rejects_empty_response_schema():
    broken = replace(CONNECTOR_OPERATIONS[0], response_schema={})
    with pytest.raises(
        ConnectorOperationValidationError, match="response_schema must not be empty"
    ):
        validate_connector_operation(broken)


def test_validate_connector_operation_rejects_none_example_request():
    broken = replace(CONNECTOR_OPERATIONS[0], example_request=None)
    with pytest.raises(ConnectorOperationValidationError, match="example_request is required"):
        validate_connector_operation(broken)


def test_validate_connector_operation_rejects_none_example_response():
    broken = replace(CONNECTOR_OPERATIONS[0], example_response=None)
    with pytest.raises(ConnectorOperationValidationError, match="example_response is required"):
        validate_connector_operation(broken)


def test_validate_connector_operation_rejects_non_bool_idempotent():
    broken = replace(CONNECTOR_OPERATIONS[0], idempotent="yes")
    with pytest.raises(ConnectorOperationValidationError, match="idempotent must be a bool"):
        validate_connector_operation(broken)


def test_validate_connector_operation_rejects_non_bool_requires_correlation_id():
    broken = replace(CONNECTOR_OPERATIONS[0], requires_correlation_id="yes")
    with pytest.raises(
        ConnectorOperationValidationError, match="requires_correlation_id must be a bool"
    ):
        validate_connector_operation(broken)
