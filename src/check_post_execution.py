import json
import boto3

sfn_client = boto3.client("stepfunctions")


def lambda_handler(event, context):
    execution_arn = event["queryStringParameters"].get("executionArn")

    if not execution_arn:
        return {
            "statusCode": 400,
            "body": json.dumps(
                {"message": "Missing 'executionArn' parameter"}
            ),
        }

    try:
        response = sfn_client.describe_execution(executionArn=execution_arn)

        status = response["status"]
        output = response.get("output")
        status_code = (
            output.get("data", {}).get("statusCode") if output else None
        )

        if status == "RUNNING":
            return {
                "statusCode": 200,
                "body": json.dumps(
                    {
                        "status": "RUNNING",
                        "message": "Execution still in progress",
                    }
                ),
            }
        elif status == "SUCCEEDED":
            return {
                "statusCode": status_code or 200,
                "body": json.dumps(
                    {"status": "SUCCEEDED", "result": json.loads(output)}
                ),
            }
        elif status == "FAILED" or status == "ABORTED":
            return {
                "statusCode": status_code or 400,
                "body": json.dumps(
                    {"status": "FAILED", "result": json.loads(output)}
                ),
            }
        else:
            return {
                "statusCode": 500,
                "body": json.dumps(
                    {
                        "status": status,
                        "message": "Execution failed or aborted",
                        "details": json.loads(output) if output else {},
                    }
                ),
            }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error checking execution", "error": str(e)}
            ),
        }
