import json
import os
import boto3
from psycopg2.extras import RealDictCursor
from db_layer.db_connect import get_connection

# Establish a database connection (ensure this connects to your inventory DB)
conn = get_connection()

# Initialize SNS client
sns_client = boto3.client("sns")
# You can set the SNS topic ARN as an environment variable, e.g.,
# STOCK_ALERT_TOPIC_ARN
SNS_TOPIC_ARN = os.environ.get("STOCK_ALERT_TOPIC_ARN")


def update_stock_for_item(item):
    """
    Decreases the stock quantity for a given item.
    Expects `item` to be a dict with 'item_id' and 'quantity'.
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Update stock: subtract the quantity purchased.
        cur.execute(
            "UPDATE item_stock SET quantity = quantity - %s WHERE id = %s \
                RETURNING id, quantity;",
            (item["quantity"], item["item_id"]),
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
    machine. Expects the event to contain a list of purchased items
    either as a top-level "items" key or nested under "detail".
    """
    print("Received event:", event)

    try:
        # Try to extract items from the event.
        items = event.get("items")
        if items is None:
            # If not found, attempt to retrieve from "detail".
            detail = event.get("detail", {})
            if isinstance(detail, str):
                detail = json.loads(detail)
            items = detail.get("items", [])

        if not items:
            raise ValueError("No items provided in the event input.")

        updated_items = []

        # Begin a transaction to update stock for all items.
        for item in items:
            updated = update_stock_for_item(item)
            if updated is None:
                # Optionally, handle the case when an item is not found.
                print(
                    f"Item with ID {item['item_id']} not found or update \
                        failed."
                )
            else:
                updated_items.append(updated)
        conn.commit()

        # Check if any updated item's stock is below 10 and send
        # SNS notification.
        for updated in updated_items:
            if updated.get("stock", 0) < 10:
                send_stock_alert(updated["id"], updated["stock"])

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
