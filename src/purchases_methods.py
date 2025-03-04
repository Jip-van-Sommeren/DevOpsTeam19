import json
from psycopg2.extras import RealDictCursor, execute_values
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
    Inserts a new purchase into the database and its associated purchased items.
    Expects `purchase` to be a dict with at least 'user_id' and 'payment_token'.
    Optionally, it can include an 'items' key, which should be a list of objects each containing
    'item_id' and 'quantity'.
    """
    try:
        with conn.cursor() as cur:
            # Insert into purchases table
            cur.execute(
                "INSERT INTO purchases (user_id, payment_token) VALUES (%s, %s) RETURNING id, user_id, payment_token;",
                (purchase["user_id"], purchase["payment_token"]),
            )
            new_purchase = cur.fetchone()
            purchase_id = new_purchase[0]

            items = purchase.get("items", [])
            inserted_items = []
            if items:
                values = [
                    (purchase_id, item["item_id"], item["quantity"])
                    for item in items
                ]
                sql = """
                INSERT INTO purchased_items (purchase_id, item_id, quantity)
                VALUES %s
                RETURNING purchase_id, item_id, quantity;
                """
                execute_values(cur, sql, values)
                inserted_items = cur.fetchall()

            conn.commit()

        response_body = {
            "purchase": {
                "id": new_purchase[0],
                "user_id": new_purchase[1],
                "payment_token": new_purchase[2],
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
