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


def lambda_handler(event, context):
    """
    Main Lambda handler. Routes requests based on HTTP method.
    Assumes API Gateway is set up with Lambda proxy integration.
    """
    http_method = event.get("httpMethod", "")
    resource = event.get("resource", "")

    # Route for /reservations endpoint
    if resource == "/reservations" and http_method == "GET":
        return get_reservations()

    # If the request doesn't match any endpoint, return 404
    return {"statusCode": 404, "body": json.dumps({"message": "Not Found"})}
