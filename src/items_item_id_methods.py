import json
from db_layer.db_connect import get_connection

conn = get_connection()


def get_item(item_id):
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, description FROM items WHERE id = %s;",
                (item_id,),
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


def delete_item(item_id):
    try:
        with conn.cursor() as cur:
            # Attempt to delete the item and return its details
            cur.execute(
                "DELETE FROM items WHERE id = %s RETURNING  \
                    id, name, description;",
                (item_id,),
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


def update_item(item_id: str, payload: dict[str, str]) -> dict:
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE items SET name = %s, description = %s WHERE id = %s \
                    RETURNING id, name, description;",
                (payload.get("name"), payload.get("description"), item_id),
            )
            updated_item = cur.fetchone()
            if not updated_item:
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
                    "id": updated_item[0],
                    "name": updated_item[1],
                    "description": updated_item[2],
                }
            ),
        }
    except Exception as e:
        conn.rollback()
        print("Error in update_item:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error updating item", "error": str(e)}
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

    if not item_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Missing item_id in path"}),
        }

    if http_method == "GET":
        return get_item(item_id)
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
        return delete_item(item_id)
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
        return update_item(item_id, payload)
    else:
        return {
            "statusCode": 405,
            "body": json.dumps(
                {"message": f"Method {http_method} not allowed"}
            ),
        }
