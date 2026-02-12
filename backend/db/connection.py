from config import DB_CONFIG


def get_connection():
    import mysql.connector
    return mysql.connector.connect(**DB_CONFIG)
