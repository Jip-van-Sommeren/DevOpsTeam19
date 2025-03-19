import json
import boto3
import os

# Initialize Step Functions client
sfn_client = boto3.client("stepfunctions")
STATE_MACHINE_ARN = os.environ.get("STATE_MACHINE_ARN")


def lambda_handler(event, context):
    # Extract data from the API request (e.g., body)
    body = event.get("data", {})

    state_machine_input = json.dumps({"data": body})

    # Start the execution of the state machine
    if STATE_MACHINE_ARN is not None:
        response = sfn_client.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            input=state_machine_input,
        )
        return {
            "statusCode": 200,
            "executionArn": response.get("executionArn"),
            "data": body,
        }
    else:
        return {
            "statusCode": 500,
            "message": "STATE_MACHINE_ARN environment \
                        variable not set",
        }

    # If the request doesn't match any endpoint, return 404
