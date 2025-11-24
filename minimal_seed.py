import sqlite3
from datetime import datetime

DB_PATH = "grocery.db"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Bestehende Daten löschen (nur für Test!)
for table in ["order_items", "orders", "supermarket_products", "products", "supermarkets", "users"]:
    try:
        cur.execute(f"DELETE FROM {table}")
        print(f"{table} geleert.")
    except Exception as e:
        print(f"Fehler beim Leeren von {table}: {e}")

# 1 User
cur.execute(
    """
    INSERT INTO users (id, username, email, password_hash, created_at)
    VALUES (?, ?, ?, ?, ?)
    """,
    ("u1", "philip", "philip@example.com", "hash123", datetime.now().isoformat())
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
    ]
)

# 2 Produkte
cur.executemany(
    """
    INSERT INTO products (id, name, brand, category, created_by_user_id, is_user_created, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
    [
        ("p1", "Vollmilch 3.5%", "Aldi", "Milch", "u1", 0, datetime.now().isoformat()),
        ("p2", "Spaghetti 500g", "NoName", "Nudeln", "u1", 0, datetime.now().isoformat()),
    ]
)

# Preise je Supermarkt
cur.executemany(
    """
    INSERT INTO supermarket_products (id, supermarket_id, product_id, price, available, last_updated)
    VALUES (?, ?, ?, ?, ?, ?)
    """,
    [
        ("sp1", "s1", "p1", 0.95, 1, datetime.now().isoformat()),
        ("sp2", "s2", "p1", 1.05, 1, datetime.now().isoformat()),
        ("sp3", "s1", "p2", 0.79, 1, datetime.now().isoformat()),
        ("sp4", "s2", "p2", 0.89, 1, datetime.now().isoformat()),
    ]
)

conn.commit()
conn.close()

print("Minimal-Seed fertig.")
