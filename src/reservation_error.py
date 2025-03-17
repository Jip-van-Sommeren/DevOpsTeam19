# import json
# from psycopg2.extras import RealDictCursor
# from db_layer.db_connect import get_connection

# conn = get_connection()


# def cancel_reservation(reservation_id):
#     """
#     Reverses or cancels the reservation in the database.
#     Implementation will vary based on your schema and business rules.
#     """
#     with conn.cursor(cursor_factory=RealDictCursor) as cur:
#         # Example: Delete the reservation record and any reservationd_items
#         # Or you might just set a 'status' to 'canceled'.
#         cur.execute(
#             "DELETE FROM reservation_items WHERE reservation_id = %s;",
#             (reservation_id,),
#         )
#         cur.execute(
#             "DELETE FROM reservations WHERE id = %s;", (reservation_id,)
#         )
#     conn.commit()


# def lambda_handler(event, context):
#     """
#     A compensation Lambda that is triggered if a reservation step fails.
#     Expects the event to contain a 'reservation_id' key.
#     """
#     print("Received compensation event:", event)
#     try:
#         # The event can come from Step Functions or another service.
#         # Adjust to match how your data is passed in.
#         # If coming from Step Functions, event['reservation_id'] might be
#         # in the top-level or nested under event['input'] or event['detail'].
#         reservation_id = event.get("data").get("reservation_id")
#         if not reservation_id:
#             return {
#                 "statusCode": 400,
#                 "body": json.dumps({"message": "No reservation_id provided"}),
#             }

#         cancel_reservation(reservation_id)

#         return {
#             "statusCode": 200,
#             "body": json.dumps(
#                 {
#                     "message": f"reservation {reservation_id}  \
#                         canceled successfully."
#                 }
#             ),
#         }

#     except Exception as e:
#         conn.rollback()
#         print("Error canceling reservation:", str(e))
#         return {
#             "statusCode": 500,
#             "body": json.dumps(
#                 {"message": "Error canceling reservation", "error": str(e)}
#             ),
#         }
import json
from db_layer.db_connect import get_session
from db_layer.basemodels import Reservation, ReservedItem


def cancel_reservation(reservation_id):
    """
    Reverses or cancels the reservation in the database.
    Implementation: Deletes associated reserved items and the reservation record.
    """
    session = get_session()
    try:
        # Delete associated reserved items.
        session.query(ReservedItem).filter(
            ReservedItem.reservation_id == reservation_id
        ).delete()
        # Retrieve and delete the reservation record.
        reservation = (
            session.query(Reservation)
            .filter(Reservation.id == reservation_id)
            .first()
        )
        if reservation:
            session.delete(reservation)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def lambda_handler(event, context):
    """
    A compensation Lambda that is triggered if a reservation step fails.
    Expects the event to contain a 'reservation_id' key nested under event['data'].
    """
    print("Received compensation event:", event)
    try:
        reservation_id = event.get("data", {}).get("reservation_id")
        if not reservation_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "No reservation_id provided"}),
            }

        cancel_reservation(reservation_id)

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": f"Reservation {reservation_id} canceled successfully."
                }
            ),
        }
    except Exception as e:
        print("Error canceling reservation:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error canceling reservation", "error": str(e)}
            ),
        }
