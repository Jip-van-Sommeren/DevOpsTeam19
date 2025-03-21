import json
import os
import pytest
from unittest.mock import patch

# Import the lambda handler from your module.
from src.invoke_purchase_step import lambda_handler


def test_not_found():
    """
    Verify that an event not matching the /purchases POST endpoint returns 404.
    """
    event = {
        "httpMethod": "GET",  # Wrong HTTP method
        "resource": "/not_purchases",
    }
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert "Not Found" in body["message"]


@patch("src.invoke_purchase_step.sfn_client")
def test_state_machine_not_set(mock_sfn_client):
    """
    Verify that when the STATE_MACHINE_ARN is not set,
    the function returns a 500 error.
    """
    # Clear the environment variable and override the module global.
    os.environ.pop("STATE_MACHINE_ARN", None)
    # Overwrite the module-level variable.
    from src import invoke_purchase_step

    invoke_purchase_step.STATE_MACHINE_ARN = None

    event = {
        "httpMethod": "POST",
        "resource": "/purchases",
        "body": json.dumps({"item": "test"}),
    }
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 500
    body = json.loads(response["body"])
    assert "STATE_MACHINE_ARN environment" in body["message"]


@patch("src.invoke_purchase_step.sfn_client")
def test_invalid_json_body(mock_sfn_client):
    """
    Verify that an invalid JSON body causes a 400 response.
    """
    # Ensure the module-level STATE_MACHINE_ARN is set.
    from src import invoke_purchase_step

    invoke_purchase_step.STATE_MACHINE_ARN = "test-arn"

    event = {
        "httpMethod": "POST",
        "resource": "/purchases",
        "body": "invalid json",
    }
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Invalid JSON in request body" in body["message"]


@patch("src.invoke_purchase_step.sfn_client")
def test_saga_trigger_success(mock_sfn_client):
    """
    Verify that a valid POST request triggers the state machine successfully.
    """
    from src import invoke_purchase_step

    # Set the module-level variable.
    invoke_purchase_step.STATE_MACHINE_ARN = "test-arn"

    # Configure the mocked sfn_client to return a fake executionArn.
    fake_response = {"executionArn": "fake-execution-arn"}
    mock_sfn_client.start_execution.return_value = fake_response

    # Prepare a valid input body.
    input_body = {"item": "test"}
    event = {
        "httpMethod": "POST",
        "resource": "/purchases",
        "body": json.dumps(input_body),
    }
    context = {}
    response = lambda_handler(event, context)

    # Verify a 200 response and correct message.
    assert response["statusCode"] == 200
    resp_body = json.loads(response["body"])
    assert "Saga triggered successfully" in resp_body["message"]
    assert resp_body["executionArn"] == "fake-execution-arn"

    # Verify that the state machine was started with the expected input.
    expected_input = json.dumps(
        {"data": {**input_body, "stock_operation": "deduct"}}
    )
    mock_sfn_client.start_execution.assert_called_once_with(
        stateMachineArn="test-arn",
        input=expected_input,
    )
