import json
from db_layer.db_connect import get_session
from db_layer.basemodels import ItemStock
import boto3
import os

sfn_client = boto3.client("stepfunctions")
STATE_MACHINE_ARN = os.environ.get("STATE_MACHINE_ARN")


def get_item(item_id, location_id):
    """
    Retrieves an item from the item_stock table.
    Optionally filters by location_id.
    """
    session = get_session()
    try:
        query = session.query(ItemStock).filter(ItemStock.item_id == item_id)
        if location_id is not None:
            query = query.filter(ItemStock.location_id == location_id)
        item = query.first()
        if item:
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(
                    {
                        "id": item.id,
                        "item_id": item.item_id,
                        "location_id": item.location_id,
                        "quantity": item.quantity,
                    }
                ),
            }
        else:
            return {
                "statusCode": 404,
                "body": json.dumps({"message": "Item not found"}),
            }
    except Exception as e:
        print("Error in get_item:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error retrieving item", "error": str(e)}
            ),
        }
    finally:
        session.close()


def delete_item(item_id, location_id):
    """
    Deletes an item from the item_stock table.
    Optionally filters by location_id.
    """
    session = get_session()
    try:
        query = session.query(ItemStock).filter(ItemStock.item_id == item_id)
        if location_id is not None:
            query = query.filter(ItemStock.location_id == location_id)
        item = query.first()
        if not item:
            return {
                "statusCode": 404,
                "body": json.dumps({"message": "Item not found"}),
            }
        session.delete(item)
        session.commit()
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "id": item.id,
                    "item_id": item.item_id,
                    "location_id": item.location_id,
                    "quantity": item.quantity,
                }
            ),
        }
    except Exception as e:
        session.rollback()
        print("Error in delete_item:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error deleting item", "error": str(e)}
            ),
        }
    finally:
        session.close()


def update_stock(item, operation):
    """
    Updates the stock quantity for a given item.
    - For operation "deduct": subtracts the quantity.
    - For operation "add": adds to the quantity.
    - For operation "reset": sets the quantity to the given value.

    Expects `item` to be a dict with 'item_id', 'location_id', and 'quantity'.
    Returns the updated item as a dict.
    """
    session = get_session()
    try:
        query = session.query(ItemStock).filter(
            ItemStock.item_id == item["item_id"],
            ItemStock.location_id == item["location_id"],
        )
        stock_item = query.first()
        if not stock_item:
            raise ValueError("Item not found")
        if operation == "deduct":
            stock_item.quantity -= item["quantity"]
        elif operation == "add":
            stock_item.quantity += item["quantity"]
        elif operation == "reset":
            stock_item.quantity = item["quantity"]
        else:
            raise ValueError(
                "Invalid operation. Expected 'deduct', 'add', or 'reset'."
            )
        session.commit()
        session.refresh(stock_item)
        return {
            "id": stock_item.id,
            "item_id": stock_item.item_id,
            "location_id": stock_item.location_id,
            "quantity": stock_item.quantity,
        }
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def lambda_handler(event, context):
    """
    Main Lambda handler for the /stock/{id} endpoint.
    Routes requests based on HTTP method.
    """
    http_method = event.get("httpMethod", "")
    path_params = event.get("pathParameters") or {}
    item_id = path_params.get("item_id")

    if not item_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Missing item_id in path"}),
        }
    try:
        payload = json.loads(event.get("body", "{}"))
    except Exception as e:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Invalid JSON", "error": str(e)}),
        }
    if http_method == "GET":
        return get_item(item_id, payload.get("location_id"))
    elif http_method == "DELETE":
        return delete_item(item_id, payload.get("location_id"))
    elif http_method == "PUT":

        stock_operation = payload.get("stock_operation", "reset")
        try:
            updated_item = update_stock(payload, stock_operation)
        except Exception as e:
            return {
                "statusCode": 500,
                "body": json.dumps(
                    {"message": "Error updating stock", "error": str(e)}
                ),
            }
        return {
            "statusCode": 200,
            "body": json.dumps(
                {"message": "Stock update successful", "updated": updated_item}
            ),
        }
    else:
        return {
            "statusCode": 405,
            "body": json.dumps(
                {"message": f"Method {http_method} not allowed"}
            ),
        }
