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
