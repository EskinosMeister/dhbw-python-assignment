# app.py
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3


DB_PATH = "grocery.db"


def get_connection():
    """Stellt eine Verbindung zur SQLite-Datenbank her."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


app = Flask(__name__)
app.secret_key = "dev-secret"  # für Flash-Messages, in Produktion ändern!

# Für Demo: fester User
CURRENT_USER_ID = "u1"


@app.route("/")
def index():
    return redirect(url_for("search"))


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("q", "") if request.method == "POST" else request.args.get("q", "")

    conn = get_connection()
    cur = conn.cursor()

    if query:
        sql = """
        SELECT
            p.id as product_id,
            p.name,
            p.brand,
            p.category,
            s.name AS supermarket_name,
            s.id AS supermarket_id,
            sp.price
        FROM products p
        JOIN supermarket_products sp ON sp.product_id = p.id
        JOIN supermarkets s ON s.id = sp.supermarket_id
        WHERE p.name LIKE ? OR p.category LIKE ?
        ORDER BY p.name, sp.price ASC
        """
        params = (f"%{query}%", f"%{query}%")
    else:
        # Zeige einfach alle Produkte mit Preisen, wenn keine Suche eingegeben wurde
        sql = """
        SELECT
            p.id as product_id,
            p.name,
            p.brand,
            p.category,
            s.name AS supermarket_name,
            s.id AS supermarket_id,
            sp.price
        FROM products p
        JOIN supermarket_products sp ON sp.product_id = p.id
        JOIN supermarkets s ON s.id = sp.supermarket_id
        ORDER BY p.name, sp.price ASC
        """
        params = ()

    products = cur.execute(sql, params).fetchall()
    conn.close()

    print(f"DEBUG: query='{query}', rows={len(products)}")  # zur Kontrolle im Terminal

    return render_template("search.html", query=query, products=products)


@app.route("/save_product/<product_id>")
def save_product(product_id):
    """Produkt für den aktuellen User auf die Merkliste setzen."""
    conn = get_connection()
    cur = conn.cursor()

    saved_id = f"svp_{int(datetime.now().timestamp() * 1000)}"
    now = datetime.now().isoformat()

    cur.execute(
        """
        INSERT INTO saved_products (id, user_id, product_id, saved_at)
        VALUES (?, ?, ?, ?)
        """,
        (saved_id, CURRENT_USER_ID, product_id, now),
    )

    conn.commit()
    conn.close()

    # zurück zur Seite, von der der User kam, oder zur Merkliste
    return redirect(request.referrer or url_for("saved"))



@app.route("/saved")
def saved():
    """Gespeicherte Produkte für den aktuellen User anzeigen."""
    conn = get_connection()
    sql = """
    SELECT
        sp.id,
        sp.saved_at,
        p.name,
        p.brand,
        p.category
    FROM saved_products sp
    JOIN products p ON p.id = sp.product_id
    WHERE sp.user_id = ?
    ORDER BY sp.saved_at DESC
    """
    items = conn.execute(sql, (CURRENT_USER_ID,)).fetchall()
    conn.close()

    return render_template("saved.html", items=items)



@app.route("/kpis")
def kpis():
    """KPIs:
    - Gesamt-Ausgaben im letzten Monat
    - Ausgaben nach Supermarkt im letzten Monat
    """
    conn = get_connection()
    now = datetime.utcnow()
    since = now - timedelta(days=30)

    # Gesamt-Ausgaben (Orders)
    sql_total = """
    SELECT COALESCE(SUM(total_amount), 0) as total
    FROM orders
    WHERE user_id = ?
      AND order_date >= ?
    """
    total = conn.execute(sql_total, (CURRENT_USER_ID, since.isoformat())).fetchone()["total"]

    # Ausgaben nach Supermarkt
    sql_by_market = """
    SELECT s.name, COALESCE(SUM(o.total_amount), 0) as sum_amount
    FROM orders o
    JOIN supermarkets s ON s.id = o.supermarket_id
    WHERE o.user_id = ?
      AND o.order_date >= ?
    GROUP BY s.id
    ORDER BY sum_amount DESC
    """
    by_market = conn.execute(sql_by_market, (CURRENT_USER_ID, since.isoformat())).fetchall()

    conn.close()

    return render_template("kpis.html", total=total, by_market=by_market, since=since.date(), now=now.date())


@app.route("/cheapest/<product_id>")
def cheapest(product_id):
    """Zeigt für ein Produkt: in welchem Markt ist es am günstigsten?"""
    conn = get_connection()
    sql = """
    SELECT
        p.name,
        s.name AS supermarket_name,
        sp.price
    FROM supermarket_products sp
    JOIN products p ON p.id = sp.product_id
    JOIN supermarkets s ON s.id = sp.supermarket_id
    WHERE p.id = ?
    ORDER BY sp.price ASC
    """
    cur = conn.execute(sql, (product_id,))
    rows = cur.fetchall()
    conn.close()
    if not rows:
        flash("Keine Preisinfos zu diesem Produkt.")
        return redirect(url_for("search"))

    product_name = rows[0]["name"]
    cheapest_row = rows[0]
    return render_template("cheapest.html", product_name=product_name, rows=rows, cheapest=cheapest_row)


if __name__ == "__main__":
    app.run(debug=True)
