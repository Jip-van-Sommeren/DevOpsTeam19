import json
import pytest
from unittest.mock import patch

from src.check_post_execution import lambda_handler


@patch("src.check_post_execution.sfn_client")
def test_missing_executionArn(mock_sfn_client):
    event = {"queryStringParameters": {}}
    context = {}
    result = lambda_handler(event, context)
    assert result["statusCode"] == 400
    body = json.loads(result["body"])
    assert "Missing 'executionArn' parameter" in body["message"]


@patch("src.check_post_execution.sfn_client")
def test_running_execution(mock_sfn_client):
    # Setup: describe_execution returns a RUNNING status with no output.
    mock_sfn_client.describe_execution.return_value = {
        "status": "RUNNING",
        "output": None,
    }
    event = {"queryStringParameters": {"executionArn": "test-arn"}}
    context = {}
    result = lambda_handler(event, context)
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["status"] == "RUNNING"
    assert "Execution still in progress" in body["message"]


@patch("src.check_post_execution.sfn_client")
def test_succeeded_execution_without_statusCode(mock_sfn_client):
    # Setup: SUCCEEDED execution without a statusCode in the output.
    output = json.dumps({"result": "success"})
    mock_sfn_client.describe_execution.return_value = {
        "status": "SUCCEEDED",
        "output": output,
    }
    event = {"queryStringParameters": {"executionArn": "test-arn"}}
    context = {}
    result = lambda_handler(event, context)
    # When no statusCode is provided in the output, defaults to 200.
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["status"] == "SUCCEEDED"
    assert body["result"] == json.loads(output)


@patch("src.check_post_execution.sfn_client")
def test_succeeded_execution_with_statusCode(mock_sfn_client):
    # Setup: SUCCEEDED execution with a statusCode provided in the output.
    output = json.dumps({"result": "success", "statusCode": 201})
    mock_sfn_client.describe_execution.return_value = {
        "status": "SUCCEEDED",
        "output": output,
    }
    event = {"queryStringParameters": {"executionArn": "test-arn"}}
    context = {}
    result = lambda_handler(event, context)
    # Expect the provided statusCode 201 to be used.
    assert result["statusCode"] == 201
    body = json.loads(result["body"])
    assert body["status"] == "SUCCEEDED"
    assert body["result"] == json.loads(output)


@patch("src.check_post_execution.sfn_client")
def test_failed_execution(mock_sfn_client):
    # Setup: FAILED execution with no statusCode in the output.
    output = json.dumps({"error": "failure occurred"})
    mock_sfn_client.describe_execution.return_value = {
        "status": "FAILED",
        "output": output,
    }
    event = {"queryStringParameters": {"executionArn": "test-arn"}}
    context = {}
    result = lambda_handler(event, context)
    # For FAILED without a statusCode, default is 400.
    assert result["statusCode"] == 400
    body = json.loads(result["body"])
    assert body["status"] == "FAILED"
    assert body["result"] == json.loads(output)


@patch("src.check_post_execution.sfn_client")
def test_unknown_status(mock_sfn_client):
    # Setup: Return an unknown status to test the default error case.
    output = json.dumps({"info": "some details"})
    mock_sfn_client.describe_execution.return_value = {
        "status": "UNKNOWN",
        "output": output,
    }
    event = {"queryStringParameters": {"executionArn": "test-arn"}}
    context = {}
    result = lambda_handler(event, context)
    # For unknown status, expect a 500 response.
    assert result["statusCode"] == 500
    body = json.loads(result["body"])
    assert body["status"] == "UNKNOWN"
    assert "Execution failed or aborted" in body["message"]


@patch("src.check_post_execution.sfn_client")
def test_exception_handling(mock_sfn_client):
    # Setup: Force describe_execution to raise an Exception.
    mock_sfn_client.describe_execution.side_effect = Exception("Test error")
    event = {"queryStringParameters": {"executionArn": "test-arn"}}
    context = {}
    result = lambda_handler(event, context)
    assert result["statusCode"] == 500
    body = json.loads(result["body"])
    assert "Error checking execution" in body["message"]
    assert "Test error" in body["error"]
