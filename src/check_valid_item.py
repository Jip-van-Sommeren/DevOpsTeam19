import json
from psycopg2.extras import RealDictCursor
from db_layer.db_connect import get_connection

conn = get_connection()


def is_item_valid(item_id):
    """
    Checks if the provided item_id exists in the items table.
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT id FROM items WHERE id = %s;", (item_id,))
        return cur.fetchone() is not None


def lambda_handler(event, context):
    """
    Lambda function that listens for an 'ItemValidation' event and checks the
    validity of item_id and location_id.
    Expects the event detail to contain an 'action' key equal to
    'validate_items' and an 'items' array.
    """
    print("Received event:", event)
    try:
        detail = event.get("detail", {})
        if isinstance(detail, str):
            detail = json.loads(detail)

        if detail.get("action") != "validate_items":
            print("Event not relevant for validation.")
            return {
                "result": "skipped",
                "message": "Event not relevant for item validation.",
            }

        items = detail.get("items", [])
        invalid_items = []

        for item in items:
            if not is_item_valid(item.get("item_id")):
                invalid_items.append(
                    {
                        "item_id": item.get("item_id"),
                        "error": "Invalid item_id",
                    }
                )

        if invalid_items:
            print("Validation errors found:", invalid_items)
            # You could trigger a compensating action or alert here if needed.
        else:
            print("All items are valid.")

        return {
            "result": "validation_complete",
            "invalid_items": invalid_items,
        }

    except Exception as e:
        print("Error during validation:", str(e))
        return {"result": "error", "error": str(e)}
