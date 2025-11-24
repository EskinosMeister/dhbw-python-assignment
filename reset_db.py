# reset_db.py
import os
import sqlite3
from datetime import datetime

DB_PATH = "grocery.db"

schema_sql = """
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS saved_products;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS supermarket_products;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS supermarkets;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    email TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE supermarkets (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    location TEXT,
    website TEXT
);

CREATE TABLE products (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    brand TEXT,
    category TEXT,
    created_by_user_id TEXT,
    is_user_created INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (created_by_user_id) REFERENCES users(id)
);

CREATE TABLE supermarket_products (
    id TEXT PRIMARY KEY,
    supermarket_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    price REAL NOT NULL,
    available INTEGER NOT NULL DEFAULT 1,
    last_updated TEXT NOT NULL,
    FOREIGN KEY (supermarket_id) REFERENCES supermarkets(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE orders (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    order_date TEXT NOT NULL,
    supermarket_id TEXT NOT NULL,
    total_amount REAL NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (supermarket_id) REFERENCES supermarkets(id)
);

CREATE TABLE order_items (
    id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    price_at_purchase REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE saved_products (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    saved_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
"""


def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Bestehende {DB_PATH} gelöscht.")

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(schema_sql)
    conn.commit()
    print("Schema neu erstellt.")

    cur = conn.cursor()
    now = datetime.now().isoformat()

    # 1 User
    cur.execute(
        """
        INSERT INTO users (id, username, email, password_hash, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("u1", "philip", "philip@example.com", "hash123", now),
    )

    # 2 Supermärkte
    cur.executemany(
        """
        INSERT INTO supermarkets (id, name, location, website)
        VALUES (?, ?, ?, ?)
        """,
        [
            ("s1", "Aldi Süd", "Stuttgart", "https://aldi-sued.de"),
            ("s2", "Rewe", "Stuttgart", "https://rewe.de"),
        ],
    )

    # 3 Produkte
    cur.executemany(
        """
        INSERT INTO products (id, name, brand, category, created_by_user_id, is_user_created, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            ("p1", "Vollmilch 3.5%", "Aldi", "Milch", "u1", 0, now),
            ("p2", "Spaghetti 500g", "NoName", "Nudeln", "u1", 0, now),
            ("p3", "Butter 250g", "Marke X", "Butter", "u1", 0, now),
        ],
    )

    # Preise je Supermarkt
    cur.executemany(
        """
        INSERT INTO supermarket_products (id, supermarket_id, product_id, price, available, last_updated)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            ("sp1", "s1", "p1", 0.95, 1, now),
            ("sp2", "s2", "p1", 1.05, 1, now),
            ("sp3", "s1", "p2", 0.79, 1, now),
            ("sp4", "s2", "p2", 0.89, 1, now),
            ("sp5", "s1", "p3", 2.29, 1, now),
            ("sp6", "s2", "p3", 2.49, 1, now),
        ],
    )

    # 1 Beispiel-Bestellung für KPIs
    cur.execute(
        """
        INSERT INTO orders (id, user_id, order_date, supermarket_id, total_amount)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("o1", "u1", now, "s1", 25.34),
    )

    cur.executemany(
        """
        INSERT INTO order_items (id, order_id, product_id, quantity, price_at_purchase)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            ("oi1", "o1", "p1", 2, 0.95),
            ("oi2", "o1", "p2", 3, 0.79),
            ("oi3", "o1", "p3", 1, 2.29),
        ],
    )

    conn.commit()
    conn.close()
    print("Testdaten eingefügt.")
    print("Fertig. Du kannst jetzt python app.py starten.")


if __name__ == "__main__":
    main()
