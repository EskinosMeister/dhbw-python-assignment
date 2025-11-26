# reset_db.py
import os

from db_init import get_connection

DB_PATH = "grocery.db" # unsure whether to delete this or not

destroy_schema = """
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS saved_products;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS supermarket_products;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS supermarkets;
DROP TABLE IF EXISTS users;
"""


def main():
    if os.path.exists(DB_PATH): # seems possibly redundant, DB_PATH is defined in this script
        os.remove(DB_PATH)
        print(f"Bestehende {DB_PATH} gelöscht.")

    conn = get_connection()
    conn.executescript(destroy_schema)
    conn.commit()
    print("Schema zerstört.")
    conn.close()


if __name__ == "__main__":
    main()
