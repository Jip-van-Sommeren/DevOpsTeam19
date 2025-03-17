import json
from db_layer.db_connect import get_connection
import os
import boto3

conn = get_connection()
sfn_client = boto3.client("stepfunctions")
STATE_MACHINE_ARN = os.environ.get("STATE_MACHINE_ARN")


def get_purchase(purchase_id):
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, user_id, payment_token FROM purchases \
                    WHERE id = %s;",
                (purchase_id,),
            )
            purchase = cur.fetchone()
        if purchase:
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(
                    {
                        "id": purchase[0],
                        "name": purchase[1],
                        "description": purchase[2],
                    }
                ),
            }
        else:
            return {
                "statusCode": 404,
                "body": json.dumps({"message": "purchase not found"}),
            }
    except Exception as e:
        print("Error in get_purchase:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error retrieving purchase", "error": str(e)}
            ),
        }


def delete_purchase(purchase_id):
    try:
        with conn.cursor() as cur:
            # First, delete rows in purchased_items that
            # reference this purchase_id
            cur.execute(
                "DELETE FROM purchased_items WHERE purchase_id = %s;",
                (purchase_id,),
            )
            # Then, delete the purchase and return its details
            cur.execute(
                "DELETE FROM purchases WHERE id = %s RETURNING id;",
                (purchase_id,),
            )
            deleted_purchase = cur.fetchone()
            if not deleted_purchase:
                # If no row was deleted, the purchase does not exist
                return {
                    "statusCode": 404,
                    "body": json.dumps({"message": "Purchase not found"}),
                }
            conn.commit()
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "id": deleted_purchase[0],
                    "name": deleted_purchase[1],
                    "description": deleted_purchase[2],
                }
            ),
        }
    except Exception as e:
        conn.rollback()
        print("Error in delete_purchase:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error deleting purchase", "error": str(e)}
            ),
        }


def update_purchase(purchase_id: str, payload: dict[str, str]) -> dict:
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE purchases SET user_id = %s, status = %s WHERE \
                    id = %s  RETURNING id, status;",
                (
                    payload.get("user_id"),
                    payload.get("status"),
                    purchase_id,
                ),
            )
            updated_purchase = cur.fetchone()
            if not updated_purchase:
                return {
                    "statusCode": 404,
                    "body": json.dumps({"message": "purchase not found"}),
                }
            conn.commit()
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "id": updated_purchase[0],
                    "name": updated_purchase[1],
                    "description": updated_purchase[2],
                }
            ),
        }
    except Exception as e:
        conn.rollback()
        print("Error in update_purchase:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error updating purchase", "error": str(e)}
            ),
        }


def lambda_handler(event, context):
    """
    Main Lambda handler for the /purchases/{purchase_id} endpoint.
    Routes the request based on the HTTP method.
    """
    http_method = event.get("httpMethod", "")
    path_params = event.get("pathParameters") or {}
    purchase_id = path_params.get("purchase_id")

    if not purchase_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Missing purchase_id in path"}),
        }

    if http_method == "GET":
        return get_purchase(purchase_id)
    elif http_method == "DELETE":
        try:
            _ = json.loads(event.get("body", "{}"))
        except Exception as e:
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {"message": "Invalid JSON", "error": str(e)}
                ),
            }
        return delete_purchase(purchase_id)
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
        return update_purchase(purchase_id, payload)

    else:
        return {
            "statusCode": 405,
            "body": json.dumps(
                {"message": f"Method {http_method} not allowed"}
            ),
        }
