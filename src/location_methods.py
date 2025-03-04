import json
from psycopg2.extras import RealDictCursor
from db_layer.db_connect import get_connection

conn = get_connection()


def get_location():
    """
    Retrieves a list of location from the database.
    """
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT address, zip_code, city, street,  \
                 state, number, addition, type FROM location;"
            )
            location = cur.fetchall()
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(location),
        }
    except Exception as e:
        print("Error fetching location:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error fetching location", "error": str(e)}
            ),
        }


def add_location(location):
    """
    Inserts a new location into the database.
    Expects `location` to be a dict with at least a 'name' key.
        address TEXT NOT NULL,
    zip_code TEXT NOT NULL,
    city TEXT NOT NULL,
    street TEXT NOT NULL,
    state TEXT NOT NULL,
    number INTEGER NOT NULL,
    addition TEXT,
    type TEXT NOT NULL
    """
    loc_type = location.get("type")
    if loc_type not in ["warehouse", "store"]:
        return {
            "statusCode": 400,
            "body": json.dumps(
                {
                    "message": "Invalid location type",
                    "error": f"Location type must be one of 'warehouse' or \
                        'store'  Got '{loc_type}'",
                }
            ),
        }
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO location (address, zip_code, city, street,  \
                 state, number, addition, type) VALUES                   \
                 (%s, %s, %s, %s, %s, %s, %s, %s)                        \
                 RETURNING id, address, zip_code, city, street,          \
                 state, number, addition, type;",
                (
                    location["address"],
                    location["zip_code"],
                    location["city"],
                    location["street"],
                    location["state"],
                    location["number"],
                    location.get("addition"),
                    loc_type,
                ),
            )
            new_location = cur.fetchone()
            conn.commit()
        return {
            "statusCode": 201,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(new_location),
        }
    except Exception as e:
        conn.rollback()
        print("Error adding location:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error adding location", "error": str(e)}
            ),
        }


def lambda_handler(event, context):
    """
    Main Lambda handler. Routes requests based on HTTP method.
    Assumes API Gateway is set up with Lambda proxy integration.
    """
    http_method = event.get("httpMethod", "")
    resource = event.get("resource", "")

    # Route for /location endpoint
    if resource == "/location":
        if http_method == "GET":
            return get_location()
        elif http_method == "POST":
            # Expect the request body to contain JSON data for the new location
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
