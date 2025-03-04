import json
from psycopg2.extras import RealDictCursor
from db_layer.db_connect import get_connection

conn = get_connection()


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


def add_purchase(purchase):
    """
    Inserts a new purchase into the database.
    Expects `purchase` to be a dict with at least a 'name' key.
    Optionally, it can include a 'description' key.
    """
    # Use a default description if not provided
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO purchases (name, description, price) VALUES \
                    (%s, %s, %s) RETURNING id, name, description, price;",
                (purchase["name"], purchase["description"], purchase["price"]),
            )
            new_purchase = cur.fetchone()
            conn.commit()
        return {
            "statusCode": 201,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(new_purchase),
        }
    except Exception as e:
        conn.rollback()
        print("Error adding purchase:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error adding purchase", "error": str(e)}
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
    if resource == "/purchases":
        if http_method == "GET":
            return get_purchases()
        elif http_method == "POST":
            # Expect the request body to contain JSON data for the new purchase
            try:
                purchase = json.loads(event.get("body", "{}"))
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
            return add_purchase(purchase)

    # If the request doesn't match any endpoint, return 404
    return {"statusCode": 404, "body": json.dumps({"message": "Not Found"})}
