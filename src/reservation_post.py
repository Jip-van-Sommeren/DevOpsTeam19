from psycopg2.extras import execute_values, RealDictCursor
from db_layer.db_connect import get_connection

conn = get_connection()


def update_reservation_items(user_id, items):
    """
    Inserts a new reservation into the reservations table and associated items
    into reserved_items.
    Returns a dict with the reservation details and inserted items.
    """
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Insert into reservations table and return the new reservation.
            cur.execute(
                "INSERT INTO reservations (user_id, status) VALUES (%s, %s)\
                    RETURNING id, user_id, status;",
                (user_id, "reserved"),
            )
            new_reservation = cur.fetchone()
            reservation_id = new_reservation[
                "id"
            ]  # Assuming the column is named 'id'

            inserted_items = []
            if items:
                values = [
                    (reservation_id, item["item_id"], item["quantity"])
                    for item in items
                ]
                sql = """
                INSERT INTO reserved_items (reservation_id, item_id,
                location_id, quantity)
                VALUES %s
                RETURNING reservation_id, item_id, location_id, quantity;
                """
                execute_values(cur, sql, values)
                inserted_items = cur.fetchall()

            conn.commit()
            # Return the reservation details that will be passed along to
            # the next step.
            response_data = {
                "reservation": {
                    "id": reservation_id,
                    "user_id": new_reservation["user_id"],
                    "status": new_reservation["status"],
                },
                "items": inserted_items,
            }
            return response_data
    except Exception as e:
        conn.rollback()
        print("Error adding reservation:", str(e))
        raise e  # Raise the exception to let Step Functions catch it if needed


def lambda_handler(event, context):
    """
    Lambda function to update reservation items.
    Expects an event with:
      - data.user_id: the ID of the user making the reservation
      - data.items: a list of objects with 'item_id' and 'quantity'

    Returns the reservation data that can be passed to the next state in
    the state machine.
    """
    print("Received event:", event)

    try:
        data = event.get("data", {})
        user_id = data.get("user_id")
        items = data.get("items", [])

        # Validate the input
        if not user_id:
            raise ValueError("Missing user_id in input")
        if not items:
            raise ValueError("No items provided to update")

        # Update the reservation items and get the response data.
        response_data = update_reservation_items(user_id, items)
        # Directly return the response_data so the state machine receives it.
        return response_data

    except Exception as e:
        conn.rollback()
        print("Error updating reservation items:", str(e))
        # Return an error structure. Alternatively, you can let the error
        # propagate to trigger a Catch in the state machine.
        raise e
