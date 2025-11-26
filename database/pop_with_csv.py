# pop_with_csv.py
import csv
from pathlib import Path

from db_init import get_connection

def load_csv(table_name, csv_path):
    conn = get_connection()
    path = Path(csv_path)
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        return

    cols = rows[0].keys()
    placeholders = ",".join(["?"] * len(cols))
    col_list = ",".join(cols)

    # creates a cursor automatically under the hood, making get_cursor redundant here
    conn.executemany(
        f"INSERT INTO {table_name} ({col_list}) VALUES ({placeholders})",
        [[row[c] for c in cols] for row in rows],
    )
    conn.commit()
    conn.close()


def seed_data():
    load_csv("users", "../data/users.csv")
    load_csv("supermarkets", "../data/supermarkets.csv")
    load_csv("products", "../data/products.csv")
    load_csv("supermarket_products", "../data/supermarket_products.csv")
    load_csv("orders", "../data/orders.csv")
    load_csv("order_items", "../data/order_items.csv")



if __name__ == "__main__":
    seed_data()
    print("DB mit .csv daten befüllt.")
