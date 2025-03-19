from db_layer.db_connect import get_session
from db_layer.basemodels import Reservation


def lambda_handler(event, context):
    # Expecting a 'reservationId' in the event payload
    data = event.get("data") or {}
    reservation_id = data.get("reservation_id")

    if not reservation_id:
        raise ValueError("Missing reservation_id in event data")

    session = get_session()
    try:
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
