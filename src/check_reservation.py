# from psycopg2.extras import RealDictCursor
# from db_layer.db_connect import get_connection

# conn = get_connection()


# def lambda_handler(event, context):
#     # Expecting a 'reservationId' in the event payload
#     data = event.get("data") or {}

#     reservation_id = data.get("response_body").get("reservation").get("id")

#     if not reservation_id:
#         raise ValueError("Missing reservation_id in event data")

#     try:
#         # Establish a connection to the PostgreSQL database

#         # Create a cursor with dictionary output for easier access
#         cur = conn.cursor(cursor_factory=RealDictCursor)

#         # Query the reservations table for the given reservation_id
#         query = "SELECT * FROM reservations WHERE reservation_id = %s"
#         cur.execute(query, (reservation_id,))
#         result = cur.fetchone()

#         # Clean up database connections
#         cur.close()
#         conn.close()

#         if result:
#             return {"stock_operation": "add", "reservationExists": True}
#         else:
#             return {"reservationExists": False}

#     except Exception as e:
#         raise e
from db_layer.db_connect import get_session
from db_layer.basemodels import Reservation


def lambda_handler(event, context):
    # Expecting a 'reservationId' in the event payload
    data = event.get("data") or {}
    # Navigate the nested structure to get the reservation id.
    reservation_id = (
        data.get("response_body", {}).get("reservation", {}).get("id")
    )

    if not reservation_id:
        raise ValueError("Missing reservation_id in event data")

    session = get_session()
    try:
        # Query the reservations table for the given reservation_id.
        # Here we assume that the Reservation model's primary key is 'id'.
        reservation = (
            session.query(Reservation)
            .filter(Reservation.id == reservation_id)
            .first()
        )

        if reservation:
            return {"stock_operation": "add", "reservationExists": True}
        else:
            return {"reservationExists": False}
    except Exception as e:
        raise e
    finally:
        session.close()
