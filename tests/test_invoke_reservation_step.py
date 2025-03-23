import json
import os
import pytest
from unittest.mock import patch

from src.invoke_reservation_step import lambda_handler


def test_not_found():
    """
    Verify that an event not matching the /reservations POST endpoint returns a 404.
    """
    event = {
        "httpMethod": "GET",  # Incorrect HTTP method
        "resource": "/not_reservations",
    }
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert "Not Found" in body["message"]


@patch("src.invoke_reservation_step.sfn_client")
def test_state_machine_not_set(mock_sfn_client):
    """
    Verify that if STATE_MACHINE_ARN is not set, the function returns a 500 error.
    """
    # Remove the environment variable and override the module-level variable.
    os.environ.pop("STATE_MACHINE_ARN", None)
    from src import invoke_reservation_step

    invoke_reservation_step.STATE_MACHINE_ARN = None

    event = {
        "httpMethod": "POST",
        "resource": "/reservations",
        "body": json.dumps({"reservation": "data"}),
    }
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 500
    body = json.loads(response["body"])
    assert "STATE_MACHINE_ARN environment" in body["message"]


@patch("src.invoke_reservation_step.sfn_client")
def test_invalid_json_body(mock_sfn_client):
    """
    Verify that providing an invalid JSON body returns a 400 error.
    """
    from src import invoke_reservation_step

    invoke_reservation_step.STATE_MACHINE_ARN = "test-arn"

    event = {
        "httpMethod": "POST",
        "resource": "/reservations",
        "body": "invalid json",
    }
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Invalid JSON in request body" in body["message"]


@patch("src.invoke_reservation_step.sfn_client")
def test_saga_trigger_success(mock_sfn_client):
    """
    Verify that a valid POST request triggers the state machine successfully.
    """
    from src import invoke_reservation_step

    invoke_reservation_step.STATE_MACHINE_ARN = "test-arn"

    # Configure the mocked sfn_client to return a fake executionArn.
    fake_response = {"executionArn": "fake-execution-arn"}
    mock_sfn_client.start_execution.return_value = fake_response

    # Prepare a valid event payload.
    input_body = {"reservation": "data", "other_field": "value"}
    event = {
        "httpMethod": "POST",
        "resource": "/reservations",
        "body": json.dumps(input_body),
    }
    context = {}
    response = lambda_handler(event, context)

    # Check that a 200 response is returned.
    assert response["statusCode"] == 200
    resp_body = json.loads(response["body"])
    assert "Saga triggered successfully" in resp_body["message"]
    assert resp_body["executionArn"] == "fake-execution-arn"

    expected_input = json.dumps(
        {"data": {**input_body, "stock_operation": "deduct"}}
    )
    mock_sfn_client.start_execution.assert_called_once_with(
        stateMachineArn="test-arn",
        input=expected_input,
    )
