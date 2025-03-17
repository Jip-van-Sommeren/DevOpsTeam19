from psycopg2.extras import execute_values
from db_layer.db_connect import get_connection

conn = get_connection()


def add_purchase(purchase):
    """
    Inserts a new purchase into the database and its associated purchased
    items.
    After successfully committing, it publishes an event to update inventory.
    """
    try:
        with conn.cursor() as cur:
            # Insert into purchases table
            cur.execute(
                "INSERT INTO purchases (user_id, payment_token, status)\
                    VALUES \
                    (%s, %s)  RETURNING id, user_id, payment_token;",
                (
                    purchase["user_id"],
                    purchase["payment_token"],
                    purchase["status"],
                ),
            )
            new_purchase = cur.fetchone()
            purchase_id = new_purchase[0]

            items = purchase.get("items", [])
            inserted_items = []
            if items:
                values = [
                    (
                        purchase_id,
                        item["item_id"],
                        item["location_id"],
                        item["quantity"],
                    )
                    for item in items
                ]
                sql = """
                INSERT INTO purchased_items (purchase_id, item_id, location_id,
                quantity)
                VALUES %s
                RETURNING purchase_id, item_id, quantity;
                """
                execute_values(cur, sql, values)
                inserted_items = cur.fetchall()

            conn.commit()

        # Publish the purchase event as part of the saga

        response_body = {
            "purchase": {
                "id": new_purchase[0],
                "user_id": new_purchase[1],
                "payment_token": new_purchase[2],
            },
            "items": inserted_items,
        }
        return response_body
    except Exception as e:
        conn.rollback()
        print("Error adding purchase:", str(e))
        raise e  # Raise the exception to let Step Functions catch it if needed


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
        # Update the purchased_items table
        return add_purchase(purchase_data)

    except Exception as e:
        conn.rollback()
        print("Error updating purchased_items:", str(e))
        raise e
