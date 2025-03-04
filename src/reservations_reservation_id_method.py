import json
from db_layer.db_connect import get_connection

conn = get_connection()


def get_reservation(reservation_id):
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, description FROM reservations \
                    WHERE id = %s;",
                (reservation_id,),
            )
            reservation = cur.fetchone()
        if reservation:
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(
                    {
                        "id": reservation[0],
                        "name": reservation[1],
                        "description": reservation[2],
                    }
                ),
            }
        else:
            return {
                "statusCode": 404,
                "body": json.dumps({"message": "reservation not found"}),
            }
    except Exception as e:
        print("Error in get_reservation:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error retrieving reservation", "error": str(e)}
            ),
        }


def delete_reservation(reservation_id):
    try:
        with conn.cursor() as cur:
            # Attempt to delete the reservation and return its details
            cur.execute(
                "DELETE FROM reservations WHERE id = %s RETURNING id, \
                    name, description;",
                (reservation_id,),
            )
            deleted_reservation = cur.fetchone()
            if not deleted_reservation:
                # If no row was deleted, the reservation does not exist
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
                    "id": deleted_reservation[0],
                    "name": deleted_reservation[1],
                    "description": deleted_reservation[2],
                }
            ),
        }
    except Exception as e:
        conn.rollback()
        print("Error in delete_reservation:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error deleting reservation", "error": str(e)}
            ),
        }


def update_reservation(reservation_id: str, payload: dict[str, str]) -> dict:
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE reservations SET name = %s, description = %s WHERE \
                    id = %s  RETURNING id, name, description;",
                (
                    payload.get("name"),
                    payload.get("description"),
                    reservation_id,
                ),
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


def lambda_handler(event, context):
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

    if http_method == "GET":
        return get_reservation(reservation_id)
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
        return delete_reservation(reservation_id)
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
        return update_reservation(reservation_id, payload)
    else:
        return {
            "statusCode": 405,
            "body": json.dumps(
                {"message": f"Method {http_method} not allowed"}
            ),
        }
