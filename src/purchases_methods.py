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
    Inserts a new purchase into the database and its associated purchased
    items.
    Expects `purchase` to be a dict with at least 'user_id' and
    'payment_token'.
    Optionally, it can include an 'items' key, which should be a
    list of objects each containing
    'item_id' and 'quantity'.
    """
    try:
        with conn.cursor() as cur:
            # Insert into purchases table
            cur.execute(
                "INSERT INTO purchases (user_id, payment_token) VALUES \
                    (%s, %s) RETURNING id, user_id, payment_token;",
                (purchase["user_id"], purchase["payment_token"]),
            )
            new_purchase = cur.fetchone()
            purchase_id = new_purchase[0]

            # If there are items in the payload, insert them into
            # purchased_items table
            items = purchase.get("items")
            if items and isinstance(items, list):
                for item in items:
                    # Optionally, validate each item has both 'item_id'
                    # and 'quantity'
                    if "item_id" not in item or "quantity" not in item:
                        raise Exception(
                            "Each item must contain 'item_id' and 'quantity'"
                        )
                    cur.execute(
                        "INSERT INTO purchased_items (purchase_id, item_id, \
                            quantity) VALUES (%s, %s, %s);",
                        (purchase_id, item["item_id"], item["quantity"]),
                    )

            # Commit the transaction after both insertions
            conn.commit()

        # Prepare a response that includes the purchase details and
        # the inserted items (if any)
        response_body = {
            "purchase": {
                "id": new_purchase[0],
                "user_id": new_purchase[1],
                "payment_token": new_purchase[2],
            }
        }
        if items:
            response_body["items"] = items

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
