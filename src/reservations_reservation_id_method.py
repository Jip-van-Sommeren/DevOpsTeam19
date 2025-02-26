import json
from db_layer.python.db_connect import (
    get_connection,
)  # Import the shared db module from the layer

conn = get_connection()


def update_reservation(reservation_id, payload):
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE reservations SET name = %s, description = %s WHERE id = %s RETURNING id, name, description;",
                (payload.get("name"), payload.get("description"), reservation_id),
            )
            updated_reservation = cur.fetchone()
            if not updated_reservation:
                return {
                    "statusCode": 404,
                    "body": json.dumps({"message": "reservation not found"}),
                }
            conn.commit()
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "id": updated_reservation[0],
                    "name": updated_reservation[1],
                    "description": updated_reservation[2],
                }
            ),
        }
    except Exception as e:
        conn.rollback()
        print("Error in update_reservation:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error updating reservation", "error": str(e)}
            ),
        }


def handler(event, context):
    """
    Main Lambda handler for the /reservations/{reservation_id} endpoint.
    Routes the request based on the HTTP method.
    """
    http_method = event.get("httpMethod", "")
    path_params = event.get("pathParameters") or {}
    reservation_id = path_params.get("reservation_id")

    if not reservation_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Missing reservation_id in path"}),
        }

    if http_method == "PUT":
        try:
            payload = json.loads(event.get("body", "{}"))
        except Exception as e:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Invalid JSON", "error": str(e)}),
            }
        return update_reservation(reservation_id, payload)
    else:
        return {
            "statusCode": 405,
            "body": json.dumps({"message": f"Method {http_method} not allowed"}),
        }
