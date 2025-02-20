import os
import json


def lambda_handler(event, context):
    """
    AWS Lambda handler for the hello_world function.
    Returns a simple JSON response with a 200 status code.
    """
    response = {"statusCode": 200, "body": json.dumps("Hello, world!")}
    return response
