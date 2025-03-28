import os
import boto3
from db_layer.db_connect import get_session
from db_layer.basemodels import ItemStock

sns_client = boto3.client("sns", region_name="eu-north-1")
SNS_TOPIC_ARN = os.environ.get("STOCK_ALERT_TOPIC_ARN")


def update_stock_for_item(session, item, operation):
    """
    Updates the stock quantity for a given item.
    - For operation "deduct": subtracts the quantity.
    - For operation "add": adds back the quantity.
    - For operation "reset": sets the quantity to a specific value.
    Expects `item` to be a dict with 'item_id', 'location_id', and 'quantity'.
    Returns the updated row as a dict.
    """
    # Query for the item stock record
    item_stock = (
        session.query(ItemStock)
        .filter_by(item_id=item["item_id"], location_id=item["location_id"])
        .one_or_none()
    )

    if item_stock is None:
        return None

    # Update the quantity based on the operation
    if operation == "deduct":
        item_stock.quantity -= item["quantity"]
    elif operation == "add":
        item_stock.quantity += item["quantity"]
    elif operation == "reset":
        item_stock.quantity = item["quantity"]
    else:
        raise ValueError(
            "Invalid operation. Expected 'deduct', 'add', or 'reset'."
        )

    # Flush changes so that they are sent to the DB, then refresh to get
    # updated values.
    session.flush()
    session.refresh(item_stock)

    return {"id": item_stock.id, "quantity": item_stock.quantity}


def send_stock_alert(item_id, stock):
    """
    Publishes an SNS notification if stock is below threshold.
    """
    message = (
        f"Alert: Stock for item {item_id} is low. Current stock: {stock}."
    )

    response = sns_client.publish(
        TopicArn=SNS_TOPIC_ARN, Message=message, Subject="Low Stock Alert"
    )
    print("SNS publish response:", response)


def lambda_handler(event, context):
    """
    Lambda handler to update inventory based on data from the state machine.

    Expects the event to contain:
      - A nested "data" key with a "response_body" that includes an "items" array.
      - An "operation" field indicating the update type:
          "deduct" for purchases (default),
          "add" for cancellations,
          "reset" to set a new quantity.
      - Optionally, "reservation_id" and/or "purchase_id" keys.
    """
    print("Received event:", event)
    session = get_session()

    try:
        # Extract input values.
        data = event.get("data", {})
        items = data.get("response_body", {}).get("items")
        operation = data.get("operation", "deduct")

        # Validate input.
        if not items:
            raise ValueError("No items provided in the event input.")

        updated_items = []
        # Update stock for each item.
        for item in items:
            updated = update_stock_for_item(session, item, operation)
            if updated is None:
                print(
                    f"Item with ID {item.get('item_id')} at location {item.get('location_id')} not found or update failed."
                )
            else:
                updated_items.append(updated)

        # Commit all updates.
        session.commit()

        # Send alerts for low stock if deducting.
        if operation == "deduct":
            for updated in updated_items:
                if updated.get("quantity", 0) < 10:
                    send_stock_alert(updated["id"], updated["quantity"])

        print("Stock updated for items:", updated_items)

        # Build response.
        response = {
            "response_body": data.get("response_body"),
            "updated_items": updated_items,
            "statusCode": 201,
        }
        if "reservation_id" in data:
            response["reservation_id"] = data["reservation_id"]
        if "purchase_id" in data:
            response["purchase_id"] = data["purchase_id"]

        return response

    except Exception as e:
        session.rollback()
        raise e

    finally:
        session.close()
