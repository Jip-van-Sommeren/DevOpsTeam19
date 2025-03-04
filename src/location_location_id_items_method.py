import json
from psycopg2.extras import RealDictCursor
from db_layer.db_connect import get_connection

conn = get_connection()


def get_items(location_id):
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, description FROM locations WHERE id = %s;",
                (location_id,),
            )
            location = cur.fetchall()
        if location:
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(
                    {
                        "id": location[0],
                        "name": location[1],
                        "description": location[2],
                    }
                ),
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
        return get_items(location_id)

    else:
        return {
            "statusCode": 405,
            "body": json.dumps(
                {"message": f"Method {http_method} not allowed"}
            ),
        }
