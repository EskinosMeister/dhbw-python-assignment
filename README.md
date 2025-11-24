# Grocery Tracker – Preisvergleich & Einkaufsanalyse

Dieses Projekt ist eine kleine Full-Stack-Webanwendung auf Basis von **Flask** und **SQLite**, mit der alltägliche Lebensmittel über verschiedene Supermärkte hinweg verglichen und eigene Einkäufe ausgewertet werden können.

## Features

- 🔍 **Produktsuche**
  - Suche nach Produktnamen oder Kategorien (z. B. „Vollmilch“, „Nudeln“).
  - Anzeige aller verfügbaren Preise je Supermarkt.
  - Direktes Speichern von Produkten auf eine persönliche Merkliste.

- ⭐ **Merkliste**
  - Produkte können über die Suche auf eine Merkliste gesetzt werden.
  - Anzeige von Name, Marke, Kategorie und *Gespeichert am* (nur Datum).

- 📈 **KPIs (Auswertungen)**
  - Ausgaben über einen wählbaren Zeitraum: **7 / 30 / 90 Tage**.
  - Aufteilung der Ausgaben:
    - nach Supermarkt (Tabelle + Balkendiagramm via Chart.js),
    - nach Produktkategorien (z. B. Milch, Nudeln, Butter).
  - Zeiträume können per Button umgeschaltet werden, KPIs aktualisieren sich dynamisch.

- 💡 **Ersparnis-Rechner („Was-wäre-wenn“)**  
  Route `/savings`
  - Zeitraum wählbar (7 / 30 / 90 Tage).
  - Auswahl eines Referenz-Supermarkts (z. B. Aldi/Rewe/Lidl).
  - Vergleich:
    - tatsächliche Ausgaben in allen Märkten,
    - hypothetische Ausgaben, wenn alles im Referenzmarkt gekauft worden wäre,
    - potentielle Ersparnis oder Mehrkosten,
    - Detailtabelle pro Position (Ist-Preis vs. Referenz-Preis).

- ➕ **Manuelle Produkte hinzufügen**
  - Neues Produkt mit Name, Marke und Kategorie anlegen.
  - Preise für vorhandene Supermärkte direkt im Formular eintragen.
  - Produkt erscheint danach in der Suche (inkl. Vergleich über Märkte) und kann wie alle anderen gespeichert werden.

- 🧾 **Neue Bestellungen erfassen**
  - Formular „Neue Bestellung“:
    - Datum (optional, sonst heute),
    - Supermarkt,
    - bis zu 3 Produktpositionen mit Mengen.
  - Preise werden automatisch aus den hinterlegten `supermarket_products` gezogen.
  - Die Bestellung wird in `orders` und `order_items` gespeichert und fließt sofort in:
    - KPIs,
    - Ersparnis-Rechner,
    - zukünftige Analysen ein.

---

## Technischer Überblick

**Stack**

