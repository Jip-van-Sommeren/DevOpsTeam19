import json
from db_layer.db_connect import get_connection

conn = get_connection()


def get_location(location_id):
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, description FROM locations WHERE id = %s;",
                (location_id,),
            )
            location = cur.fetchone()
        if location:
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(
                    {
                        "id": location[0],
                        "name": location[1],
                        "description": location[2],
                    }
                ),
            }
        else:
            return {
                "statusCode": 404,
                "body": json.dumps({"message": "location not found"}),
            }
    except Exception as e:
        print("Error in get_location:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error retrieving location", "error": str(e)}
            ),
        }


def delete_location(location_id):
    try:
        with conn.cursor() as cur:
            # Attempt to delete the location and return its details
            cur.execute(
                "DELETE FROM locations WHERE id = %s RETURNING id, name, description;",
                (location_id,),
            )
            deleted_location = cur.fetchone()
            if not deleted_location:
                # If no row was deleted, the location does not exist
                return {
                    "statusCode": 404,
                    "body": json.dumps({"message": "location not found"}),
                }
            conn.commit()
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "id": deleted_location[0],
                    "name": deleted_location[1],
                    "description": deleted_location[2],
                }
            ),
        }
    except Exception as e:
        conn.rollback()
        print("Error in delete_location:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error deleting location", "error": str(e)}
            ),
        }


def update_location(location_id: str, payload: dict[str, str]) -> dict:
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE locations SET name = %s, description = %s WHERE id = %s \
                    RETURNING id, name, description;",
                (payload.get("name"), payload.get("description"), location_id),
            )
            updated_location = cur.fetchone()
            if not updated_location:
                return {
                    "statusCode": 404,
                    "body": json.dumps({"message": "location not found"}),
                }
            conn.commit()
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "id": updated_location[0],
                    "name": updated_location[1],
                    "description": updated_location[2],
                }
            ),
        }
    except Exception as e:
        conn.rollback()
        print("Error in update_location:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error updating location", "error": str(e)}
            ),
        }


def lambda_handler(event, context):
    """
    Main Lambda handler for the /locations/{location_id} endpoint.
    Routes the request based on the HTTP method.
    """
    http_method = event.get("httpMethod", "")
    path_params = event.get("pathParameters") or {}
    location_id = path_params.get("location_id")

    if not location_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Missing location_id in path"}),
        }

    if http_method == "GET":
        return get_location(location_id)
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
        return delete_location(location_id)
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
        return update_location(location_id, payload)
    else:
        return {
            "statusCode": 405,
            "body": json.dumps(
                {"message": f"Method {http_method} not allowed"}
            ),
        }
