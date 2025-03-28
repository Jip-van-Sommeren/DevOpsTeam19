from db_layer.db_connect import get_session
from db_layer.basemodels import Purchase, PurchasedItem


def add_purchase(purchase):
    """
    Inserts a new purchase into the database and its associated purchased
    items.
    After successfully committing, it publishes an event to update inventory.
    Returns a dict with the purchase details and inserted items.
    """
    session = get_session()
    try:
        # Create a new Purchase record.
        new_purchase = Purchase(
            user_id=purchase["user_id"],
            payment_token=purchase["payment_token"],
            status=purchase["status"],
        )
        session.add(new_purchase)
        session.commit()
        session.refresh(new_purchase)  # Refresh to get the generated ID.
        purchase_id = new_purchase.id

        inserted_items = []
        items = purchase.get("items", [])
        if items:
            purchased_items_objects = []
            for item in items:
                purchased_item = PurchasedItem(
                    purchase_id=purchase_id,
                    item_id=item["item_id"],
                    location_id=item["location_id"],
                    quantity=item["quantity"],
                )
                purchased_items_objects.append(purchased_item)
            session.add_all(purchased_items_objects)
            session.commit()

            # Build a list of inserted items for the response.
            for pi in purchased_items_objects:
                inserted_items.append(
                    {
                        "item_id": pi.item_id,
                        "quantity": pi.quantity,
                        "location_id": pi.location_id,
                    }
                )

        response_body = {
            "purchase": {
                "id": new_purchase.id,
                "user_id": new_purchase.user_id,
                "payment_token": new_purchase.payment_token,
            },
            "items": inserted_items,
        }
        return response_body
    except Exception as e:
        session.rollback()
        print("Error adding purchase:", str(e))
        # Propagate the exception so that Step Functions can catch it.
        raise e
    finally:
        session.close()


def lambda_handler(event, context):
    """
    Lambda function to update the purchased_items table.
    Expects an event with:
      - data.purchase: a dict containing purchase details (user_id,
      payment_token, status)
      - data.items: a list of objects with 'item_id', 'location_id', and '
      quantity'
    This function is meant to be invoked by a Step Functions state machine.
    """
    print("Received event:", event)
    try:
        purchase_data = event.get("data")

        # Insert the purchase and associated purchased items.
        response_body = add_purchase(purchase_data)
        reservation_id = purchase_data.get("reservation_id")
        if reservation_id:
            # Update the reservation status to 'completed'.
            return {
                "response_body": response_body,
                "statusCode": 201,
                "reservation_id": reservation_id,
                "purchase_id": response_body["purchase"]["id"],
            }
        else:
            return {
                "response_body": response_body,
                "statusCode": 201,
                "purchase_id": response_body["purchase"]["id"],
                "stock_operation": "deduct",
            }
    except Exception as e:
        print("Error updating purchased_items:", str(e))
        raise e
