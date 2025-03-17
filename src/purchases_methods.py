# import json
# from psycopg2.extras import RealDictCursor
# from db_layer.db_connect import get_connection

# conn = get_connection()

# # Initialize an EventBridge client


# def get_purchases(event):
#     """
#     Retrieves a list of purchases from the database with pagination.
#     Expects query string parameters "skip" and "limit" for pagination.
#     Defaults: skip=0, limit=100.
#     """
#     try:
#         query_params = event.get("queryStringParameters") or {}
#         try:
#             skip = int(query_params.get("skip", 0))
#             limit = int(query_params.get("limit", 100))
#         except ValueError:
#             skip = 0
#             limit = 100
#         if limit > 1000:
#             limit = 1000

#         with conn.cursor(cursor_factory=RealDictCursor) as cur:
#             cur.execute(
#                 "SELECT id, name FROM purchases OFFSET %s LIMIT %s;",
#                 (skip, limit),
#             )
#             purchases = cur.fetchall()

#         return {
#             "statusCode": 200,
#             "headers": {"Content-Type": "application/json"},
#             "body": json.dumps(purchases),
#         }
#     except Exception as e:
#         print("Error fetching purchases:", str(e))
#         return {
#             "statusCode": 500,
#             "body": json.dumps(
#                 {"message": "Error fetching purchases", "error": str(e)}
#             ),
#         }


# def lambda_handler(event, context):
#     """
#     Main Lambda handler. Routes requests based on HTTP method.
#     Assumes API Gateway is set up with Lambda proxy integration.
#     """
#     http_method = event.get("httpMethod", "")
#     resource = event.get("resource", "")

#     # Route for /purchases endpoint
#     if resource == "/purchases" and http_method == "GET":
#         return get_purchases(event)

#     # If the request doesn't match any endpoint, return 404
#     return {"statusCode": 404, "body": json.dumps({"message": "Not Found"})}

import json
from db_layer.db_connect import get_session
from db_layer.basemodels import Purchase, PurchasedItem


def get_purchase(purchase_id):
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
        # Map fields: here "name" represents the user_id and "description" the payment_token
        purchase_data = {
            "id": purchase.id,
            "name": purchase.user_id,
            "description": purchase.payment_token,
            "status": purchase.status,
            "purchase_date": (
                purchase.purchase_date.isoformat()
                if purchase.purchase_date
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
        print("Error in get_purchase:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error retrieving purchase", "error": str(e)}
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
        # Update allowed fields.
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
