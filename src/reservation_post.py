from db_layer.db_connect import get_session
from db_layer.basemodels import Reservation, ReservedItem
import boto3
import os

sfn_client = boto3.client("stepfunctions")
STATE_MACHINE_ARN = os.environ.get("STATE_MACHINE_ARN")


def update_reservation_items(user_id, items):
    """
    Inserts a new reservation into the reservations table and associated items
    into reserved_items.
    Returns a dict with the reservation details and inserted items.
    """
    session = get_session()
    try:
        # Create a new reservation.
        new_reservation = Reservation(user_id=user_id, status="reserved")
        session.add(new_reservation)
        session.commit()
        session.refresh(
            new_reservation
        )  # Ensure new_reservation.id is populated.
        reservation_id = new_reservation.id

        inserted_items = []
        if items:
            reserved_items_objects = []
            for item in items:
                reserved_item = ReservedItem(
                    reservation_id=reservation_id,
                    item_id=item["item_id"],
                    location_id=item.get("location_id"),
                    quantity=item["quantity"],
                )
                reserved_items_objects.append(reserved_item)
            session.add_all(reserved_items_objects)
            session.commit()
            # Build the inserted items list.
            for reserved_item in reserved_items_objects:
                inserted_items.append(
                    {
                        "reservation_id": reserved_item.reservation_id,
                        "item_id": reserved_item.item_id,
                        "location_id": reserved_item.location_id,
                        "quantity": reserved_item.quantity,
                    }
                )

        response_data = {
            "reservation": {
                "id": reservation_id,
                "user_id": new_reservation.user_id,
                "status": new_reservation.status,
            },
            "items": inserted_items,
        }
        return response_data
    except Exception as e:
        session.rollback()
        print("Error adding reservation:", str(e))
        # Propagate the error so the state machine can catch it.
        raise e
    finally:
        session.close()


def lambda_handler(event, context):
    """
    Lambda function to update reservation items.
    Expects an event with:
      - data.user_id: the ID of the user making the reservation
      - data.items: a list of objects with 'item_id', 'quantity' and
      optionally 'location_id'
    Returns the reservation data that can be passed to the next state in the
    state machine.
    """
    print("Received event:", event)
    try:
        data = event.get("data", {})
        user_id = data.get("user_id")
        items = data.get("items", [])

        # Validate the input.
        if not user_id:
            raise ValueError("Missing user_id in input")
        if not items:
            raise ValueError("No items provided to update")

        response_data = update_reservation_items(user_id, items)

        return {
            "response_body": response_data,
            "reservation_id": response_data["reservation"]["id"],
            "statusCode": 201,
        }

    except Exception as e:
        print("Error updating reservation items:", str(e))
        # Propagate the exception to trigger a Catch in the state machine.
        raise e
