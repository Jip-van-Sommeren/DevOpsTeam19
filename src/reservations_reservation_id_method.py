# import json
# from db_layer.db_connect import get_connection

# conn = get_connection()


# def get_reservation(reservation_id):
#     try:
#         with conn.cursor() as cur:
#             cur.execute(
#                 "SELECT id, user_id FROM reservations \
#                     WHERE id = %s;",
#                 (reservation_id,),
#             )
#             reservation = cur.fetchone()
#         if reservation:
#             return {
#                 "statusCode": 200,
#                 "headers": {"Content-Type": "application/json"},
#                 "body": json.dumps(
#                     {
#                         "id": reservation[0],
#                         "name": reservation[1],
#                         "description": reservation[2],
#                     }
#                 ),
#             }
#         else:
#             return {
#                 "statusCode": 404,
#                 "body": json.dumps({"message": "reservation not found"}),
#             }
#     except Exception as e:
#         print("Error in get_reservation:", str(e))
#         return {
#             "statusCode": 500,
#             "body": json.dumps(
#                 {"message": "Error retrieving reservation", "error": str(e)}
#             ),
#         }


# def delete_reservation(reservation_id):
#     try:
#         with conn.cursor() as cur:
#             # First, delete rows in reservationd_items that
#             # reference this reservation_id
#             cur.execute(
#                 "DELETE FROM reserved_items WHERE reservation_id = %s;",
#                 (reservation_id,),
#             )
#             # Then, delete the reservation and return its details
#             cur.execute(
#                 "DELETE FROM reservations WHERE id = %s RETURNING id;",
#                 (reservation_id,),
#             )
#             deleted_reservation = cur.fetchone()
#             if not deleted_reservation:
#                 # If no row was deleted, the reservation does not exist
#                 return {
#                     "statusCode": 404,
#                     "body": json.dumps({"message": "reservation not found"}),
#                 }
#             conn.commit()
#         return {
#             "statusCode": 200,
#             "headers": {"Content-Type": "application/json"},
#             "body": json.dumps(
#                 {
#                     "id": deleted_reservation[0],
#                     "name": deleted_reservation[1],
#                     "description": deleted_reservation[2],
#                 }
#             ),
#         }
#     except Exception as e:
#         conn.rollback()
#         print("Error in delete_reservation:", str(e))
#         return {
#             "statusCode": 500,
#             "body": json.dumps(
#                 {"message": "Error deleting reservation", "error": str(e)}
#             ),
#         }


# def update_reservation(reservation_id: str, payload: dict[str, str]) -> dict:
#     try:
#         with conn.cursor() as cur:
#             cur.execute(
#                 "UPDATE reservations SET user_id = %s, status = %s WHERE \
#                     id = %s  RETURNING id, user_id, status;",
#                 (
#                     payload.get("user_id"),
#                     payload.get("status"),
#                     reservation_id,
#                 ),
#             )
#             updated_reservation = cur.fetchone()
#             if not updated_reservation:
#                 return {
#                     "statusCode": 404,
#                     "body": json.dumps({"message": "reservation not found"}),
#                 }
#             conn.commit()
#         return {
#             "statusCode": 200,
#             "headers": {"Content-Type": "application/json"},
#             "body": json.dumps(
#                 {
#                     "id": updated_reservation[0],
#                     "name": updated_reservation[1],
#                     "description": updated_reservation[2],
#                 }
#             ),
#         }
#     except Exception as e:
#         conn.rollback()
#         print("Error in update_reservation:", str(e))
#         return {
#             "statusCode": 500,
#             "body": json.dumps(
#                 {"message": "Error updating reservation", "error": str(e)}
#             ),
#         }


# def lambda_handler(event, context):
#     """
#     Main Lambda handler for the /reservations/{reservation_id} endpoint.
#     Routes the request based on the HTTP method.
#     """
#     http_method = event.get("httpMethod", "")
#     path_params = event.get("pathParameters") or {}
#     reservation_id = path_params.get("reservation_id")

#     if not reservation_id:
#         return {
#             "statusCode": 400,
#             "body": json.dumps({"message": "Missing reservation_id in path"}),
#         }

#     if http_method == "GET":
#         return get_reservation(reservation_id)
#     elif http_method == "DELETE":
#         # try:
#         #     payload = json.loads(event.get("body", "{}"))
#         # except Exception as e:
#         #     return {
#         #         "statusCode": 400,
#         #         "body": json.dumps(
#         #             {"message": "Invalid JSON", "error": str(e)}
#         #         ),
#         #     }
#         return delete_reservation(reservation_id)
#     elif http_method == "PUT":
#         try:
#             payload = json.loads(event.get("body", "{}"))
#         except Exception as e:
#             return {
#                 "statusCode": 400,
#                 "body": json.dumps(
#                     {"message": "Invalid JSON", "error": str(e)}
#                 ),
#             }
#         return update_reservation(reservation_id, payload)
#     else:
#         return {
#             "statusCode": 405,
#             "body": json.dumps(
#                 {"message": f"Method {http_method} not allowed"}
#             ),
#         }


