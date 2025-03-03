import json
from db_layer.db_connect import get_connection

conn = get_connection()


def reserve_item(item_id, reservation_data):
    """
    Inserts a new reservation record for the given item.
    Expects reservation_data to include at least 'user_id' and
    'reservation_details' (or any other required fields).
    """
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO reservations (item_id,
                    user_id, status)
                VALUES (%s, %s, %s)
                RETURNING id;
                """,
                (
                    item_id,
                    reservation_data.get("user_id"),
                    reservation_data.get("status"),
                ),
            )
            reservation_id = cur.fetchone()[0]
            conn.commit()

        return {
            "statusCode": 201,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "message": "Reservation created successfully",
                    "reservation_id": reservation_id,
                }
            ),
        }
    except Exception as e:
        conn.rollback()
        print("Error reserving item:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error reserving item", "error": str(e)}
            ),
        }


def lambda_handler(event, context):
    """
    Lambda handler for POST /items/{item_id}/reservations.
    Expects a JSON body containing reservation details.
    """
    # Enforce POST method only
    # TODO: Add GET Method
    if event.get("httpMethod", "") != "POST":
        return {
            "statusCode": 405,
            "body": json.dumps({"message": "Method not allowed"}),
        }

    # Extract the dynamic item_id from path parameters
    path_params = event.get("pathParameters") or {}
    item_id = path_params.get("item_id")
    if not item_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Missing item_id in path"}),
        }

    # Parse the JSON request body
    try:
        reservation_data = json.loads(event.get("body", "{}"))
    except Exception as e:
        return {
            "statusCode": 400,
            "body": json.dumps(
                {"message": "Invalid JSON in request body", "error": str(e)}
            ),
        }

    # Process the reservation
    return reserve_item(item_id, reservation_data)
