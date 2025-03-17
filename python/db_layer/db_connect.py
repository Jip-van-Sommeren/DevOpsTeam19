import os
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


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


engine = return_engine()

# Create a sessionmaker bound to the engine
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session():
    """
    Returns a new session instance.
    """
    return SessionLocal()


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
