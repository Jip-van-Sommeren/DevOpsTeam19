import json
import boto3
import os

# Initialize Step Functions client
sfn_client = boto3.client("stepfunctions")


def lambda_handler(event, context):
    # Extract data from the API request (e.g., body)
    http_method = event.get("httpMethod", "")
    resource = event.get("resource", "")
    if resource == "/purchases" and http_method == "POST":
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
        state_machine_input = json.dumps({"purchaseData": body})

        # Start the execution of the state machine
        response = sfn_client.start_execution(
            stateMachineArn=os.environ.get("STATE_MACHINE_ARN"),
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

    # If the request doesn't match any endpoint, return 404
    return {"statusCode": 404, "body": json.dumps({"message": "Not Found"})}
