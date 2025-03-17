# import json
# from db_layer.db_connect import get_connection

# conn = get_connection()


# def get_location(location_id):
#     try:
#         with conn.cursor() as cur:
#             cur.execute(
#                 "SELECT id, address, zip_code, city, street,  \
#                  state, number, addition, type FROM locations WHERE id = %s;",
#                 (location_id,),
#             )
#             location = cur.fetchone()
#         if location:
#             return {
#                 "statusCode": 200,
#                 "headers": {"Content-Type": "application/json"},
#                 "body": json.dumps(
#                     {
#                         "id": location[0],
#                         "name": location[1],
#                         "description": location[2],
#                     }
#                 ),
#             }
#         else:
#             return {
#                 "statusCode": 404,
#                 "body": json.dumps({"message": "location not found"}),
#             }
#     except Exception as e:
#         print("Error in get_location:", str(e))
#         return {
#             "statusCode": 500,
#             "body": json.dumps(
#                 {"message": "Error retrieving location", "error": str(e)}
#             ),
#         }


# def delete_location(location_id):
#     try:
#         with conn.cursor() as cur:
#             # Attempt to delete the location and return its details
#             cur.execute(
#                 "DELETE FROM locations WHERE id = %s RETURNING id;",
#                 (location_id,),
#             )
#             deleted_location = cur.fetchone()
#             if not deleted_location:
#                 # If no row was deleted, the location does not exist
#                 return {
#                     "statusCode": 404,
#                     "body": json.dumps({"message": "location not found"}),
#                 }
#             conn.commit()
#         return {
#             "statusCode": 200,
#             "headers": {"Content-Type": "application/json"},
#             "body": json.dumps(
#                 {
#                     "id": deleted_location[0],
#                     "name": deleted_location[1],
#                     "description": deleted_location[2],
#                 }
#             ),
#         }
#     except Exception as e:
#         conn.rollback()
#         print("Error in delete_location:", str(e))
#         return {
#             "statusCode": 500,
#             "body": json.dumps(
#                 {"message": "Error deleting location", "error": str(e)}
#             ),
#         }


# def update_location(location_id: str, payload) -> dict:
#     """
#     address TEXT NOT NULL,
#     zip_code TEXT NOT NULL,
#     city TEXT NOT NULL,
#     street TEXT NOT NULL,
#     state TEXT NOT NULL,
#     number INTEGER NOT NULL,
#     addition TEXT,
#     type TEXT NOT NULL


#     Args:
#         location_id (str): _description_
#         payload (_type_): _description_

#     Returns:
#         dict: _description_
#     """
#     try:
#         with conn.cursor() as cur:
#             cur.execute(
#                 "UPDATE locations SET address = %s, zip_code = %s, city = %s, \
#                 street = %s, state = %s, number = %s, addition = %s,  \
#                 type = %s  WHERE id = %s RETURNING id, name, description;",
#                 (
#                     payload.get("address"),
#                     payload.get("zip_code"),
#                     payload.get("city"),
#                     payload.get("street"),
#                     payload.get("state"),
#                     payload.get("number"),
#                     payload.get("addition"),
#                     payload.get("type"),
#                     location_id,
#                 ),
#             )
#             updated_location = cur.fetchone()
#             if not updated_location:
#                 return {
#                     "statusCode": 404,
#                     "body": json.dumps({"message": "location not found"}),
#                 }
#             conn.commit()
#         return {
#             "statusCode": 200,
#             "headers": {"Content-Type": "application/json"},
#             "body": json.dumps(
#                 {
#                     "id": updated_location[0],
#                     "name": updated_location[1],
#                     "description": updated_location[2],
#                 }
#             ),
#         }
#     except Exception as e:
#         conn.rollback()
#         print("Error in update_location:", str(e))
#         return {
#             "statusCode": 500,
#             "body": json.dumps(
#                 {"message": "Error updating location", "error": str(e)}
#             ),
#         }


# def lambda_handler(event, context):
#     """
#     Main Lambda handler for the /locations/{location_id} endpoint.
#     Routes the request based on the HTTP method.
#     """
#     http_method = event.get("httpMethod", "")
#     path_params = event.get("pathParameters") or {}
#     location_id = path_params.get("location_id")

#     if not location_id:
#         return {
#             "statusCode": 400,
#             "body": json.dumps({"message": "Missing location_id in path"}),
#         }

#     if http_method == "GET":
#         return get_location(location_id)
#     elif http_method == "DELETE":
#         try:
#             payload = json.loads(event.get("body", "{}"))
#         except Exception as e:
#             return {
#                 "statusCode": 400,
#                 "body": json.dumps(
#                     {"message": "Invalid JSON", "error": str(e)}
#                 ),
#             }
#         return delete_location(location_id)
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
#         return update_location(location_id, payload)
#     else:
#         return {
#             "statusCode": 405,
#             "body": json.dumps(
#                 {"message": f"Method {http_method} not allowed"}
#             ),
#         }
import json
from db_layer.db_connect import get_session
from db_layer.basemodels import Location


def get_location(location_id):
    """
    Retrieves a location by its ID.
    Returns a JSON response with "id", "name" (address), and "description" (zip_code).
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
                "name": location.address,  # using address as "name"
                "description": location.zip_code,  # using zip_code as "description"
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
        response_body = {
            "id": location.id,
            "name": location.address,
            "description": location.zip_code,
        }
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
    Returns a JSON response with "id", "name" (address), and "description" (zip_code).
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
