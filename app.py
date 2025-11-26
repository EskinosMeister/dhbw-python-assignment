# app.py

from datetime import datetime, timedelta
import os

from flask import Flask, render_template, request, redirect, url_for

from database.my_helpers import get_connection

#DB_PATH = "grocery.db"

app = Flask(__name__)
app.secret_key = "dev-secret"
# this is hardcoded for one user... Should work for multiple users. This requires session management.
CURRENT_USER_ID = "u1"


@app.route("/")
def index():
    return redirect(url_for("search"))


@app.route("/search", methods=["GET", "POST"])
def search():
    # I don't why we would get either GET or POST access methods
    query = request.form.get("q", "") if request.method == "POST" else request.args.get("q", "")

    conn = get_connection()
    cur = conn.cursor()

    # I don't understand how we could have no query at all
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

    return render_template("template/search.html", query=query, products=products)


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
    """Gespeicherte Produkte für den aktuellen User anzeigen (inkl. günstigstem Preis)."""
    conn = get_connection()
    sql = """
    SELECT
        sp.id,
        sp.saved_at,
        p.name,
        p.brand,
        p.category,
        MIN(spm.price) AS min_price
    FROM saved_products sp
    JOIN products p ON p.id = sp.product_id
    LEFT JOIN supermarket_products spm ON spm.product_id = p.id
    WHERE sp.user_id = ?
    GROUP BY
        sp.id,
        sp.saved_at,
        p.name,
        p.brand,
        p.category
    ORDER BY sp.saved_at DESC
    """
    items = conn.execute(sql, (CURRENT_USER_ID,)).fetchall()
    conn.close()

    return render_template("template/saved.html", items=items)



@app.route("/add_product", methods=["GET", "POST"])
def add_product():
    """Neues Produkt manuell anlegen und Preise je Supermarkt hinterlegen."""
    conn = get_connection()
    cur = conn.cursor()

    # Supermärkte für Formular laden
    supermarkets = cur.execute(
        "SELECT id, name FROM supermarkets ORDER BY name"
    ).fetchall()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        brand = request.form.get("brand", "").strip() or None
        category = request.form.get("category", "").strip() or None

        if not name:
            # Minimal: bei fehlendem Namen einfach wieder Formular zeigen
            conn.close()
            return render_template("template/add_product.html", supermarkets=supermarkets, error="Name darf nicht leer sein.")

        now = datetime.now().isoformat()
        product_id = f"up_{int(datetime.now().timestamp() * 1000)}"

        # Produkt selbst anlegen
        cur.execute(
            """
            INSERT INTO products (id, name, brand, category, created_by_user_id, is_user_created, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (product_id, name, brand, category, CURRENT_USER_ID, 1, now),
        )

        # Preise je Supermarkt aus Formular
        for s in supermarkets:
            field_name = f"price_{s['id']}"
            price_str = request.form.get(field_name, "").strip()
            if not price_str:
                continue
            # Komma oder Punkt erlauben
            try:
                price = float(price_str.replace(",", "."))
            except ValueError:
                continue

            sp_id = f"spu_{s['id']}_{product_id}"
            cur.execute(
                """
                INSERT INTO supermarket_products (id, supermarket_id, product_id, price, available, last_updated)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (sp_id, s["id"], product_id, price, 1, now),
            )

        conn.commit()
        conn.close()

        # Danach direkt zur Suche mit dem neuen Produktnamen
        return redirect(url_for("search", q=name))

    # GET: Formular anzeigen
    conn.close()
    return render_template("template/add_product.html", supermarkets=supermarkets, error=None)


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
        "template/kpis.html",
        total_last_30=total_amount,
        by_market=by_market,
        by_category=by_category,
        since=since.date(),
        until=now.date(),
        days=days,
    )