import json
from db_layer.db_connect import get_session
from db_layer.basemodels import Reservation, ReservedItem


def get_reservation(reservation_id):
    """
    Retrieves a reservation along with its reserved items.
    """
    session = get_session()
    try:
        reservation = (
            session.query(Reservation)
            .filter(Reservation.id == reservation_id)
            .first()
        )
        if reservation is None:
            return {
                "statusCode": 404,
                "body": json.dumps({"message": "Reservation not found"}),
            }

        # Query reserved items corresponding to the reservation id.
        reserved_items = (
            session.query(ReservedItem)
            .filter(ReservedItem.reservation_id == reservation_id)
            .all()
        )
        reserved_items_list = [
            {"item_id": item.item_id, "quantity": item.quantity}
            for item in reserved_items
        ]

        reservation_data = {
            "id": reservation.id,
            "user_id": reservation.user_id,
            "status": reservation.status,
            "created_at": (
                reservation.created_at.isoformat()
                if reservation.created_at
                else None
            ),
            "updated_at": (
                reservation.updated_at.isoformat()
                if reservation.updated_at
                else None
            ),
            "reserved_items": reserved_items_list,
        }
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(reservation_data),
        }
    except Exception as e:
        print("Error in get_reservation:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error retrieving reservation", "error": str(e)}
            ),
        }
    finally:
        session.close()


def delete_reservation(reservation_id):
    """
    Deletes a reservation and its associated reserved items.
    """
    session = get_session()
    try:
        reservation = (
            session.query(Reservation)
            .filter(Reservation.id == reservation_id)
            .first()
        )
        if not reservation:
            return {
                "statusCode": 404,
                "body": json.dumps({"message": "Reservation not found"}),
            }
        # Store details for the response.
        reservation_data = {
            "id": reservation.id,
            "user_id": reservation.user_id,
            "status": reservation.status,
        }
        # Delete associated reserved items.
        session.query(ReservedItem).filter(
            ReservedItem.reservation_id == reservation_id
        ).delete()
        # Delete the reservation.
        session.delete(reservation)
        session.commit()
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "message": "Reservation deleted",
                    "reservation": reservation_data,
                }
            ),
        }
    except Exception as e:
        session.rollback()
        print("Error in delete_reservation:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error deleting reservation", "error": str(e)}
            ),
        }
    finally:
        session.close()


def update_reservation(reservation_id, payload):
    """
    Updates the reservation fields such as user_id and status.
    """
    session = get_session()
    try:
        reservation = (
            session.query(Reservation)
            .filter(Reservation.id == reservation_id)
            .first()
        )
        if not reservation:
            return {
                "statusCode": 404,
                "body": json.dumps({"message": "Reservation not found"}),
            }
        # Update fields based on the payload.
        if "user_id" in payload:
            reservation.user_id = payload["user_id"]
        if "status" in payload:
            reservation.status = payload["status"]

        session.commit()
        session.refresh(reservation)

        updated_data = {
            "id": reservation.id,
            "user_id": reservation.user_id,
            "status": reservation.status,
            "created_at": (
                reservation.created_at.isoformat()
                if reservation.created_at
                else None
            ),
            "updated_at": (
                reservation.updated_at.isoformat()
                if reservation.updated_at
                else None
            ),
        }
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(updated_data),
        }
    except Exception as e:
        session.rollback()
        print("Error in update_reservation:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error updating reservation", "error": str(e)}
            ),
        }
    finally:
        session.close()


def lambda_handler(event, context):
    """
    Main Lambda handler for the /reservations/{reservation_id} endpoint.
    Routes requests based on the HTTP method.
    """
    http_method = event.get("httpMethod", "")
    path_params = event.get("pathParameters") or {}
    reservation_id = path_params.get("reservation_id")

    if not reservation_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Missing reservation_id in path"}),
        }

    if http_method == "GET":
        return get_reservation(reservation_id)
    elif http_method == "DELETE":
        return delete_reservation(reservation_id)
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
        return update_reservation(reservation_id, payload)
    else:
        return {
            "statusCode": 405,
            "body": json.dumps(
                {"message": f"Method {http_method} not allowed"}
            ),
        }
