"""
Database connection and configuration.
Single source for DB settings; load dotenv here so scripts and app can use db without calling load_dotenv elsewhere.
"""
import os

from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}


def get_connection():
    """Return a new MySQL connection. Caller must close it."""
    import mysql.connector
    return mysql.connector.connect(**DB_CONFIG)
