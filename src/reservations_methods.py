import json
from psycopg2.extras import RealDictCursor
from db_layer.db_connect import get_connection

conn = get_connection()

# Initialize an EventBridge client


def get_reservations(event):
    """
    Retrieves a list of reservations from the database with pagination.
    Expects query string parameters "skip" and "limit" for pagination.
    Defaults: skip=0, limit=100.
    """
    try:
        query_params = event.get("queryStringParameters") or {}
        try:
            skip = int(query_params.get("skip", 0))
            limit = int(query_params.get("limit", 100))
        except ValueError:
            skip = 0
            limit = 100
        if limit > 1000:
            limit = 1000

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, name FROM reservations OFFSET %s LIMIT %s;",
                (skip, limit),
            )
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
        return get_reservations(event)

    # If the request doesn't match any endpoint, return 404
    return {"statusCode": 404, "body": json.dumps({"message": "Not Found"})}
