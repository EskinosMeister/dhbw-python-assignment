# app.py
""" 
Label: Zentrale Flask Anwendung
Ersteller: Welter Philip, Jakub Nossowski, Marie Wuetz
Datum: 2025-11-26
Version: 1.0.0
Lizenz: Proprietär (für Studienzwecke)

Kurzbeschreibung des Moduls:
    Stellt die zentrale Flask-Anwendung für ein userbezogenes Produkt- und Einkaufsverwaltungssystem bereit.
    
    Die Anwendung dient dem Erfassen von Produkten, dem Preisvergleich zwischen Supermärkten und der 
    Berechnung wirtschaftlicher Kennzahlen (KPIs und Einsparpotenziale). Alle Daten werden 
    userbezogen in einer SQLite-Datenbank gespeichert.

"""
from datetime import datetime, timedelta
import os
import sqlite3

from flask import Flask, render_template, request, redirect, url_for

DB_PATH = "grocery.db"


def get_connection():
    """
   Label: Datenbank-Verbindung herstellen
    Kurzbeschreibung:
        Erstellt und konfiguriert eine Verbindung zur SQLite-Datenbank, wie in DB_PATH definiert.
        Die Konfiguration umfasst das Setzen der Row-Factory für den Spaltennamen-Zugriff 
        und das Aktivieren von Foreign Keys.

    Parameter:
        - Keine

    Return:
        sqlite3.Connection: Die konfigurierte Datenbank-Verbindung.

    Tests:
        1. Verbindung herstellen: Erwartet eine gültige DB-Verbindung ohne Exception.
        2. Row Factory-Check: Zugriff auf conn.row_factory liefert sqlite3.Row.

    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


app = Flask(__name__)
app.secret_key = "dev-secret"
CURRENT_USER_ID = "u1"


@app.route("/")
def index():
    """
    Label: Startseiten-Weiterleitung
    Kurzbeschreibung:
        Startseite der Anwendung, die automatisch zur Produktsuche (/search) weiterleitet, 
        um einen direkten Einstiegspunkt in die Hauptfunktionalität zu bieten.

    Parameter:
        - Keine

    Return:
        werkzeug.wrappers.Response: HTTP-Redirect zur /search-Seite.

    Tests:
        1. Aufruf von "/": Erfolgt ein HTTP-Redirect zu /search.
        2. Browser Refresh: Bleibt nach dem Redirect auf der Zielseite (search).

    """
    return redirect(url_for("search"))


@app.route("/search", methods=["GET", "POST"])
def search():
    """
   Label: Produktsuche
    Kurzbeschreibung:
        Ermöglicht die Suche nach Produkten mittels Name oder Kategorie und zeigt die Ergebnisse 
        sortiert nach Produktname und Preis (günstigster zuerst) an. 
        Die Abfrage erfolgt dynamisch basierend auf dem Suchbegriff.

    Parameter:
        q (str, optional): Der Suchbegriff. Kann via POST-Formular ('q') oder 
                           GET-Query-Parameter ('q') übermittelt werden. Default ist ein leerer String.

    Return:
        werkzeug.wrappers.Response: Renderte HTML-Seite "search.html" mit der gefilterten Produktliste.
       
    Tests:
        1. Suche nach "Milch": Nur passende Produkte (Milchprodukte, Milch-Kategorie) erscheinen.
        2. Leere Suche: Alle verfügbaren Produkte werden angezeigt.
    
    """
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
    """
    Label: Produkt speichern
    Kurzbeschreibung:
        Speichert ein Produkt anhand seiner ID in der Merkliste des aktuellen Users. 
        Ein Zeitstempel und eine eindeutige ID werden generiert und in 'saved_products' gespeichert.

    Parameter:
        product_id (str): Die ID des Produkts, das gespeichert werden soll (Teil der URL).

    Return:
        werkzeug.wrappers.Response: HTTP-Redirect zur vorherigen Seite (request.referrer) oder 
                                    standardmäßig zu /saved.

    Tests:
        1. Produkt speichern: Produkt erscheint in der /saved-Liste.
        2. Doppelte Speicherung: Ein neuer Eintrag wird in der Datenbank erzeugt (keine Duplikatprüfung in der Logik).
    
    """
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
    """
   Label: Gespeicherte Produkte anzeigen
    Kurzbeschreibung:
        Zeigt alle vom aktuellen User gespeicherten Produkte in der Merkliste an. 
        Die Liste enthält zusätzlich den minimalen Marktpreis des jeweiligen Produkts 
        und ist absteigend nach dem Speicherzeitpunkt sortiert.

    Parameter:
        - Keine

    Return:
        werkzeug.wrappers.Response: Renderte HTML-Seite "saved.html" mit der Liste der gespeicherten Produkte.

    Tests:
        1. Nutzer ohne gespeicherte Produkte: Eine leere Liste wird korrekt angezeigt.
        2. Mehrere gespeicherte Produkte: Korrekte Sortierung nach Speicherdatum und Anzeige des Minimalpreises.
        
    
    """
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

    return render_template("saved.html", items=items)



@app.route("/add_product", methods=["GET", "POST"])
def add_product():
    """
    Label: Produkt hinzufügen
    Kurzbeschreibung:
        Ermöglicht dem User, ein neues Produkt manuell anzulegen und die aktuellen Preise 
        für alle erfassten Supermärkte zu hinterlegen.

    Parameter:
        GET: Keine Parameter. Zeigt das Formular an.
        POST:
            name (str): Produktname (erforderlich).
            brand (str): Marke (optional).
            category (str): Kategorie (optional).
            price_{s_id} (str, optional): Preis für den Supermarkt mit ID s_id (z.B. price_s1). 
                                         Punkt oder Komma als Dezimaltrennzeichen erlaubt.

    Return:
        werkzeug.wrappers.Response: Bei GET oder Fehler: Renderte HTML-Seite "add_product.html" mit Formular.
                                    Bei Erfolg: HTTP-Redirect zur /search-Seite mit dem neuen Produktnamen.

    Tests:
        1. Neues Produkt mit Name + Marke + Kategorie + Preise: Erfolgreich in DB gespeichert.
        2. Name leer: Formular wird mit Fehlermeldung angezeigt.
        3. Ungültiger Preis (z.B. Text): Preis wird ignoriert, Produkt wird trotzdem gespeichert.
    
        """
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
            return render_template("add_product.html", supermarkets=supermarkets, error="Name darf nicht leer sein.")

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
    return render_template("add_product.html", supermarkets=supermarkets, error=None)


@app.route("/kpis")
def kpis():
    """
    Label: KPIs berechnen und anzeigen
    Kurzbeschreibung:
        Berechnet die wichtigsten Leistungskennzahlen (KPIs) für den aktuellen User, 
        basierend auf Bestellungen innerhalb eines wählbaren Zeitraums (Standard: 30 Tage). 
        Enthaltene KPIs: Gesamtausgaben, Ausgaben pro Supermarkt und Ausgaben pro Kategorie.

    Parameter:
        days (int, optional): Der Zeitraum in Tagen (7, 30, 90). Default ist 30.

    Return:
        werkzeug.wrappers.Response: Renderte HTML-Seite "kpis.html" mit den berechneten Kennzahlen.

    Tests:
        1. Zeitraum 30 Tage: Die Gesamtbeträge der Bestellungen im 30-Tage-Fenster sind korrekt.
        2. Zeitraum 7 Tage: Der Gesamtbetrag ist kleiner oder gleich dem des 30-Tage-Zeitraums.
    """
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


@app.route("/savings")
def savings():
    """
    Label: Einsparpotenzial berechnen
    Kurzbeschreibung:
        Berechnet das hypothetische Einsparpotenzial für den User. Dazu wird verglichen, 
        was der User tatsächlich ausgegeben hat, im Vergleich zu dem, was die gleichen 
        Einkäufe beim Referenz-Supermarkt gekostet hätten.

    Parameter:
        days (int, optional): Zeitraum in Tagen (7, 30, 90). Default ist 30.
        market_id (str, optional): ID des ausgewählten Referenz-Supermarkts. Default ist der erste Supermarkt in der Liste.

    Return:
        werkzeug.wrappers.Response: Renderte HTML-Seite "savings.html" mit den Berechnungsdetails und dem Einsparpotenzial.

    Tests:
        1. Alle Preise für Referenz-Supermarkt vorhanden: Die berechnete potential_saving ist größer 0, wenn der Referenz-Supermarkt günstiger war.
        2. Referenz-Supermarkt hat teilweise keine Preise: skipped_total ist größer 0.
    """
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
        "savings.html",
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
    """
    Label: Bestellung erfassen
    Kurzbeschreibung:
       Ermöglicht das Erfassen einer neuen Bestellung des Users, inklusive Supermarkt, 
       Bestelldatum und bis zu drei Bestellpositionen (Produkte mit Mengen).
       Der Preis wird dabei aus den aktuell gespeicherten Supermarktpreisen entnommen.

    Parameter:
        GET: Keine Parameter. Zeigt das Bestellformular an.
        POST:
            supermarket_id (str): ID des gewählten Supermarkts.
            order_date (str, optional): Datum der Bestellung (Format: YYYY-MM-DD). Default ist heute.
            product_1..3 (str, optional): ID des gewählten Produkts.
            qty_1..3 (str, optional): Menge des gewählten Produkts (ganze Zahl > 0).

    Return:
        werkzeug.wrappers.Response: Bei GET oder Fehler: Renderte HTML-Seite "add_order.html" mit Formular und Fehlermeldung.
                                    Bei Erfolg: HTTP-Redirect zur /kpis-Seite (30 Tage).

    Tests:
        1. Bestellung mit 2 Produkten: total_amount korrekt basierend auf Produktpreisen und Mengen berechnet.
        2. Keine gültigen Produkte ausgewählt: Formular wird mit entsprechender Fehlermeldung zurückgegeben.
        
          """
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
                    "add_order.html",
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
                "add_order.html",
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
        "add_order.html",
        supermarkets=supermarkets,
        products=products,
        error=error,
    )




if __name__ == "__main__":
    print("Starte Flask app, app.py:", os.path.abspath(__file__))
    app.run(debug=True)
