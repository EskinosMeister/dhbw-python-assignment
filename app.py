#app.py

"""
Label: Flask-Hauptanwendung (Web-Frontend & Routing)
Ersteller: Philip Welter, Jakub Nossowski, Marie Wütz
Datum: 2025-11-27
Version: 1.0.0
Lizenz: Proprietär (für Studienzwecke)

Kurzbeschreibung des Moduls:
    Dieses Modul bildet den Einstiegspunkt der Webanwendung. Es initialisiert die Flask-App,
    verwaltet alle HTTP-Routen und verbindet die Präsentationsschicht (Templates) mit der
    Persistenzschicht (SQLite-Datenbank) sowie dem Aldi-Süd-Crawler.

    Kernfunktionen:
        - Produktsuche mit kombinierten Ergebnissen aus Datenbank und Live-Crawler
        - Merkliste für Produkte des aktuellen Users
        - Erfassung neuer Produkte und Bestellungen
        - KPI-Dashboard (Ausgabenanalyse)
        - Ersparnis-Rechner („Was wäre wenn alles in einem Markt gekauft worden wäre?“)
"""

from datetime import datetime, timedelta
import os

from flask import Flask, render_template, request, redirect, url_for

from database.my_helpers import get_connection
from scrapers.aldi_crawler import scrape_aldi_sued_top

# DB_PATH = "grocery.db"  # nicht mehr benötigt, Pfad wird zentral in my_helpers.py verwaltet


# =======================
# Flask-Konfiguration
# =======================

app = Flask(__name__)
app.secret_key = "dev-secret"

# Aktuell wird mit einem statischen User gearbeitet.
# Für mehrere Nutzer wäre Session-/Auth-Management notwendig.
CURRENT_USER_ID = "u1"


# =======================
# Routen – Einstieg
# =======================

@app.route("/")
def index():
    """
    Label: Startseite / Redirect
    Kurzbeschreibung:
        Leitet den Benutzer von der Root-URL "/" direkt auf die Produktsuche (/search) um.
        Dadurch gibt es keine separate Landing-Page und der User landet sofort im Haupt-Feature.

    Parameter:
        - Keine (Request-Kontext kommt implizit von Flask)

    Return:
        flask.Response: Redirect auf die Route 'search'.

    Tests:
        1. Aufruf von "/" liefert einen HTTP-Redirect (Status 302) auf "/search".
        2. Die Route 'search' ist registriert und führt nicht zu einem 404.
    """
    return redirect(url_for("search"))


# =======================
# Routen – Suche & Merkliste
# =======================

@app.route("/search", methods=["GET", "POST"])
def search():
    """
    Label: Produktsuche & Preisvergleich
    Kurzbeschreibung:
        Ermöglicht die Suche nach Produkten über Name oder Kategorie. Es werden zunächst
        passende Produkte aus der lokalen SQLite-Datenbank geladen und anschließend
        Live-Preisangebote von Aldi Süd über den Crawler ergänzt. Beide Ergebnislisten
        werden in einer gemeinsamen Tabelle im Template 'search.html' dargestellt.

    Parameter:
        - Keine direkten Funktionsparameter.
        - Suchbegriff:
            - Bei POST: request.form["q"]
            - Bei GET: request.args["q"]

    Return:
        flask.Response: Gerendertes Template 'search.html' mit:
            - query  (str): der eingegebene Suchbegriff
            - products (list): kombinierte Liste aus DB-Records und Aldi-Live-Dicts

    Tests:
        1. Ohne Suchbegriff (GET /search) werden alle DB-Produkte mit Preisen angezeigt.
        2. Mit Suchbegriff werden nur Produkte angezeigt, deren Name oder Kategorie LIKE '%q%' matcht.
        3. Bei einem gültigen Suchbegriff wird zusätzlich scrape_aldi_sued_top(query) aufgerufen
           und die Ergebnisse in der Tabelle angezeigt (erkennbar an is_live = True).
    """
    # Suchbegriff abhängig von HTTP-Methode ermitteln
    query = (
        request.form.get("q", "")
        if request.method == "POST"
        else request.args.get("q", "")
    )

    conn = get_connection()
    cur = conn.cursor()

    # SQL-Query abhängig davon, ob ein Suchbegriff vorhanden ist
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

    # DB-Ergebnisse laden
    products = cur.execute(sql, params).fetchall()
    conn.close()

    # Live-Ergebnisse von Aldi Süd hinzufügen (falls query leer, wird i. d. R. eine leere Liste zurückgegeben)
    aldi_results = scrape_aldi_sued_top(query)
    for result in aldi_results:
        products.append(result)

    return render_template("search.html", query=query, products=products)


