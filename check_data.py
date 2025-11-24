import sqlite3

DB_PATH = "grocery.db"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("=== Tabellen & Counts ===")
for table in ["users", "supermarkets", "products", "supermarket_products", "orders", "order_items"]:
    try:
        count = cur.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()["c"]
        print(f"{table}: {count} Zeilen")
    except Exception as e:
        print(f"{table}: FEHLER -> {e}")

print("\n=== Beispiel-Produkte ===")
try:
    rows = cur.execute("SELECT id, name, brand, category FROM products LIMIT 10").fetchall()
    for r in rows:
        print(dict(r))
except Exception as e:
    print("Fehler beim Lesen aus products:", e)

conn.close()
