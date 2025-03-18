import json
import os
import boto3
import base64
import uuid
from db_layer.db_connect import get_session
from db_layer.basemodels import (
    Item,
)  # Assuming you have an ORM model named Item

# Initialize S3 client and get the bucket name from environment variables
s3_client = boto3.client("s3", region_name="eu-north-1")
S3_BUCKET = os.environ.get("S3_BUCKET")


def add_items(items):
    """
    Inserts multiple new items into the database.
    Expects `items` to be a list of dicts, each with at least 'name' and 'price'.
    Optionally, each item can include a 'description' key and a base64-encoded 'image_data'.
    If image_data is provided, the image is uploaded to S3 and its key is added to the response.
    """
    session = get_session()
    added_items = []

    try:
        for item in items:

            s3_key = None
            if "image_data" in item:
                image_data = base64.b64decode(item["image_data"])
                s3_key = f"items/item_{uuid.uuid4().hex}.jpg"
                s3_client.put_object(
                    Bucket=S3_BUCKET,
                    Key=s3_key,
                    Body=image_data,
                    ContentType="image/jpeg",
                )
            if s3_key:
                new_item = Item(
                    name=item["name"],
                    description=item["description"],
                    price=item["price"],
                    s3_key=s3_key,
                )
            else:
                new_item = Item(
                    name=item["name"],
                    description=["description"],
                    price=item["price"],
                )
            session.add(new_item)
            session.commit()
            session.refresh(new_item)

            response_item = {
                "id": new_item.id,
                "name": new_item.name,
                "description": new_item.description,
                "price": new_item.price,
            }
            if s3_key:
                response_item["s3_key"] = s3_key

            added_items.append(response_item)

        return added_items
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def lambda_handler(event, context):
    """
    Main Lambda handler. Routes requests based on HTTP method.
    Assumes API Gateway is set up with Lambda proxy integration.
    """

    try:
        # Expect the request body to contain JSON data for the new item.
        items = event.get("data", "{}").get("items")
        if not isinstance(items, list):
            return {
                "statusCode": 400,
                "body": {
                    "message": "Invalid JSON in request body",
                    "error": "Expected 'items' to be a list",
                },
            }
        added_items = add_items(items)
        return {"added_items": added_items, "statusCode": 201}
    except Exception as e:
        raise e
