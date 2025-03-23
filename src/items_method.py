import json
import os
import boto3
from db_layer.db_connect import get_session
from db_layer.generate_s3_url import generate_presigned_url
from db_layer.basemodels import (
    Item,
)

s3_client = boto3.client("s3")
S3_BUCKET = os.environ.get("S3_BUCKET")


def get_items(event):
    """
    Retrieves a list of items from the database with pagination.
    Expects query string parameters "skip" and "limit" for pagination.
    Defaults: skip=0, limit=100.
    """
    session = get_session()
    try:
        query_params = event.get("queryStringParameters") or {}
        try:
            skip = int(query_params.get("skip", 0))
            limit = int(query_params.get("limit", 100))
        except ValueError:
            skip = 0
            limit = 100
        if limit > 1000:
            limit = 1000

        items = session.query(Item).offset(skip).limit(limit).all()
        # Convert each Item object to a dictionary.
        items_list = [
            {
                "id": item.id,
                "name": item.name,
                "description": item.description,
                "price": item.price,
                "image_url": generate_presigned_url(S3_BUCKET, item.s3_key),
            }
            for item in items
        ]
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(items_list),
        }
    except Exception as e:
        print("Error fetching items:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error fetching items", "error": str(e)}
            ),
        }
    finally:
        session.close()


def lambda_handler(event, context):
    """
    Main Lambda handler. Routes requests based on HTTP method.
    Assumes API Gateway is set up with Lambda proxy integration.
    """
    http_method = event.get("httpMethod", "")
    resource = event.get("resource", "")

    # Route for /items endpoint.
    if resource == "/items":
        if http_method == "GET":
            return get_items(event)
        http_method = event.get("httpMethod", "")
    resource = event.get("resource", "")

    # If the request doesn't match any endpoint, return 404.
    return {"statusCode": 404, "body": json.dumps({"message": "Not Found"})}
