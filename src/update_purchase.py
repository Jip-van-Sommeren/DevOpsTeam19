import json
from db_layer.db_connect import get_connection

conn = get_connection()


def update_purchase(purchase_id: str, payload):

    if (
        payload.get("status") == "paid"
        and payload.get("payment_token") is None
    ):
        return {
            "statusCode": 400,
            "body": json.dumps(
                {"message": "Missing payment_token in request body"}
            ),
        }

    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE purchases SET payment_token = %s, \
                status = %s WHERE id = %s RETURNING id, status;",
                (
                    payload.get("payment_token "),
                    payload.get("status"),
                    purchase_id,
                ),
            )
            updated_purchase = cur.fetchone()
            if not updated_purchase:
                return {
                    "statusCode": 404,
                    "body": json.dumps({"message": "purchase not found"}),
                }
            conn.commit()
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {"id": updated_purchase[0], "status": updated_purchase[1]}
            ),
        }
    except Exception as e:
        conn.rollback()
        print("Error in update_purchase:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error updating purchase", "error": str(e)}
            ),
        }


def lambda_handler(event, context):
    """
    Lambda function to update the purchased_items table.
    Expects an event with:
      - purchase_id: the ID of the purchase
      - items: a list of objects with 'item_id' and 'quantity'

    This function is meant to be invoked by a Step Functions state machine.
    """
    print("Received event:", event)

    try:
        purchase_data = event.get("data")
        purchase_id = purchase_data.get("purchase_id")
        # Update the purchased_items table
        return update_purchase(purchase_id, purchase_data)

    except Exception as e:
        conn.rollback()
        print("Error updating purchased_items:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error updating purchased_items", "error": str(e)}
            ),
        }
