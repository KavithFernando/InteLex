"""
Database connection. Uses config for DB settings.
"""
from config import DB_CONFIG


def get_connection():
    """Return a new MySQL connection. Caller must close it."""
    import mysql.connector
    return mysql.connector.connect(**DB_CONFIG)
