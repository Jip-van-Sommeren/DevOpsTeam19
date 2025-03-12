import json
from psycopg2.extras import RealDictCursor
from db_layer.db_connect import get_connection

conn = get_connection()


def is_location_valid(location_id):
    """
    Checks if the provided location_id exists in the locations table.
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT id FROM locations WHERE id = %s;", (location_id,))
        return cur.fetchone() is not None


def lambda_handler(event, context):
    """
    Lambda function that validates location_id values.
    Expects the event detail to contain an 'action' key equal to
    'validate_items'
    and an 'items' array.

    Returns a JSON object with a list of any invalid items.
    This output is meant to be consumed by a Step Functions state machine.
    """
    print("Received event:", event)
    try:
        # Retrieve detail; if it's a string, parse it as JSON.
        detail = event.get("detail", {})
        if isinstance(detail, str):
            detail = json.loads(detail)

        # Check that the event is intended for validation.
        if detail.get("action") != "validate_items":
            print("Event not relevant for validation.")
            return {
                "result": "skipped",
                "message": "Event not relevant for item validation.",
            }

        items = detail.get("items", [])
        invalid_items = []

        for item in items:
            if not is_location_valid(item.get("location_id")):
                invalid_items.append(
                    {
                        "location_id": item.get("location_id"),
                        "error": "Invalid location_id",
                    }
                )

        if invalid_items:
            print("Validation errors found:", invalid_items)
        else:
            print("All items are valid.")

        return {
            "result": "validation_complete",
            "invalid_items": invalid_items,
        }

    except Exception as e:
        print("Error during validation:", str(e))
        return {"result": "error", "error": str(e)}
