import json
import os
from unittest.mock import patch

from src.invoke_reservation_wait import lambda_handler


@patch("src.invoke_reservation_wait.sfn_client")
def test_state_machine_not_set(mock_sfn_client):
    """
    When STATE_MACHINE_ARN is not set, the function should return a 500 error.
    """
    # Ensure the environment variable and module-level variable are not set.
    os.environ.pop("STATE_MACHINE_ARN", None)
    from src import invoke_reservation_wait

    invoke_reservation_wait.STATE_MACHINE_ARN = None

    event = {"data": {"key": "value"}}
    context = {}
    result = lambda_handler(event, context)

    assert result["statusCode"] == 500
    assert "STATE_MACHINE_ARN environment" in result["message"]


@patch("src.invoke_reservation_wait.sfn_client")
def test_saga_trigger_success(mock_sfn_client):
    """
    When STATE_MACHINE_ARN is set and a valid event is provided, the function
    should start the execution of the state machine and return a 200 response.
    """
    from src import invoke_reservation_wait

    invoke_reservation_wait.STATE_MACHINE_ARN = "test-arn"

    fake_response = {"executionArn": "fake-execution-arn"}
    mock_sfn_client.start_execution.return_value = fake_response

    input_data = {"foo": "bar"}
    event = {"data": input_data}
    context = {}
    result = lambda_handler(event, context)

    assert result["statusCode"] == 200
    assert result["executionArn"] == "fake-execution-arn"
    assert result["data"] == input_data

    expected_input = json.dumps({"data": input_data})
    mock_sfn_client.start_execution.assert_called_once_with(
        stateMachineArn="test-arn",
        input=expected_input,
    )
