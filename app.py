# app.py

from datetime import datetime, timedelta
import os
import sqlite3

from flask import Flask, render_template, request, redirect, url_for

DB_PATH = "grocery.db"


def get_connection():
    """Stellt eine Verbindung zur SQLite-Datenbank her."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


app = Flask(__name__)
app.secret_key = "dev-secret"
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
    """KPIs für den aktuellen User: Ausgaben in wählbarem Zeitraum (7/30/90 Tage)."""
    conn = get_connection()
    cur = conn.cursor()

    days_param = request.args.get("days", "30")
    try:
        days = int(days_param)
    except ValueError:
        days = 30

    if days not in (7, 30, 90):
        days = 30

    now = datetime.now()
    since = now - timedelta(days=days)

    total_row = cur.execute(
        """
        SELECT COALESCE(SUM(total_amount), 0) AS total
        FROM orders
        WHERE user_id = ?
          AND order_date >= ?
        """,
        (CURRENT_USER_ID, since.isoformat()),
    ).fetchone()
    total_amount = total_row["total"]

    by_market = cur.execute(
        """
        SELECT
            s.name AS supermarket_name,
            COUNT(o.id) AS order_count,
            SUM(o.total_amount) AS sum_amount
        FROM orders o
        JOIN supermarkets s ON s.id = o.supermarket_id
        WHERE o.user_id = ?
          AND o.order_date >= ?
        GROUP BY s.id
        ORDER BY sum_amount DESC
        """,
        (CURRENT_USER_ID, since.isoformat()),
    ).fetchall()

    by_category = cur.execute(
        """
        SELECT
            p.category AS category,
            SUM(oi.quantity * oi.price_at_purchase) AS sum_amount
        FROM order_items oi
        JOIN orders o ON o.id = oi.order_id
        JOIN products p ON p.id = oi.product_id
        WHERE o.user_id = ?
          AND o.order_date >= ?
        GROUP BY p.category
        ORDER BY sum_amount DESC
        """,
        (CURRENT_USER_ID, since.isoformat()),
    ).fetchall()

    conn.close()

    return render_template(
        "kpis.html",
        total_last_30=total_amount,
        by_market=by_market,
        by_category=by_category,
        since=since.date(),
        until=now.date(),
        days=days,
    )


if __name__ == "__main__":
    print("Starte Flask app, app.py:", os.path.abspath(__file__))
    app.run(debug=True)
