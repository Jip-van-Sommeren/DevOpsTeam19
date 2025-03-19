import os
import boto3
from db_layer.db_connect import get_session
from db_layer.basemodels import ItemStock

# Establish a database connection (ensure this connects to your inventory DB)

# Initialize SNS client
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
    Lambda handler to update inventory based on data passed from the state
    machine.
    Expects the event to contain:
      - a nested "data" key with an "items" array,
      - and an "operation" field indicating the update type ("deduct" for
      purchases, "add" for cancellations, "reset" to set a new quantity).
    """
    print("Received event:", event)
    session = get_session()

    try:
        # Extract and validate input
        data = event.get("data", {})
        items = data.get("response_body", {}).get("items")
        operation = data.get(
            "operation", "deduct"
        )  # default to 'deduct' if not specified

        if not items:
            raise ValueError("No items provided in the event input.")

        updated_items = []

        # Process each item in the list
        for item in items:
            updated = update_stock_for_item(session, item, operation)
            if updated is None:
                print(
                    f"Item with ID {item['item_id']} at location \
                        {item['location_id']} not found or update failed."
                )
            else:
                updated_items.append(updated)

        # Commit all changes once all updates are done
        session.commit()

        # For deduction operations, check for low stock and send alerts if
        # necessary.
        if operation == "deduct":
            for updated in updated_items:
                if updated.get("quantity", 0) < 10:
                    send_stock_alert(updated["id"], updated["quantity"])

        print("Stock updated for items:", updated_items)
        reservation_id = data.get("reservation_id")
        purchase_id = data.get("purchase_id")
        if reservation_id and purchase_id:
            return {
                "response_body": data.get("response_body"),
                "updated_items": updated_items,
                "statusCode": 201,
                "reservation_id": reservation_id,
                "purchase_id": purchase_id,
            }
        elif reservation_id:
            return {
                "response_body": data.get("response_body"),
                "updated_items": updated_items,
                "statusCode": 201,
                "reservation_id": reservation_id,
            }
        elif purchase_id:
            return {
                "response_body": data.get("response_body"),
                "updated_items": updated_items,
                "statusCode": 201,
                "purchase_id": purchase_id,
            }
        else:
            return {
                "response_body": data.get("response_body"),
                "updated_items": updated_items,
                "statusCode": 201,
            }

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