@app.route("/savings")
def savings():
    """Ersparnis, wenn alle Einkäufe bei einem gewählten Supermarkt gemacht worden wären."""
    conn = get_connection()
    cur = conn.cursor()

    # Zeitraum wie bei KPIs
    days_param = request.args.get("days", "30")
    try:
        days = int(days_param)
    except ValueError:
        days = 30
    if days not in (7, 30, 90):
        days = 30

    now = datetime.now()
    since = now - timedelta(days=days)

    # verfügbare Supermärkte laden
    supermarkets = cur.execute(
        "SELECT id, name FROM supermarkets ORDER BY name"
    ).fetchall()

    selected_market_id = request.args.get("market_id")
    if supermarkets:
        valid_ids = [s["id"] for s in supermarkets]
        if not selected_market_id or selected_market_id not in valid_ids:
            selected_market_id = supermarkets[0]["id"]
    else:
        selected_market_id = None

    rows = []
    actual_total = 0.0
    comparable_actual_total = 0.0
    alt_total = 0.0
    skipped_total = 0.0

    if selected_market_id:
        rows = cur.execute(
            """
            SELECT
                oi.order_id,
                o.order_date,
                o.supermarket_id,
                s.name AS actual_supermarket_name,
                p.id AS product_id,
                p.name AS product_name,
                p.category,
                oi.quantity,
                oi.price_at_purchase,
                sp_ref.price AS ref_price
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            JOIN supermarkets s ON s.id = o.supermarket_id
            JOIN products p ON p.id = oi.product_id
            LEFT JOIN supermarket_products sp_ref
              ON sp_ref.product_id = p.id
             AND sp_ref.supermarket_id = ?
            WHERE o.user_id = ?
              AND o.order_date >= ?
            """,
            (selected_market_id, CURRENT_USER_ID, since.isoformat()),
        ).fetchall()

        for r in rows:
            line_actual = r["quantity"] * r["price_at_purchase"]
            actual_total += line_actual

            if r["ref_price"] is not None:
                line_alt = r["quantity"] * r["ref_price"]
                alt_total += line_alt
                comparable_actual_total += line_actual
            else:
                skipped_total += line_actual

    conn.close()

    potential_saving = comparable_actual_total - alt_total  # > 0 = Ref-Supermarkt wäre günstiger

    return render_template(
        "template/savings.html",
        supermarkets=supermarkets,
        selected_market_id=selected_market_id,
        days=days,
        since=since.date(),
        until=now.date(),
        rows=rows,
        actual_total=actual_total,
        comparable_actual_total=comparable_actual_total,
        alt_total=alt_total,
        skipped_total=skipped_total,
        potential_saving=potential_saving,
    )

@app.route("/add_order", methods=["GET", "POST"])
def add_order():
    """Neue Bestellung erfassen: Supermarkt, Datum, mehrere Produkt-Positionen."""
    conn = get_connection()
    cur = conn.cursor()

    # Supermärkte und Produkte für Formular laden
    supermarkets = cur.execute(
        "SELECT id, name FROM supermarkets ORDER BY name"
    ).fetchall()
    products = cur.execute(
        "SELECT id, name, brand FROM products ORDER BY name"
    ).fetchall()

    error = None

    if request.method == "POST":
        supermarket_id = request.form.get("supermarket_id")
        date_str = request.form.get("order_date", "").strip()

        # Datum: wenn leer, heute; ansonsten YYYY-MM-DD erwarten
        if date_str:
            try:
                dt = datetime.fromisoformat(date_str)
            except ValueError:
                error = "Datum muss im Format JJJJ-MM-TT sein."
                return render_template(
                    "template/add_order.html",
                    supermarkets=supermarkets,
                    products=products,
                    error=error,
                )
        else:
            dt = datetime.now()
        order_date_iso = dt.isoformat()

        # Bestellpositionen einsammeln (3 Zeilen als einfache Variante)
        items = []
        for i in range(1, 4):
            product_id = request.form.get(f"product_{i}")
            qty_str = request.form.get(f"qty_{i}", "").strip()

            if not product_id or not qty_str:
                continue

            try:
                qty = int(qty_str)
            except ValueError:
                continue
            if qty <= 0:
                continue

            # Preis im gewählten Supermarkt holen
            row = cur.execute(
                """
                SELECT price
                FROM supermarket_products
                WHERE supermarket_id = ? AND product_id = ?
                ORDER BY last_updated DESC
                LIMIT 1
                """,
                (supermarket_id, product_id),
            ).fetchone()

            if row is None:
                # Kein Preis → wir ignorieren die Position
                continue

            price = row["price"]
            items.append((product_id, qty, price))

        if not supermarket_id or not items:
            error = "Bitte Supermarkt wählen und mindestens eine gültige Position mit Preis angeben."
            return render_template(
                "template/add_order.html",
                supermarkets=supermarkets,
                products=products,
                error=error,
            )

        # Order-ID und Gesamtbetrag berechnen
        order_id = f"o_{int(datetime.now().timestamp() * 1000)}"
        total_amount = sum(qty * price for _, qty, price in items)

        # Bestellung anlegen
        cur.execute(
            """
            INSERT INTO orders (id, user_id, order_date, supermarket_id, total_amount)
            VALUES (?, ?, ?, ?, ?)
            """,
            (order_id, CURRENT_USER_ID, order_date_iso, supermarket_id, total_amount),
        )

        # Order-Items anlegen
        for idx, (product_id, qty, price) in enumerate(items, start=1):
            item_id = f"oi_{order_id}_{idx}"
            cur.execute(
                """
                INSERT INTO order_items (id, order_id, product_id, quantity, price_at_purchase)
                VALUES (?, ?, ?, ?, ?)
                """,
                (item_id, order_id, product_id, qty, price),
            )

        conn.commit()
        conn.close()

        # Nach neuer Bestellung direkt zu KPIs (z. B. 30 Tage)
        return redirect(url_for("kpis", days=30))

    # GET: Formular anzeigen
    conn.close()
    return render_template(
        "template/add_order.html",
        supermarkets=supermarkets,
        products=products,
        error=error,
    )




if __name__ == "__main__":
    print("Starte Flask app, app.py:", os.path.abspath(__file__))
    app.run(debug=True)
