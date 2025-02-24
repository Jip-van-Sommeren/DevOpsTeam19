import json
from db_layer import db  # Import our shared db module from the layer

# Create a global connection to be reused in warm invocations
conn = db.get_connection()


def purchase_item(item_id, purchase_data):
    """
    Handles the purchase operation for an item.
    Inserts a new record into a 'purchases' table.
    """
    try:
        with conn.cursor() as cur:
            # Insert a new purchase record. Adjust the SQL as needed for your schema.
            cur.execute(
                "INSERT INTO purchases (item_id, payment_token) VALUES (%s, %s) RETURNING id;",
                (item_id, purchase_data.get("payment_token")),
            )
            purchase_id = cur.fetchone()[0]
            conn.commit()

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {"message": "Item purchased successfully", "purchase_id": purchase_id}
            ),
        }
    except Exception as e:
        conn.rollback()
        print("Error purchasing item:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Error purchasing item", "error": str(e)}),
        }


def lambda_handler(event, context):
    """
    Lambda handler for POST /items/{item_id}/purchase.
    Expects a JSON body with purchase details (e.g., payment_token).
    """
    # Only allow POST
    if event.get("httpMethod", "") != "POST":
        return {
            "statusCode": 405,
            "body": json.dumps({"message": "Method not allowed"}),
        }

    # Extract the item_id from the path parameters
    path_params = event.get("pathParameters") or {}
    item_id = path_params.get("item_id")
    if not item_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Missing item_id in path"}),
        }

    # Parse the request body for purchase data
    try:
        purchase_data = json.loads(event.get("body", "{}"))
    except Exception as e:
        return {
            "statusCode": 400,
            "body": json.dumps(
                {"message": "Invalid JSON in request body", "error": str(e)}
            ),
        }

    # Optionally, you can read additional headers if needed:
    # auth_token = event.get("headers", {}).get("Authorization")

    # Process the purchase
    return purchase_item(item_id, purchase_data)
