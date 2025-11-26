import sqlite3

DB_PATH = "grocery.db"


def get_connection():
    """
    Create and return a connection to the sqlite database specified by DB_PATH.
    If the database doesn't exist yet, one is automatically created.
    - 
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn