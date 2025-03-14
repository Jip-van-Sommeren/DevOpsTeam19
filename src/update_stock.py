import json
import os
import boto3
from psycopg2.extras import RealDictCursor
from db_layer.db_connect import get_connection

# Establish a database connection (ensure this connects to your inventory DB)
conn = get_connection()

# Initialize SNS client
sns_client = boto3.client("sns")
SNS_TOPIC_ARN = os.environ.get("STOCK_ALERT_TOPIC_ARN")


def update_stock_for_item(item, operation):
    """
    Updates the stock quantity for a given item.
    - For operation "deduct": subtracts the quantity.
    - For operation "add": adds back the quantity.
    Expects `item` to be a dict with 'item_id' and 'quantity'.
    Returns the updated row.
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        if operation == "deduct":
            query = """
                UPDATE item_stock
                SET quantity = quantity - %s
                WHERE item_id = %s AND location_id = %s
                RETURNING id, quantity;
            """
        elif operation == "add":
            query = """
                UPDATE item_stock
                SET quantity = quantity + %s
                WHERE item_id = %s AND location_id = %s
                RETURNING id, quantity;
            """
        elif operation == "reset":
            query = """
                UPDATE item_stock
                SET quantity = %s
                WHERE item_id = %s AND location_id = %s
                RETURNING id, quantity;
            """
        else:
            raise ValueError(
                "Invalid operation. Expected 'deduct', 'add' 'reset."
            )
        cur.execute(
            query, (item["quantity"], item["item_id"], item["location_id"])
        )
        updated = cur.fetchone()
    return updated


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
      purchases, "add" for cancellations).
    """
    print("Received event:", event)

    try:
        # Attempt to extract 'items' and 'operation' from the
        # event under the 'data' key.
        data = event.get("data", {})
        items = data.get("items")
        operation = data.get(
            "operation", "deduct"
        )  # default to 'deduct' if not specified
        if not items:
            raise ValueError("No items provided in the event input.")

        updated_items = []

        # Begin a transaction to update stock for all items.
        for item in items:
            updated = update_stock_for_item(item, operation)
            if updated is None:
                print(
                    f"Item with ID {item['item_id']} not found or \
                        update failed."
                )
            else:
                updated_items.append(updated)
        conn.commit()

        # If the operation is deducting stock, check for low stock and send
        # SNS alerts.
        if operation == "deduct":
            for updated in updated_items:
                if updated.get("quantity", 0) < 10:
                    send_stock_alert(updated["id"], updated["quantity"])

        print("Stock updated for items:", updated_items)
        return {
            "statusCode": 200,
            "body": json.dumps(
                {"message": "Stock updated", "updated": updated_items}
            ),
        }

    except Exception as e:
        conn.rollback()
        print("Error updating stock:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error updating stock", "error": str(e)}
            ),
        }
