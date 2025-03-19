from db_layer.db_connect import get_session
from db_layer.basemodels import Purchase, PurchasedItem


def cancel_purchase(purchase_id):
    """
    Reverses or cancels the purchase in the database.
    Implementation: Deletes associated purchased items and the purchase record.
    """
    session = get_session()
    try:
        # Delete associated purchased items.
        session.query(PurchasedItem).filter(
            PurchasedItem.purchase_id == purchase_id
        ).delete()
        # Retrieve and delete the purchase record.
        purchase = (
            session.query(Purchase).filter(Purchase.id == purchase_id).first()
        )
        if purchase:
            session.delete(purchase)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e  # Propagate the exception to be caught by the caller.
    finally:
        session.close()


def lambda_handler(event, context):
    """
    A compensation Lambda that is triggered if a purchase step fails.
    Expects the event to contain a 'purchase_id' key nested under
    event['data'].
    """
    print("Received compensation event:", event)
    try:
        purchase_id = event.get("data", {}).get("purchase_id")
        if not purchase_id:
            return {
                "statusCode": 400,
                "body": {"message": "No purchase_id provided"},
            }

        cancel_purchase(purchase_id)

        return {
            "statusCode": 200,
            "body": {
                "message": f"Purchase {purchase_id} cancelled successfully."
            },
        }
    except Exception as e:
        raise e
