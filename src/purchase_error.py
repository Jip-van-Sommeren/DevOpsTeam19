# import json
# from psycopg2.extras import RealDictCursor
# from db_layer.db_connect import get_connection

# conn = get_connection()


# def cancel_purchase(purchase_id):
#     """
#     Reverses or cancels the purchase in the database.
#     Implementation will vary based on your schema and business rules.
#     """
#     with conn.cursor(cursor_factory=RealDictCursor) as cur:
#         # Example: Delete the purchase record and any purchased_items
#         # Or you might just set a 'status' to 'canceled'.
#         cur.execute(
#             "DELETE FROM purchased_items WHERE purchase_id = %s;",
#             (purchase_id,),
#         )
#         cur.execute("DELETE FROM purchases WHERE id = %s;", (purchase_id,))
#     conn.commit()


# def lambda_handler(event, context):
#     """
#     A compensation Lambda that is triggered if a purchase step fails.
#     Expects the event to contain a 'purchase_id' key.
#     """
#     print("Received compensation event:", event)
#     try:
#         # The event can come from Step Functions or another service.
#         # Adjust to match how your data is passed in.
#         # If coming from Step Functions, event['purchase_id'] might be
#         # in the top-level or nested under event['input'] or event['detail'].
#         purchase_id = event.get("data").get("purchase_id")
#         if not purchase_id:
#             return {
#                 "statusCode": 400,
#                 "body": json.dumps({"message": "No purchase_id provided"}),
#             }

#         cancel_purchase(purchase_id)

#         return {
#             "statusCode": 200,
#             "body": json.dumps(
#                 {"message": f"Purchase {purchase_id} cancelled successfully."}
#             ),
#         }

#     except Exception as e:
#         conn.rollback()
#         print("Error canceling purchase:", str(e))
#         return {
#             "statusCode": 500,
#             "body": json.dumps(
#                 {"message": "Error canceling purchase", "error": str(e)}
#             ),
#         }

import json
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
    Expects the event to contain a 'purchase_id' key nested under event['data'].
    """
    print("Received compensation event:", event)
    try:
        purchase_id = event.get("data", {}).get("purchase_id")
        if not purchase_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "No purchase_id provided"}),
            }

        cancel_purchase(purchase_id)

        return {
            "statusCode": 200,
            "body": json.dumps(
                {"message": f"Purchase {purchase_id} cancelled successfully."}
            ),
        }
    except Exception as e:
        print("Error canceling purchase:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error canceling purchase", "error": str(e)}
            ),
        }
