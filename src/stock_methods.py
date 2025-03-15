import json
from psycopg2.extras import RealDictCursor, execute_values
from db_layer.db_connect import get_connection

conn = get_connection()

# Initialize EventBridge client.


def get_items(event):
    """
    Retrieves a list of items from the database with pagination.
    Expects query string parameters "skip" and "limit" for pagination.
    Defaults: skip=0, limit=100.
    """
    try:
        # Extract query parameters (if any)
        query_params = event.get("queryStringParameters") or {}
        try:
            skip = int(query_params.get("skip", 0))
            limit = int(query_params.get("limit", 100))
        except ValueError:
            skip = 0
            limit = 100
        if limit > 1000:
            limit = 1000
        location_id = query_params.get("location_id")
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if location_id is None:
                cur.execute(
                    "SELECT id, item_id, location_id, quantity FROM item_stock\
                        OFFSET %s LIMIT %s;",
                    (skip, limit),
                )
            else:
                cur.execute(
                    "SELECT id, item_id, location_id, quantity FROM item_stock\
                        WHERE location_id = %s OFFSET %s LIMIT %s;",
                    (location_id, skip, limit),
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
    Inserts multiple items into the item_stock table after publishing an event
    for validation.
    Expects `items` to be a list of dicts, each with 'item_id', 'location_id',
    and 'quantity'.
    This function publishes an event so that a separate Lambda can check if
    the provided IDs are valid.
    """
    try:

        with conn.cursor() as cur:
            values = [
                (item["item_id"], item["location_id"], item["quantity"])
                for item in items
            ]
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
    if resource == "/stock":
        if http_method == "GET":
            return get_items(event)
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
            return add_items(item)

    # If the request doesn't match any endpoint, return 404
    return {"statusCode": 404, "body": json.dumps({"message": "Not Found"})}
