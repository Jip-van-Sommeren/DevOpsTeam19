import json
from psycopg2.extras import RealDictCursor
from db_layer.db_connect import get_connection

conn = get_connection()


def get_items():
    """
    Retrieves a list of items from the database.
    """
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, name FROM items;")
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


def add_item(item):
    """
    Inserts a new item into the database.
    Expects `item` to be a dict with at least a 'name' key.
    """
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO items (name) VALUES (%s) RETURNING id, name;",
                (item["name"],),
            )
            new_item = cur.fetchone()
            conn.commit()
        return {
            "statusCode": 201,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(new_item),
        }
    except Exception as e:
        conn.rollback()
        print("Error adding item:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error adding item", "error": str(e)}
            ),
        }


def handler(event, context):
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


if __name__ == "__main__":

    print(
        handler(
            {
                "httpMethod": "POST",
                "resource": "/items",
                "body": json.dumps({"name": "New Item"}),
            },
            None,
        )
    )