@app.route("/save_product/<product_id>")
def save_product(product_id: str):
    """
    Label: Produkt auf Merkliste setzen
    Kurzbeschreibung:
        Fügt ein vorhandenes Produkt (aus der products-Tabelle) für den aktuellen User
        in die Merkliste (saved_products) ein. Der Eintrag enthält einen technischen
        Primärschlüssel, den User, das Produkt und einen Timestamp.

    Parameter:
        product_id (str): Primärschlüssel des Produkts aus der Tabelle 'products'.

    Return:
        flask.Response:
            Redirect zurück auf die vorherige Seite (request.referrer) oder,
            falls diese nicht verfügbar ist, auf die Merkliste (/saved).

    Tests:
        1. Aufruf mit existierendem product_id erzeugt genau einen Eintrag in saved_products.
        2. Mehrfaches Speichern desselben Produkts ist möglich und erzeugt mehrere Einträge.
        3. Nach dem Speichern wird ein Redirect ausgeführt (kein reines 200-Response).
    """
    conn = get_connection()
    cur = conn.cursor()

    # Einfache ID-Erzeugung basierend auf aktueller Zeit (Millisekunden)
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
    Label: Merkliste anzeigen
    Kurzbeschreibung:
        Zeigt alle für den aktuellen User gespeicherten Produkte aus 'saved_products'
        an. Zusätzlich wird für jedes Produkt der günstigste bekannte Preis aus
        'supermarket_products' berechnet (MIN-Preis).

    Parameter:
        - Keine direkten Funktionsparameter (User wird über CURRENT_USER_ID bestimmt).

    Return:
        flask.Response: Gerendertes Template 'saved.html' mit:
            - items (list[sqlite3.Row]): Name, Marke, Kategorie, min_price, saved_at.

    Tests:
        1. Für einen User ohne gespeicherte Produkte wird eine leere Liste/Empty-State angezeigt.
        2. Für gespeicherte Produkte wird der korrekte MIN-Preis angezeigt.
        3. Die Einträge sind absteigend nach gespeicherten Datum sortiert (neueste zuerst).
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


# =======================
# Routen – Produkt & Bestellung anlegen
# =======================

@app.route("/add_product", methods=["GET", "POST"])
def add_product():
    """
    Label: Neues Produkt anlegen
    Kurzbeschreibung:
        Ermöglicht es dem User, ein eigenes Produkt anzulegen und für bestehende Supermärkte
        Preise zu hinterlegen. Die Daten werden in 'products' und 'supermarket_products'
        gespeichert und stehen anschließend in der Suche und im Vergleich zur Verfügung.

    Parameter:
        - Keine direkt über Funktionsparameter; Werte kommen aus request.form.

    Return:
        flask.Response:
            - GET: Rendert 'add_product.html' mit Supermarkt-Liste.
            - POST (erfolgreich): Redirect auf '/search' mit Query = Produktname.
            - POST (Fehler, z. B. leerer Name): Rendert Formular mit Fehlermeldung.

    Tests:
        1. GET /add_product liefert das Formular mit allen Supermärkten.
        2. POST mit validem Namen erzeugt einen Eintrag in 'products' und optional Einträge
           in 'supermarket_products'.
        3. POST mit leerem Namen zeigt das Formular erneut mit der Fehlermeldung "Name darf nicht leer sein.".
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
            return render_template(
                "add_product.html",
                supermarkets=supermarkets,
                error="Name darf nicht leer sein.",
            )

        now = datetime.now().isoformat()
        product_id = f"up_{int(datetime.now().timestamp() * 1000)}"

        # Produktstammsatz anlegen
        cur.execute(
            """
            INSERT INTO products (id, name, brand, category, created_by_user_id, is_user_created, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (product_id, name, brand, category, CURRENT_USER_ID, 1, now),
        )

        # Preise je Supermarkt aus Formular einlesen
        for s in supermarkets:
            field_name = f"price_{s['id']}"
            price_str = request.form.get(field_name, "").strip()
            if not price_str:
                continue

            # Komma oder Punkt als Dezimaltrennzeichen erlauben
            try:
                price = float(price_str.replace(",", "."))
            except ValueError:
                # Ungültiger Preis → ignorieren
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


