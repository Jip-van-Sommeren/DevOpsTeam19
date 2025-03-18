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
from sqlalchemy.orm import joinedload
from db_layer.db_connect import get_session
from db_layer.basemodels import Purchase


def get_purchases(event):
    """
    Retrieves a list of purchases from the database with pagination, including reserved items.
    Expects query string parameters "skip" and "limit" for pagination.
    Defaults: skip=0, limit=100.
    """
    session = get_session()
    try:
        query_params = event.get("queryStringParameters") or {}
        try:
            skip = int(query_params.get("skip", 0))
            limit = int(query_params.get("limit", 100))
        except ValueError:
            skip = 0
            limit = 100
        if limit > 1000:
            limit = 1000

        user_id = query_params.get("user_id")
        if user_id:
            purchases = (
                session.query(Purchase)
                .options(joinedload(Purchase.purchased_items))
                .filter(Purchase.user_id == user_id)
                .offset(skip)
                .limit(limit)
                .all()
            )
        else:
            purchases = (
                session.query(Purchase)
                .options(joinedload(Purchase.purchased_items))
                .offset(skip)
                .limit(limit)
                .all()
            )

        purchases_list = []
        for res in purchases:
            purchases_list.append(
                {
                    "id": res.id,
                    "user_id": res.user_id,
                    "items": [
                        {"item_id": item.item_id, "quantity": item.quantity}
                        for item in res.reserved_items
                    ],
                }
            )

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(purchases_list),
        }
    except Exception as e:
        print("Error fetching purchases:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error fetching purchases", "error": str(e)}
            ),
        }
    finally:
        session.close()


def lambda_handler(event, context):
    """
    Main Lambda handler. Routes requests based on HTTP method.
    Assumes API Gateway is set up with Lambda proxy integration.
    """
    http_method = event.get("httpMethod", "")
    resource = event.get("resource", "")

    # Route for /purchases endpoint
    if resource == "/purchases" and http_method == "GET":
        return get_purchases(event)

    # If the request doesn't match any endpoint, return 404
    return {"statusCode": 404, "body": json.dumps({"message": "Not Found"})}
