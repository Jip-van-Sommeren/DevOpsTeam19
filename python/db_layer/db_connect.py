import os
import psycopg2
from sqlalchemy import create_engine


def return_engine():
    """
    Returns a new connection to the PostgreSQL database using
    credentials stored in environment variables.
    """
    host = os.environ.get("DB_HOST")
    dbname = os.environ.get("DB_NAME")
    port = os.environ.get("DB_PORT", 5432)
    user = os.environ.get("DB_USER")
    password = os.environ.get("DB_PASSWORD")
    DATABASE_URL = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    # e.g., "postgresql://user:password@host:port/dbname"

    return create_engine(DATABASE_URL)


def get_connection():
    """
    Returns a new connection to the PostgreSQL database using
    credentials stored in environment variables.
    """
    return psycopg2.connect(
        host=os.environ.get("DB_HOST"),
        dbname=os.environ.get("DB_NAME"),
        port=os.environ.get("DB_PORT", 5432),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
    )