@app.route("/add_order", methods=["GET", "POST"])
def add_order():
    """
    Label: Neue Bestellung erfassen
    Kurzbeschreibung:
        Erfasst eine neue Bestellung für den aktuellen User. Der User wählt einen
        Supermarkt, optional ein Datum und bis zu drei Produktpositionen mit Mengen.
        Die Preise werden automatisch aus 'supermarket_products' für den gewählten Markt
        gelesen. Es entstehen ein Eintrag in 'orders' sowie mehrere Einträge in
        'order_items'.

    Parameter:
        - Keine direkten Funktionsparameter; Formwerte kommen aus request.form.

    Return:
        flask.Response:
            - GET: Rendert 'add_order.html' mit Listen von Supermärkten und Produkten.
            - POST (erfolgreich): Redirect auf '/kpis?days=30'.
            - POST (Fehler): Rendert Formular mit Fehlermeldung.

    Tests:
        1. GET /add_order liefert das Formular mit allen Supermärkten und Produkten.
        2. POST mit gültigem Supermarkt und mindestens einer Position mit Preis erzeugt
           einen Eintrag in 'orders' und die passenden 'order_items'.
        3. POST ohne gültige Position oder ohne Supermarkt zeigt eine Fehlermeldung:
           "Bitte Supermarkt wählen und mindestens eine gültige Position mit Preis angeben."
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

            # Preis im gewählten Supermarkt holen (letzter Stand per last_updated)
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

        # Nach neuer Bestellung direkt zu den KPIs (Standard: 30 Tage)
        return redirect(url_for("kpis", days=30))

    # GET: Formular anzeigen
    conn.close()
    return render_template(
        "add_order.html",
        supermarkets=supermarkets,
        products=products,
        error=error,
    )


# =======================
# Routen – KPIs & Ersparnis
# =======================

@app.route("/kpis")
def kpis():
    """
    Label: KPI-Dashboard (Ausgabenanalyse)
    Kurzbeschreibung:
        Liefert Kennzahlen zu den Ausgaben des aktuellen Users in einem wählbaren
        Zeitraum (7, 30 oder 90 Tage). Es werden Gesamtausgaben, Ausgaben pro
        Supermarkt und Ausgaben pro Produktkategorie berechnet und im Template
        'kpis.html' in Tabellenform und als Balkendiagramm (Chart.js) dargestellt.

    Parameter:
        - days (Query-Parameter, optional, str):
            "7", "30" oder "90". Standard: "30".

    Return:
        flask.Response: Gerendertes Template 'kpis.html' mit:
            - total_last_30 (float): Gesamtausgaben im Zeitraum (Name historisch),
            - by_market (list[sqlite3.Row]): Ausgaben nach Supermarkt,
            - by_category (list[sqlite3.Row]): Ausgaben nach Kategorie,
            - since (date), until (date): Datumsgrenzen,
            - days (int): tatsächlich verwendeter Zeitraum.

    Tests:
        1. Ungültiger days-Parameter (z. B. "abc") wird auf 30 Tage normalisiert.
        2. Ohne Orders im Zeitraum sind Summen 0 und Tabellen leer.
        3. Mit vorhandenen Orders stimmen Summen und Gruppierungen mit der Datenbank überein.
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

    # Gesamtausgaben im Zeitraum
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

    # Ausgaben nach Supermarkt
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

    # Ausgaben nach Produktkategorie
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
    Label: Ersparnis-Rechner („Was-wäre-wenn“-Analyse)
    Kurzbeschreibung:
        Berechnet, wie sich die Ausgaben des aktuellen Users verändert hätten, wenn
        alle Einkäufe im Zeitraum bei einem bestimmten Referenz-Supermarkt getätigt
        worden wären. Verglichen werden:
            - tatsächliche Ausgaben,
            - vergleichbare Ausgaben (nur Produkte, die im Referenzmarkt verfügbar sind),
            - hypothetische Ausgaben im Referenzmarkt,
            - potentielle Ersparnis oder Mehrkosten.

    Parameter:
        - days (Query-Parameter, optional, str): Zeitraum in Tagen (7, 30, 90), Standard 30.
        - market_id (Query-Parameter, optional, str): ID des Referenz-Supermarkts.
          Falls nicht gesetzt oder ungültig, wird der erste Markt aus der DB verwendet.

    Return:
        flask.Response: Gerendertes Template 'savings.html' mit:
            - supermarkets (list[sqlite3.Row]): Liste aller Märkte,
            - selected_market_id (str): effektiver Referenzmarkt,
            - days (int), since (date), until (date),
            - rows (list[sqlite3.Row]): Detailpositionen mit Ist- und Referenzpreisen,
            - actual_total (float): tatsächliche Ausgaben im Zeitraum,
            - comparable_actual_total (float): Ausgaben für vergleichbare Positionen,
            - alt_total (float): hypothetische Ausgaben im Referenzmarkt,
            - skipped_total (float): Summe der nicht vergleichbaren Positionen,
            - potential_saving (float): > 0 = Referenzmarkt wäre günstiger gewesen.

    Tests:
        1. Ohne bestehende Orders im Zeitraum sind alle Summen 0 und es gibt keine Detailzeilen.
        2. Wenn market_id fehlt oder ungültig ist, wird automatisch der erste Markt gewählt.
        3. Für Produkte ohne Preis im Referenzmarkt wird deren Wert in skipped_total addiert
           und in den Detailzeilen als „–“ dargestellt.
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

    # > 0 = Referenzmarkt wäre günstiger gewesen
    potential_saving = comparable_actual_total - alt_total

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


# =======================
# Main-Einstieg
# =======================

if __name__ == "__main__":
    """
    Label: Lokaler Startpunkt
    Kurzbeschreibung:
        Startet die Flask-Anwendung im Debug-Modus, wenn app.py direkt über den
        Python-Interpreter ausgeführt wird. Geeignet für lokale Entwicklung und Tests.

    Tests:
        1. Ausführung von `python app.py` startet einen Entwicklungsserver auf
           http://127.0.0.1:5000/ (Standard-Flask-Port).
        2. Änderungen am Code werden im Debug-Modus automatisch neu geladen.
    """
    print("Starte Flask app, app.py:", os.path.abspath(__file__))
    app.run(debug=True)
