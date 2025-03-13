import json
import os
import boto3
from psycopg2.extras import RealDictCursor
from db_layer.db_connect import get_connection

# Initialize resources
conn = get_connection()
sfn_client = boto3.client("stepfunctions")


def get_and_delete_reservations(reservation_id):
    """
    Deletes reserved items for the given reservation_id from the database
    and returns the deleted rows.
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            DELETE FROM reserved_items
            WHERE reservation_id = %s
            RETURNING item_id, quantity;
            """,
            (reservation_id,),
        )
        deleted_rows = cur.fetchall()
    conn.commit()
    return deleted_rows


def update_reservation(reservation_id: str, payload: dict[str, str]) -> dict:
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE reservations SET, status = %s WHERE \
                    id = %s  RETURNING id, status;",
                (
                    payload.get("status"),
                    reservation_id,
                ),
            )
            updated_reservation = cur.fetchone()
            if not updated_reservation:
                return {
                    "statusCode": 404,
                    "body": json.dumps({"message": "reservation not found"}),
                }
            conn.commit()
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "id": updated_reservation[0],
                    "name": updated_reservation[1],
                    "description": updated_reservation[2],
                }
            ),
        }
    except Exception as e:
        conn.rollback()
        print("Error in update_reservation:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error updating reservation", "error": str(e)}
            ),
        }


def lambda_handler(event, context):
    """
    Main Lambda handler that extracts data from the API request, deletes
    reservation items,
    and triggers a state machine execution with the deleted items.
    """
    http_method = event.get("httpMethod", "")
    path_params = event.get("pathParameters") or {}
    reservation_id = path_params.get("reservation_id")

    if http_method != "PUT":
        return {
            "statusCode": 404,
            "body": json.dumps({"message": "Not Found"}),
        }

    try:
        body = json.loads(event.get("body", "{}"))
    except Exception as e:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Invalid JSON", "error": str(e)}),
        }

    # Fetch and delete reservation items
    if body.get("status") == "cancelled" or body.get("status") == "paid":
        try:
            deleted_items = get_and_delete_reservations(reservation_id)
        except Exception as e:
            return {
                "statusCode": 500,
                "body": json.dumps(
                    {"message": "Error fetching reservations", "error": str(e)}
                ),
            }

        # Build input for the state machine as a dictionary
        if body.get("status") == "paid":
            body["items"] = deleted_items
        if body.get("status") == "cancelled":
            body["stock_operation"] = "add"
        state_machine_input = json.dumps({"data": body})

        try:
            response = sfn_client.start_execution(
                stateMachineArn=os.environ.get("STATE_MACHINE_ARN"),
                input=json.dumps(state_machine_input),
            )
        except Exception as e:
            return {
                "statusCode": 500,
                "body": json.dumps(
                    {
                        "message": "Error starting state machine",
                        "error": str(e),
                    }
                ),
            }
    else:
        update_reservation(reservation_id, body)

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "Saga triggered successfully",
                "executionArn": response.get("executionArn"),
            }
        ),
    }
