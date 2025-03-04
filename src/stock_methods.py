import json
from psycopg2.extras import RealDictCursor, execute_values
from db_layer.db_connect import get_connection


conn = get_connection()


def get_items():
    """
    Retrieves a list of items from the database.
        id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL REFERENCES items(id),
    location_id INTEGER NOT NULL REFERENCES location(id),
    quantity INTEGER NOT NULL DEFAULT 0
    """
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, item_id, location_id, quantity FROM item_stock;"
            )
            items = cur.fetchall()
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(items),
        }
    except Exception as e:
        print("Error fetching items:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error fetching items", "error": str(e)}
            ),
        }


def add_items(items):
    """
    Inserts multiple items into the item_stock table.
    Expects `items` to be a list of dicts, each with 'item_id', 'location_id', and 'quantity'.
    Returns the inserted rows.
    """
    try:
        with conn.cursor() as cur:
            # Create a list of tuples containing the values for each item
            values = [
                (item["item_id"], item["location_id"], item["quantity"])
                for item in items
            ]
            # Build the SQL query using execute_values to perform a bulk insert
            sql = """
                INSERT INTO item_stock (item_id, location_id, quantity)
                VALUES %s
                RETURNING id, item_id, location_id, quantity;
            """
            execute_values(cur, sql, values)
            inserted_items = cur.fetchall()
            conn.commit()
        return {
            "statusCode": 201,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(inserted_items),
        }
    except Exception as e:
        conn.rollback()
        print("Error adding items:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error adding items", "error": str(e)}
            ),
        }


def lambda_handler(event, context):
    """
    Main Lambda handler. Routes requests based on HTTP method.
    Assumes API Gateway is set up with Lambda proxy integration.
    """
    http_method = event.get("httpMethod", "")
    resource = event.get("resource", "")

    # Route for /items endpoint
    if resource == "/items":
        if http_method == "GET":
            return get_items()
        elif http_method == "POST":
            # Expect the request body to contain JSON data for the new item
            try:
                item = json.loads(event.get("body", "{}"))
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
            return add_item(item)

    # If the request doesn't match any endpoint, return 404
    return {"statusCode": 404, "body": json.dumps({"message": "Not Found"})}
