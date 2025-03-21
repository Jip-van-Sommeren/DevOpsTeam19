import json
import os
import pytest
from unittest.mock import patch

# Import the Lambda handler from your module.
from src import invoke_item_step


def test_not_found():
    """
    Test that an event that doesn't match the /items POST endpoint returns a 404.
    """
    event = {
        "httpMethod": "GET",  # Wrong HTTP method
        "resource": "/not-items",
    }
    context = {}
    response = invoke_item_step.lambda_handler(event, context)
    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert "Not Found" in body["message"]


@patch("src.invoke_item_step.sfn_client")
def test_state_machine_not_set(mock_sfn_client):
    """
    Test that if the STATE_MACHINE_ARN environment variable is not set,
    the Lambda returns a 500 error.
    """
    # Remove the environment variable if present.
    os.environ.pop("STATE_MACHINE_ARN", None)

    event = {
        "httpMethod": "POST",
        "resource": "/items",
        "body": json.dumps(
            [
                {
                    "name": "Item One",
                    "description": "First item",
                    "price": 100,
                    "image_data": "base64string",
                }
            ]
        ),
    }
    context = {}
    response = invoke_item_step.lambda_handler(event, context)
    assert response["statusCode"] == 500
    body = json.loads(response["body"])
    assert "STATE_MACHINE_ARN environment" in body["message"]


@patch("src.invoke_item_step.sfn_client")
def test_invalid_json_body(mock_sfn_client):
    """
    Test that when an invalid JSON body is provided,
    the Lambda returns a 400 error.
    """
    os.environ["STATE_MACHINE_ARN"] = "test-arn"
    invoke_item_step.STATE_MACHINE_ARN = "test-arn"

    event = {
        "httpMethod": "POST",
        "resource": "/items",
        "body": "this-is-not-json",
    }
    context = {}
    response = invoke_item_step.lambda_handler(event, context)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Invalid JSON in request body" in body["message"]


@patch("src.invoke_item_step.sfn_client")
def test_saga_trigger_success(mock_sfn_client):
    """
    Test that with a valid POST request containing a list of items,
    the Lambda starts a Step Functions execution and returns a 200 response.

    The list of items is expected to have the following structure:

    {
      "required": [ "name", "description", "price"],
      "type": "object",
      "properties": {
        "id": { "type": "integer", "format": "int32" },
        "name": { "type": "string" },
        "description": { "type": "string" },
        "price": { "type": "integer", "format": "int32" },
        "image_data": { "type": "string" }
      }
    }
    """
    os.environ["STATE_MACHINE_ARN"] = "test-arn"
    invoke_item_step.STATE_MACHINE_ARN = "test-arn"

    # Configure the mocked sfn_client to return a fake executionArn.
    fake_response = {"executionArn": "fake-execution-arn"}
    mock_sfn_client.start_execution.return_value = fake_response

    # Prepare a valid event payload with a list of items.
    body_data = [
        {
            "name": "Item One",
            "description": "First item",
            "price": 100,
            "image_data": "base64string1",
        },
        {
            "name": "Item Two",
            "description": "Second item",
            "price": 200,
            "image_data": "base64string2",
        },
    ]
    event = {
        "httpMethod": "POST",
        "resource": "/items",
        "body": json.dumps(body_data),
    }
    context = {}
    response = invoke_item_step.lambda_handler(event, context)

    # Verify that the response contains the expected status and executionArn.
    assert response["statusCode"] == 200
    resp_body = json.loads(response["body"])
    assert "Saga triggered successfully" in resp_body["message"]
    assert resp_body["executionArn"] == "fake-execution-arn"

    # Verify that the state machine was started with the expected input.
    expected_input = json.dumps({"data": {"items": body_data}})
    mock_sfn_client.start_execution.assert_called_once_with(
        stateMachineArn="test-arn",
        input=expected_input,
    )
