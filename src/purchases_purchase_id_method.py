import json
from sqlalchemy.orm import joinedload
from db_layer.db_connect import get_session
from db_layer.basemodels import Purchase, PurchasedItem


def get_purchase(purchase_id):
    session = get_session()
    try:
        # Fetch purchase along with associated purchased items
        purchase = (
            session.query(Purchase)
            .options(joinedload(Purchase.purchased_items))
            .filter(Purchase.id == purchase_id)
            .first()
        )

        if not purchase:
            return {
                "statusCode": 404,
                "body": json.dumps({"message": "Purchase not found"}),
            }

        # Build response object including purchased items
        purchase_data = {
            "id": purchase.id,
            "user_id": purchase.user_id,
            "payment_token": purchase.payment_token,
            "purchase_items": [
                {"item_id": item.item_id, "quantity": item.quantity}
                for item in purchase.purchased_items
            ],
            "status": getattr(purchase, "status", None),
            "created_at": (
                purchase.created_at.isoformat()
                if purchase.created_at
                else None
            ),
            "updated_at": (
                purchase.updated_at.isoformat()
                if purchase.updated_at
                else None
            ),
        }

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(purchase_data),
        }
    except Exception as e:
        print("Error fetching purchase:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error fetching purchase", "error": str(e)}
            ),
        }
    finally:
        session.close()


def delete_purchase(purchase_id):
    session = get_session()
    try:
        purchase = (
            session.query(Purchase).filter(Purchase.id == purchase_id).first()
        )
        if not purchase:
            return {
                "statusCode": 404,
                "body": json.dumps({"message": "Purchase not found"}),
            }
        # Delete associated purchased items first.
        session.query(PurchasedItem).filter(
            PurchasedItem.purchase_id == purchase_id
        ).delete()
        # Prepare response data before deletion.
        response_data = {
            "id": purchase.id,
            "name": purchase.user_id,
            "description": purchase.payment_token,
        }
        session.delete(purchase)
        session.commit()
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(response_data),
        }
    except Exception as e:
        session.rollback()
        print("Error in delete_purchase:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error deleting purchase", "error": str(e)}
            ),
        }
    finally:
        session.close()


def update_purchase(purchase_id, payload):
    session = get_session()
    try:
        purchase = (
            session.query(Purchase).filter(Purchase.id == purchase_id).first()
        )
        if not purchase:
            return {
                "statusCode": 404,
                "body": json.dumps({"message": "Purchase not found"}),
            }
        # Update allowed fields (mapping 'name' to user_id, etc.)
        if "user_id" in payload:
            purchase.user_id = payload["user_id"]
        if "status" in payload:
            purchase.status = payload["status"]
        session.commit()
        session.refresh(purchase)
        updated_data = {
            "id": purchase.id,
            "name": purchase.user_id,
            "description": purchase.payment_token,
            "status": purchase.status,
        }
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(updated_data),
        }
    except Exception as e:
        session.rollback()
        print("Error in update_purchase:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error updating purchase", "error": str(e)}
            ),
        }
    finally:
        session.close()


def lambda_handler(event, context):
    """
    Main Lambda handler for the /purchases/{purchase_id} endpoint.
    Routes the request based on the HTTP method.
    """
    http_method = event.get("httpMethod", "")
    path_params = event.get("pathParameters") or {}
    purchase_id = path_params.get("purchase_id")

    if not purchase_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Missing purchase_id in path"}),
        }

    if http_method == "GET":
        return get_purchase(purchase_id)
    elif http_method == "DELETE":
        # For DELETE, we ignore the request body.
        return delete_purchase(purchase_id)
    elif http_method == "PUT":
        try:
            payload = json.loads(event.get("body", "{}"))
        except Exception as e:
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {"message": "Invalid JSON", "error": str(e)}
                ),
            }
        return update_purchase(purchase_id, payload)
    else:
        return {
            "statusCode": 405,
            "body": json.dumps(
                {"message": f"Method {http_method} not allowed"}
            ),
        }
