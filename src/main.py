import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor

conn = None


def get_db_connection():
    global conn

    if conn is None:
        conn = psycopg2.connect(
            host=os.environ.get("DB_HOST"),
            port=os.environ.get("DB_PORT", 5432),
            database=os.environ.get("DB_NAME"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD"),
        )
    return conn


def lambda_handler(event, context):
    """
    AWS Lambda handler for the hello_world function.
    Returns a simple JSON response with a 200 status code.
    """
    response = {"statusCode": 200, "body": json.dumps("Hello, world!")}
    return response
