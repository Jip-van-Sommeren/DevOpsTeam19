import json
import boto3
import os

# Initialize Step Functions client
sfn_client = boto3.client("stepfunctions")
STATE_MACHINE_ARN = os.environ.get("STATE_MACHINE_ARN")


def lambda_handler(event, context):
    # Extract data from the API request (e.g., body)
    http_method = event.get("httpMethod", "")
    if http_method == "PUT":
        try:
            body = json.loads(event.get("body", "{}"))
        except Exception as e:
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {
                        "message": "Invalid JSON in request body",
                        "error": str(e),
                    }
                ),
            }
        body["stock_operation"] = "deduct"
        state_machine_input = json.dumps({"data": body})

        # Start the execution of the state machine
        if STATE_MACHINE_ARN is not None:
            response = sfn_client.start_execution(
                stateMachineArn=STATE_MACHINE_ARN,
                input=state_machine_input,
            )
            return {
                "statusCode": 200,
                "body": json.dumps(
                    {
                        "message": "Saga triggered successfully",
                        "executionArn": response.get("executionArn"),
                    }
                ),
            }
        else:
            return {
                "statusCode": 500,
                "body": json.dumps(
                    {
                        "message": "STATE_MACHINE_ARN environment \
                            variable not set"
                    }
                ),
            }

    # If the request doesn't match any endpoint, return 404
    return {"statusCode": 404, "body": json.dumps({"message": "Not Found"})}
