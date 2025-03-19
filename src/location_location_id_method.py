import json
from db_layer.db_connect import get_session
from db_layer.basemodels import Location


def get_location(location_id):
    """
    Retrieves a location by its ID.
    Returns a JSON response with "id", "name" (address), and "description"
    (zip_code).
    """
    session = get_session()
    try:
        location = (
            session.query(Location).filter(Location.id == location_id).first()
        )
        if location:
            # Mimic the original response mapping:
            response_body = {
                "id": location.id,
                "address": location.address,
                "zip_code": location.zip_code,
                "city": location.city,
                "street": location.street,
                "state": location.state,
                "number": location.number,
                "addition": location.addition,
                "type": location.type,
            }
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(response_body),
            }
        else:
            return {
                "statusCode": 404,
                "body": json.dumps({"message": "location not found"}),
            }
    except Exception as e:
        print("Error in get_location:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error retrieving location", "error": str(e)}
            ),
        }
    finally:
        session.close()


def delete_location(location_id):
    """
    Deletes a location by its ID.
    Returns the deleted location's details in a JSON response.
    """
    session = get_session()
    try:
        # Retrieve the location first.
        location = (
            session.query(Location).filter(Location.id == location_id).first()
        )
        if not location:
            return {
                "statusCode": 404,
                "body": json.dumps({"message": "location not found"}),
            }
        # Prepare response data before deletion.
        response_body = {"id": location.id}
        # Delete the record and commit.
        session.delete(location)
        session.commit()
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(response_body),
        }
    except Exception as e:
        session.rollback()
        print("Error in delete_location:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error deleting location", "error": str(e)}
            ),
        }
    finally:
        session.close()


def update_location(location_id: str, payload) -> dict:
    """
    Updates a location with the provided payload.
    Expected payload keys:
        address, zip_code, city, street, state, number, addition, type
    Returns a JSON response with "id", "name" (address), and "description"
    (zip_code).
    """
    session = get_session()
    try:
        location = (
            session.query(Location).filter(Location.id == location_id).first()
        )
        if not location:
            return {
                "statusCode": 404,
                "body": json.dumps({"message": "location not found"}),
            }
        # Update fields.
        location.address = payload.get("address")
        location.zip_code = payload.get("zip_code")
        location.city = payload.get("city")
        location.street = payload.get("street")
        location.state = payload.get("state")
        location.number = payload.get("number")
        location.addition = payload.get("addition")
        location.type = payload.get("type")

        session.commit()
        session.refresh(location)
        updated_response = {
            "id": location.id,
            "name": location.address,
            "description": location.zip_code,
        }
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(updated_response),
        }
    except Exception as e:
        session.rollback()
        print("Error in update_location:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error updating location", "error": str(e)}
            ),
        }
    finally:
        session.close()


def lambda_handler(event, context):
    """
    Main Lambda handler for the /locations/{location_id} endpoint.
    Routes the request based on the HTTP method.
    """
    http_method = event.get("httpMethod", "")
    path_params = event.get("pathParameters") or {}
    location_id = path_params.get("location_id")

    if not location_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Missing location_id in path"}),
        }

    if http_method == "GET":
        return get_location(location_id)
    elif http_method == "DELETE":
        # Even if the DELETE method receives a body, we ignore it.
        return delete_location(location_id)
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
        return update_location(location_id, payload)
    else:
        return {
            "statusCode": 405,
            "body": json.dumps(
                {"message": f"Method {http_method} not allowed"}
            ),
        }
