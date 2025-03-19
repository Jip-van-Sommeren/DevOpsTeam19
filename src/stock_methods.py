import json
from db_layer.db_connect import get_session
from db_layer.basemodels import ItemStock


def get_items(event):
    """
    Retrieves a list of items from the database with pagination.
    Expects query string parameters "skip" and "limit" for pagination.
    Optionally filters by location_id.
    """
    session = get_session()
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
        query = session.query(ItemStock)
        if location_id is not None:
            query = query.filter(ItemStock.location_id == location_id)

        items = query.offset(skip).limit(limit).all()

        # Convert SQLAlchemy model instances to dictionaries.
        items_list = [
            {
                "id": item.id,
                "item_id": item.item_id,
                "location_id": item.location_id,
                "quantity": item.quantity,
            }
            for item in items
        ]
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(items_list),
        }
    except Exception as e:
        print("Error fetching items:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error fetching items", "error": str(e)}
            ),
        }
    finally:
        session.close()


def add_items(items):
    """
    Inserts multiple items into the item_stock table.
    Expects 'items' to be a list of dicts, each with keys:
      'item_id', 'location_id', and 'quantity'.
    """
    session = get_session()
    try:
        # Create ItemStock objects from the provided data.
        item_objects = [
            ItemStock(
                item_id=data["item_id"],
                location_id=data["location_id"],
                quantity=data["quantity"],
            )
            for data in items
        ]
        session.add_all(item_objects)
        session.commit()

        # Refresh to ensure primary keys (e.g., id) are populated.
        for item in item_objects:
            session.refresh(item)

        inserted_items = [
            {
                "id": item.id,
                "item_id": item.item_id,
                "location_id": item.location_id,
                "quantity": item.quantity,
            }
            for item in item_objects
        ]
        return {
            "statusCode": 201,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(inserted_items),
        }
    except Exception as e:
        session.rollback()
        print("Error adding items:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error adding items", "error": str(e)}
            ),
        }
    finally:
        session.close()


def lambda_handler(event, context):
    """
    Main Lambda handler. Routes requests based on HTTP method.
    Assumes API Gateway is set up with Lambda proxy integration.
    """
    http_method = event.get("httpMethod", "")
    resource = event.get("resource", "")

    # Route for /stock endpoint.
    if resource == "/stock":
        if http_method == "GET":
            return get_items(event)
        elif http_method == "POST":
            # Expect the request body to contain JSON data.
            try:
                body = json.loads(event.get("body", "{}"))
                items = body.get("items", [])
                # Ensure we have a list of items.
                if not isinstance(items, list):
                    items = [items]
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
            return add_items(items)

    # If the request doesn't match any endpoint, return 404.
    return {"statusCode": 404, "body": json.dumps({"message": "Not Found"})}
