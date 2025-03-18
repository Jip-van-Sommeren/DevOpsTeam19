# import json
# from psycopg2.extras import RealDictCursor
# from db_layer.db_connect import get_connection

# conn = get_connection()


# def get_items(event):
#     """
#     Retrieves a list of items from the database with pagination.
#     Expects query string parameters "skip" and "limit" for pagination.
#     Defaults: skip=0, limit=100.
#     """
#     try:
#         query_params = event.get("queryStringParameters") or {}
#         try:
#             skip = int(query_params.get("skip", 0))
#             limit = int(query_params.get("limit", 100))
#         except ValueError:
#             skip = 0
#             limit = 100
#         if limit > 1000:
#             limit = 1000

#         with conn.cursor(cursor_factory=RealDictCursor) as cur:
#             cur.execute(
#                 "SELECT id, name, description FROM items OFFSET %s LIMIT %s;",
#                 (skip, limit),
#             )
#             items = cur.fetchall()

#         return {
#             "statusCode": 200,
#             "headers": {"Content-Type": "application/json"},
#             "body": json.dumps(items),
#         }
#     except Exception as e:
#         print("Error fetching items:", str(e))
#         return {
#             "statusCode": 500,
#             "body": json.dumps(
#                 {"message": "Error fetching items", "error": str(e)}
#             ),
#         }


# def add_item(item):
#     """
#     Inserts a new item into the database.
#     Expects `item` to be a dict with at least a 'name' key.
#     Optionally, it can include a 'description' key.
#     """
#     # Use a default description if not provided
#     try:
#         with conn.cursor() as cur:
#             cur.execute(
#                 "INSERT INTO items (name, description, price) VALUES \
#                     (%s, %s, %s) RETURNING id, name, description, price;",
#                 (item["name"], item["description"], item["price"]),
#             )
#             new_item = cur.fetchone()
#             conn.commit()
#         return {
#             "statusCode": 201,
#             "headers": {"Content-Type": "application/json"},
#             "body": json.dumps(new_item),
#         }
#     except Exception as e:
#         conn.rollback()
#         print("Error adding item:", str(e))
#         return {
#             "statusCode": 500,
#             "body": json.dumps(
#                 {"message": "Error adding item", "error": str(e)}
#             ),
#         }


# def lambda_handler(event, context):
#     """
#     Main Lambda handler. Routes requests based on HTTP method.
#     Assumes API Gateway is set up with Lambda proxy integration.
#     """
#     http_method = event.get("httpMethod", "")
#     resource = event.get("resource", "")

#     # Route for /items endpoint
#     if resource == "/items":
#         if http_method == "GET":
#             return get_items(event)
#         elif http_method == "POST":
#             # Expect the request body to contain JSON data for the new item
#             try:
#                 item = json.loads(event.get("body", "{}"))
#             except Exception as e:
#                 return {
#                     "statusCode": 400,
#                     "body": json.dumps(
#                         {
#                             "message": "Invalid JSON in request body",
#                             "error": str(e),
#                         }
#                     ),
#                 }
#             return add_item(item)

#     # If the request doesn't match any endpoint, return 404
#     return {"statusCode": 404, "body": json.dumps({"message": "Not Found"})}


import json
import os
import boto3
import base64
import uuid
from db_layer.db_connect import get_session
from db_layer.generate_s3_url import generate_presigned_url
from db_layer.basemodels import (
    Item,
)  # Assuming you have an ORM model named Item

# Initialize S3 client and get the bucket name from environment variables
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
            return get_items(
                event
            )  # Assumes you have a get_items function that accepts event

    # If the request doesn't match any endpoint, return 404.
    return {"statusCode": 404, "body": json.dumps({"message": "Not Found"})}
