import json
from psycopg2.extras import RealDictCursor
from db_layer.db_connect import get_connection

conn = get_connection()

# Initialize an EventBridge client


def get_purchases():
    """
    Retrieves a list of purchases from the database.
    """
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, name FROM purchases;")
            purchases = cur.fetchall()
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(purchases),
        }
    except Exception as e:
        print("Error fetching purchases:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error fetching purchases", "error": str(e)}
            ),
        }


def lambda_handler(event, context):
    """
    Main Lambda handler. Routes requests based on HTTP method.
    Assumes API Gateway is set up with Lambda proxy integration.
    """
    http_method = event.get("httpMethod", "")
    resource = event.get("resource", "")

    # Route for /purchases endpoint
    if resource == "/purchases" and http_method == "GET":
        return get_purchases()

    # If the request doesn't match any endpoint, return 404
    return {"statusCode": 404, "body": json.dumps({"message": "Not Found"})}
