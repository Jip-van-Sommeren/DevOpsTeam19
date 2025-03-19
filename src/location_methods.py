import json
from db_layer.db_connect import get_session
from db_layer.basemodels import Location


def get_locations(event):
    """
    Retrieves a list of locations from the database with pagination.
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

        locations = session.query(Location).offset(skip).limit(limit).all()
        locations_list = [
            {
                "id": loc.id,
                "address": loc.address,
                "zip_code": loc.zip_code,
                "city": loc.city,
                "street": loc.street,
                "state": loc.state,
                "number": loc.number,
                "addition": loc.addition,
                "type": loc.type,
            }
            for loc in locations
        ]

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(locations_list),
        }
    except Exception as e:
        print("Error fetching location:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error fetching location", "error": str(e)}
            ),
        }
    finally:
        session.close()


def add_location(location):
    """
    Inserts a new location into the database.
    Expects `location` to be a dict with keys:
        address, zip_code, city, street, state, number, addition (optional),
        type.
    """
    loc_type = location.get("type")
    if loc_type not in ["warehouse", "store"]:
        return {
            "statusCode": 400,
            "body": json.dumps(
                {
                    "message": "Invalid location type",
                    "error": f"Location type must be one of 'warehouse' \
                        or 'store'. Got '{loc_type}'",
                }
            ),
        }
    session = get_session()
    try:
        new_location = Location(
            address=location["address"],
            zip_code=location["zip_code"],
            city=location["city"],
            street=location["street"],
            state=location["state"],
            number=location["number"],
            addition=location.get("addition"),
            type=loc_type,
        )
        session.add(new_location)
        session.commit()
        session.refresh(new_location)
        response = {
            "id": new_location.id,
            "address": new_location.address,
            "zip_code": new_location.zip_code,
            "city": new_location.city,
            "street": new_location.street,
            "state": new_location.state,
            "number": new_location.number,
            "addition": new_location.addition,
            "type": new_location.type,
        }
        return {
            "statusCode": 201,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(response),
        }
    except Exception as e:
        session.rollback()
        print("Error adding location:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error adding location", "error": str(e)}
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

    # Route for /location endpoint
    if resource == "/locations":
        if http_method == "GET":
            return get_locations(event)
        elif http_method == "POST":
            try:
                location = json.loads(event.get("body", "{}"))
            except Exception as e:
                return {
                    "statusCode": 400,
                    "body": json.dumps(
                        {
                            "message": "Invalid JSON in request body",
                            "error": str(e),
                        }
                    ),
                }
            return add_location(location)

    # If the request doesn't match any endpoint, return 404
    return {"statusCode": 404, "body": json.dumps({"message": "Not Found"})}
