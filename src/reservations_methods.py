import json
from psycopg2.extras import RealDictCursor
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
    Inserts a new reservation into the database.
    Expects `reservation` to be a dict with at least a 'name' key.
    Optionally, it can include a 'description' key.
    """
    # Use a default description if not provided
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO reservations (status, user_id) VALUES \
                    (%s, %s) RETURNING id, status, user_id;",
                (reservation["status"], reservation["user_id"]),
            )
            new_reservation = cur.fetchone()
            conn.commit()
        return {
            "statusCode": 201,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(new_reservation),
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
            # Expect the request body to contain JSON data for the new reservation
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