- Backend: [Flask](https://flask.palletsprojects.com/)
- Datenbank: SQLite (`grocery.db`)
- Templates: Jinja2 (`templates/…`)
- Frontend: klassisches serverseitiges Rendering (HTML + etwas inline CSS)
- Diagramme: [Chart.js](https://www.chartjs.org/) per CDN für Balkendiagramme

**Wichtige Dateien**

- `app.py`  
  Hauptapplikation (Flask), Routing und Business-Logik:
  - `/` → Redirect auf `/search`
  - `/search` → Produktsuche & Preisvergleich
  - `/saved` → Merkliste
  - `/kpis` → KPI-Dashboard mit Zeitraumauswahl + Diagramm
  - `/savings` → Ersparnis-Berechnung „Was wäre wenn alles bei X?“
  - `/add_product` → Produkt manuell anlegen
  - `/add_order` → Neue Bestellung erfassen

- `database.py`  
  Stellt die Verbindung zur SQLite-Datenbank bereit (Helper-Funktion `get_connection()`).

- `reset_db.py`  
  Löscht die vorhandene `grocery.db`, legt das Schema neu an und füllt die Tabellen mit Testdaten (Produkte, Supermärkte, Orders, Order-Items usw.).  
  → Praktisch, um einen definierten Ausgangszustand zu bekommen.

- `schema.sql`  
  SQL-Schema der Datenbank (Tabellen `users`, `supermarkets`, `products`, `supermarket_products`, `orders`, `order_items`, `saved_products`).

- `templates/`  
  - `base.html` – Grundlayout, Navigation, Styling.
  - `search.html` – Produktsuche & Vergleichstabelle.
  - `saved.html` – Merkliste.
  - `kpis.html` – KPI-Dashboard mit Zeitraum-Buttons + Chart.js-Diagramm.
  - `savings.html` – Ersparnis-Rechner mit Zusammenfassung & Detailtabelle.
  - `add_product.html` – Formular zum Anlegen eines neuen Produkts.
  - `add_order.html` – Formular zum Erfassen einer neuen Bestellung.
  - (optional) `cheapest.html` – Ansicht für günstigsten Markt, falls genutzt.

- `data/` (falls vorhanden)  
  CSV-Dateien mit Beispiel- oder Seed-Daten, die zum initialen Befüllen genutzt wurden.

---

## Installation & Setup

### Voraussetzungen

- Python 3.10+ (getestet mit 3.13)
- `pip` installiert

Empfohlen: virtuelles Environment (aber optional).

### 1. Abhängigkeiten installieren

Im Projektordner:

```bash
pip install flask

### Neues UML

// Grocery Tracker – aktuelles Datenmodell

title Grocery Product Comparison Platform Data Model

// ----- Tabellen -----

users [icon: user, color: yellow]{
  id string pk
  username string
  email string
  password_hash string
  created_at timestamp
}

supermarkets [icon: shopping-cart, color: green]{
  id string pk
  name string
  location string
  website string
}

products [icon: package, color: blue]{
  id string pk
  name string
  brand string
  category string
  created_by_user_id string      // u.a. für manuell angelegte Produkte
  is_user_created boolean        // true = über GUI hinzugefügt
  created_at timestamp
}

supermarket_products [icon: tag, color: orange]{
  id string pk
  supermarket_id string          // z.B. Aldi, Rewe, Lidl
  product_id string              // verweist auf products
  price decimal                  // aktueller Preis
  available boolean
  last_updated timestamp
}

orders [icon: file-text, color: purple]{
  id string pk
  user_id string                 // aktueller User (z.B. u1)
  order_date timestamp           // für 7/30/90-Tage-KPIs
  supermarket_id string          // wo wurde eingekauft
  total_amount decimal           // Summe aus den order_items
}

order_items [icon: shopping-bag, color: pink]{
  id string pk
  order_id string                // gehört zu einer Bestellung
  product_id string              // welches Produkt
  quantity integer               // Menge
  price_at_purchase decimal      // Preis zum Kaufzeitpunkt
}

saved_products [icon: star, color: gold]{
  id string pk
  user_id string                 // wem gehört_


### Altes UML

title Grocery Product Comparison Platform Data Model

// define tables
users [icon: user, color: yellow]{
  id string pk
  username string
  email string
  password_hash string
  created_at timestamp
}

supermarkets [icon: shopping-cart, color: green]{
  id string pk
  name string
  location string
  website string
}

products [icon: package, color: blue]{
  id string pk
  name string
  brand string
  category string
  created_by_user_id string
  is_user_created boolean
  created_at timestamp
}

supermarket_products [icon: tag, color: orange]{
  id string pk
  supermarket_id string
  product_id string
  price decimal
  available boolean
  last_updated timestamp
}

orders [icon: file-text, color: purple]{
  id string pk
  user_id string
  order_date timestamp
  supermarket_id string
  total_amount decimal
}

order_items [icon: shopping-bag, color: pink]{
  id string pk
  order_id string
  product_id string
  quantity integer
  price_at_purchase decimal
}

saved_products [icon: star, color: gold]{
  id string pk
  user_id string
  product_id string
  saved_at timestamp
}

// define relationships
products.created_by_user_id > users.id
supermarket_products.supermarket_id > supermarkets.id
supermarket_products.product_id > products.id
orders.user_id > users.id
orders.supermarket_id > supermarkets.id
order_items.order_id > orders.id
order_items.product_id > products.id
saved_products.user_id > users.id
saved_products.product_id > products.id