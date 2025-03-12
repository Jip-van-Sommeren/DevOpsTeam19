import json
from psycopg2.extras import execute_values, RealDictCursor
from db_layer.db_connect import get_connection

conn = get_connection()


def update_reservation_items(user_id, items):
    """
    Inserts reservation items into the reservation_items table.
    Returns the inserted rows.
    """
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Prepare the values for insertion.
            cur.execute(
                "INSERT INTO reservations (user_id, status) VALUES (%s, %s)  \
                    RETURNING id, user_id, status;",
                (user_id, "reserved"),
            )
            new_reservation = cur.fetchone()
            reservation_id = new_reservation[0]

            inserted_items = []
            if items:
                values = [
                    (reservation_id, item["item_id"], item["quantity"])
                    for item in items
                ]
                sql = """
                INSERT INTO reserved_items (reservation_id, item_id, quantity)
                VALUES %s
                RETURNING reservation_id, item_id, quantity;
                """
                execute_values(cur, sql, values)
                inserted_items = cur.fetchall()

                conn.commit()
                response_body = {
                    "reservation": {
                        "id": new_reservation[0],
                        "user_id": new_reservation[1],
                        "status": "reserved",
                    },
                    "items": inserted_items,
                }
            return {
                "statusCode": 201,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(response_body),
            }
    except Exception as e:
        conn.rollback()
        print("Error adding reservation:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error adding reservation", "error": str(e)}
            ),
        }


def lambda_handler(event, context):
    """
    Lambda function to update the reservation_items table.
    Expects an event with:
      - reservation_id: the ID of the reservation
      - items: a list of objects with 'item_id' and 'quantity'

    This function is meant to be invoked by a Step Functions state machine.
    """
    print("Received event:", event)

    try:
        # reservation_id = event.get("reservation_id")
        user_id = event.get("user_id")
        items = event.get("items", [])

        # Validate the input
        if not user_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Missing user_id in input"}),
            }
        if not items:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "No items provided to update"}),
            }

        # Update the reservation_items table
        update_reservation_items(user_id, items)
    except Exception as e:
        conn.rollback()
        print("Error updating purchased_items:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error updating purchased_items", "error": str(e)}
            ),
        }
