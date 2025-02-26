import json
from db_layer.python.db_connect import get_connection

conn = get_connection()


def get_item_stock_for_location(item_id, location_id):
    """
    Query the database to retrieve stock information for a specific item at a specific location.
    Assumes there is an 'inventory' table with columns: item_id, location_id, and stock.
    """
    try:
        with conn.cursor() as cur:
            query = """
                SELECT stock 
                FROM inventory 
                WHERE item_id = %s AND location_id = %s;
            """
            cur.execute(query, (item_id, location_id))
            result = cur.fetchone()

        if result is None:
            return {
                "statusCode": 404,
                "body": json.dumps({"message": "Item or location not found"}),
            }

        stock = result[
            0
        ]  # Assuming the query returns a tuple with stock as first element

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {"item_id": item_id, "location_id": location_id, "stock": stock}
            ),
        }
    except Exception as e:

        print("Error fetching stock information:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error retrieving stock information", "error": str(e)}
            ),
        }


def lambda_handler(event, context):
    """
    Lambda handler for GET /items/{item_id}/location/{location_id}.
    Extracts item_id and location_id from the path parameters and returns the stock information.
    """
    # Ensure the HTTP method is GET
    if event.get("httpMethod", "") != "GET":
        return {
            "statusCode": 405,
            "body": json.dumps({"message": "Method not allowed"}),
        }

    # Extract dynamic parameters from the path
    path_params = event.get("pathParameters") or {}
    item_id = path_params.get("item_id")
    location_id = path_params.get("location_id")

    if not item_id or not location_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Missing item_id or location_id in path"}),
        }

    # Retrieve stock information for the given item and location
    return get_item_stock_for_location(item_id, location_id)
