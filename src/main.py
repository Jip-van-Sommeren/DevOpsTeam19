import json


def lambda_handler(event, context):
    """
    AWS Lambda handler for the hello_world function.
    Returns a simple JSON response with a 200 status code.
    """
    response = {"statusCode": 200, "body": json.dumps("Hello, world!")}
    return response


if __name__ == "__main__":
    # Simulate a Lambda event and context for local testing
    test_event = {}  # Customize as needed
    test_context = None  # You can leave this as None for basic testing

    result = lambda_handler(test_event, test_context)
    print("Lambda function result:")
    print(result)
