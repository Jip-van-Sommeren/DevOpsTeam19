import json
from db_layer.db_connect import get_connection
import boto3
import os

conn = get_connection()
sfn_client = boto3.client("stepfunctions")
STATE_MACHINE_ARN = os.environ.get("STATE_MACHINE_ARN")


def get_item(item_id, location_id):
    try:
        with conn.cursor() as cur:
            if location_id is None:
                cur.execute(
                    "SELECT id, quantity FROM item_stock WHERE item_id = %s;",
                    (item_id,),
                )
            else:
                cur.execute(
                    "SELECT id, quantity FROM item_stock WHERE item_id = %s \
                        AND location_id = %s;",
                    (item_id, location_id),
                )
            item = cur.fetchone()
        if item:
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(
                    {"id": item[0], "name": item[1], "description": item[2]}
                ),
            }
        else:
            return {
                "statusCode": 404,
                "body": json.dumps({"message": "Item not found"}),
            }
    except Exception as e:
        print("Error in get_item:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error retrieving item", "error": str(e)}
            ),
        }


def delete_item(item_id, location_id):
    try:
        with conn.cursor() as cur:
            # Attempt to delete the item and return its details
            if location_id is None:
                query = "DELETE FROM item_stock WHERE item_id = %s \
                    RETURNING id;"
                params = (item_id,)
            else:
                query = "DELETE FROM item_stock WHERE item_id = %s AND \
                    location_id = %s RETURNING id;"
                params = (item_id, location_id)
            cur.execute(
                query,
                params,
            )
            deleted_item = cur.fetchone()
            if not deleted_item:
                # If no row was deleted, the item does not exist
                return {
                    "statusCode": 404,
                    "body": json.dumps({"message": "Item not found"}),
                }
            conn.commit()
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "id": deleted_item[0],
                    "name": deleted_item[1],
                    "description": deleted_item[2],
                }
            ),
        }
    except Exception as e:
        conn.rollback()
        print("Error in delete_item:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error deleting item", "error": str(e)}
            ),
        }


def lambda_handler(event, context):
    """
    Main Lambda handler for the /items/{item_id} endpoint.
    Routes the request based on the HTTP method.
    """
    http_method = event.get("httpMethod", "")
    path_params = event.get("pathParameters") or {}
    item_id = path_params.get("item_id")
    query_params = event.get("queryStringParameters", {})
    location_id = query_params.get("location_id")

    if not item_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Missing item_id in path"}),
        }

    if http_method == "GET":
        return get_item(item_id, location_id)
    elif http_method == "DELETE":
        try:
            payload = json.loads(event.get("body", "{}"))
        except Exception as e:
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {"message": "Invalid JSON", "error": str(e)}
                ),
            }
        return delete_item(item_id, location_id)
    elif http_method == "PUT":
        try:
            payload = json.loads(event.get("body", "{}"))
        except Exception as e:
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {"message": "Invalid JSON", "error": str(e)}
                ),
            }
        payload["stock_operation"] = payload.get(
            "stock_operation", "overwrite"
        )
        payload["location_id"] = location_id
        state_machine_input = json.dumps({"data": payload})
        if STATE_MACHINE_ARN is not None:
            response = sfn_client.start_execution(
                stateMachineArn=STATE_MACHINE_ARN,
                input=state_machine_input,
            )
            return {
                "statusCode": 200,
                "body": json.dumps(
                    {
                        "message": "Update item triggered successfully",
                        "executionArn": response.get("executionArn"),
                    }
                ),
            }
    else:
        return {
            "statusCode": 405,
            "body": json.dumps(
                {"message": f"Method {http_method} not allowed"}
            ),
        }
