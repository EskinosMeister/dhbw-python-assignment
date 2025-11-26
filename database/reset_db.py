# reset_db.py
# this only works, if all resources are free. If the server uses grocery.db, the reset won't work
from my_helpers import get_connection, DB_PATH

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
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"Bestehende {DB_PATH} gelöscht.")

    conn = get_connection()
    conn.executescript(destroy_schema)
    conn.commit()
    print("Schema zerstört.")
    conn.close()


if __name__ == "__main__":
    main()
