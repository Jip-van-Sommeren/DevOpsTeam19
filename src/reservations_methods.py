import json
from psycopg2.extras import RealDictCursor, execute_values
from db_layer.db_connect import get_connection

conn = get_connection()


def get_reservations():
    """
    Retrieves a list of reservations from the database.
    """
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, status FROM reservations;")
            reservations = cur.fetchall()
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(reservations),
        }
    except Exception as e:
        print("Error fetching reservations:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error fetching reservations", "error": str(e)}
            ),
        }


def add_reservation(reservation):
    """
    Inserts a new reservation into the database and its associated reservationd items.
    Expects `reservation` to be a dict with at least 'user_id' and 'payment_token'.
    Optionally, it can include an 'items' key, which should be a list of objects each containing
    'item_id' and 'quantity'.
    """
    try:
        with conn.cursor() as cur:
            # Insert into reservations table
            cur.execute(
                "INSERT INTO reservations (user_id, status) VALUES (%s, %s) RETURNING id, user_id, status;",
                (reservation["user_id"], "reserved"),
            )
            new_reservation = cur.fetchone()
            reservation_id = new_reservation[0]

            items = reservation.get("items", [])
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
    Main Lambda handler. Routes requests based on HTTP method.
    Assumes API Gateway is set up with Lambda proxy integration.
    """
    http_method = event.get("httpMethod", "")
    resource = event.get("resource", "")

    # Route for /reservations endpoint
    if resource == "/reservations":
        if http_method == "GET":
            return get_reservations()
        elif http_method == "POST":
            # Expect the request body to contain JSON data for
            # the new reservation
            try:
                reservation = json.loads(event.get("body", "{}"))
            except Exception as e:
                return {
                    "statusCode": 400,
                    "body": json.dumps(
                        {
                            "message": "Invalid JSON in request body",
                            "error": str(e),
                        }
                    ),
                }
            # Check for the required user_id field
            if "user_id" not in reservation:
                return {
                    "statusCode": 400,
                    "body": json.dumps(
                        {"message": "Missing required field: user_id"}
                    ),
                }
            return add_reservation(reservation)

    # If the request doesn't match any endpoint, return 404
    return {"statusCode": 404, "body": json.dumps({"message": "Not Found"})}
