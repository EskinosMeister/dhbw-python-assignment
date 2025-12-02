# Grocery Tracker – Preisvergleich & Einkaufsanalyse

Eine kleine Full-Stack-Webanwendung auf Basis von **Flask** und **SQLite**, mit der du:

- Lebensmittelprodukte über mehrere Supermärkte hinweg vergleichen kannst,
- eigene Einkäufe erfasst,
- Ausgaben analysierst (KPIs),
- und „Was-wäre-wenn“-Szenarien für Ersparnisse durchrechnest.

---

## Features

### 🔍 Produktsuche (`/search`)
- Suche nach Produktname oder Kategorie (z. B. „Vollmilch“, „Nudeln“).
- Vergleich der Preise aus der eigenen Datenbank (z. B. Aldi, Rewe, Lidl).
- Live-Ergänzung durch **Aldi Süd Crawler**:
  - ruft die Aldi-Süd-Webseite auf,
  - extrahiert Produktkarten,
  - liefert aktuelle Preise & Produktlinks zurück.
- Ergebnisliste kombiniert DB-Produkte und Live-Ergebnisse in einer Tabelle.
- DB-Produkte lassen sich auf die Merkliste setzen.

### ⭐ Merkliste (`/saved`)
- Produkte aus der Suche können gespeichert werden.
- Anzeige von:
  - Produktname, Marke, Kategorie,
  - günstigstem bekannten Preis,
  - Datum, an dem das Produkt gemerkt wurde.

### ➕ Manuelle Produkte anlegen (`/add_product`)
- Eigene Produkte mit:
  - Name (Pflicht),
  - Marke (optional),
  - Kategorie (optional),
  anlegen.
- Preise pro Supermarkt im Formular eingeben.
- Neue Produkte erscheinen danach in der Suche und im Vergleich.

### 🧾 Bestellungen erfassen (`/add_order`)
- Erfasse neue Einkäufe mit:
  - Datum (optional, sonst heute),
  - Supermarkt,
  - bis zu 3 Produktpositionen mit Mengen.
- Preise werden automatisch aus `supermarket_products` für den gewählten Markt gezogen.
- Es werden angelegt:
  - ein Eintrag in `orders`,
  - mehrere Einträge in `order_items`.
- Neue Bestellungen fließen direkt in KPIs und Ersparnis-Berechnung ein.

### 📊 KPIs – Ausgabenanalyse (`/kpis`)
- Zeitraum wählbar: **7 / 30 / 90 Tage**.
- Ausgabenübersicht:
  - Gesamtbetrag im Zeitraum,
  - Ausgaben nach Supermarkt (Tabelle + Balkendiagramm via Chart.js),
  - Ausgaben nach Kategorie.
- Dynamische Umschaltung des Zeitraums über Buttons.

### 💡 Ersparnis-Rechner (`/savings`)
- Zeitraum wählbar: **7 / 30 / 90 Tage**.
- Auswahl eines Referenz-Supermarkts.
- Berechnet u. a.:
  - tatsächliche Ausgaben,
  - vergleichbare Ausgaben (nur Produkte, die es auch im Referenzmarkt gibt),
  - hypothetische Ausgaben im Referenzmarkt,
  - potentielle **Ersparnis** oder **Mehrkosten**.
- Detailtabelle pro Position:
  - Ist-Preis vs. Referenz-Preis,
  - Zeilen-Differenz.

---

## Technischer Überblick

### Stack

- Backend: **Flask**
- Datenbank: **SQLite** (`grocery.db`)
- Templates: **Jinja2**
- Frontend: serverseitig gerendertes HTML + etwas inline CSS
- Diagramme: **Chart.js** (via CDN)
- Crawler: **requests + BeautifulSoup**

### Projektstruktur

```text
dhbw-python-assignment/
├─ app.py                 # Flask-App, Routing & Business-Logik
├─ grocery.db             # SQLite-Datenbank (wird erzeugt / zurückgesetzt)
├─ README.md
├─ requirements.in / .txt # Python-Abhängigkeiten
│
├─ database/
│  ├─ my_helpers.py       # get_connection(), Pfadlogik für grocery.db
│  ├─ db_init.py          # liest schema.sql und erzeugt Tabellen
│  ├─ schema.sql          # SQL-Schema aller Tabellen
│  ├─ reset_db.py         # DB-Datei löschen + Tabellen droppen
│  ├─ populate_db.py      # interaktives Menü: CSV vs. Beispieldaten
│  ├─ pop_with_csv.py     # befüllt DB aus CSV-Dateien in /data
│  └─ pop_with_example.py # befüllt DB mit fest codierten Testdaten
│
├─ scrapers/
│  └─ aldi_crawler.py     # Aldi Süd Crawler (Live-Preise)
│
├─ scripts/
│  ├─ linux/
│  │  ├─ init.sh          # Dependencies installieren, DB resetten & Schema anlegen
│  │  ├─ populate_db.sh   # ruft populate_db.py auf
│  │  └─ server-start.sh  # startet Flask-App (python app.py)
│  └─ windows/
│     ├─ init.bat
│     ├─ populate_db.bat
│     └─ server-start.bat
│
└─ templates/
   ├─ base.html           # Grundlayout & Navigation
   ├─ search.html         # Produktsuche & Preistabelle
   ├─ saved.html          # Merkliste
   ├─ add_product.html    # Produkt anlegen
   ├─ add_order.html      # Bestellung erfassen
   ├─ kpis.html           # KPI-Dashboard + Chart.js
   └─ savings.html        # Ersparnis-Analyse


Installation & Setup
1. Repository klonen
git clone <URL ZU DIESEM REPO>
cd dhbw-python-assignment

2. Virtuelle Umgebung (empfohlen)
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

3. Abhängigkeiten installieren
pip install -r requirements.txt


Datenbank vorbereiten

Es gibt zwei Wege: manuell mit Python oder über die Skripte.

Variante A: Direkt mit Python

DB zurücksetzen (falls vorhanden):

python database/reset_db.py


Schema anlegen:

python database/db_init.py


DB befüllen (interaktiv):

python database/populate_db.py


Du wirst gefragt:

1 → Befüllung aus CSV-Dateien (data/*.csv)

2 → Befüllung mit fest codierten Beispieldaten

Variante B: über Skripte
Linux
cd scripts/linux
./init.sh         # Installiert Requirements, reset_db, db_init
./populate_db.sh  # Startet populate_db.py (CSV oder Beispiele wählen)

Windows
cd scripts/windows
init.bat
populate_db.bat


Anwendung starten
Direkt mit Python

Im Projektroot:

python app.py


Die Flask-App startet im Debug-Modus (Standard: http://127.0.0.1:5000/).

Über Startskript (Linux/Windows)
# Linux
cd scripts/linux
./server-start.sh

# Windows
cd scripts/windows
server-start.bat

Wichtige Routen

/ → Redirect auf /search

/search → Produktsuche + Preisvergleich (DB + Aldi-Crawler)

/saved → Merkliste

/add_product → eigenes Produkt anlegen

/add_order → neue Bestellung erfassen

/kpis → KPI-Dashboard (7/30/90 Tage)

/savings → Ersparnis-Rechner

Aldi Süd Crawler

Ort: scrapers/aldi_crawler.py

Baut eine requests.Session mit Retry-Logik und Browser-ähnlichen HTTP-Headern.

Sucht auf der Aldi-Süd-Seite nach Produkten (search-Parameter).

Extrahiert:

Titel (inkl. Marke),

Preis,

Produktlink,

Timestamp.

Rückgabeformat (vereinfacht):

{
    "supermarket_name": "Aldi Süd",
    "name": "...",
    "brand": "...",
    "price": 0.99,
    "product_url": "...",
    "is_live": True,
    "timestamp": "2025-11-27T12:34:56"
}


In app.py werden diese Live-Ergebnisse mit den DB-Ergebnissen zusammen in search.html angezeigt.

Datenmodell (UML/ER-Diagramm)

Das Kern-Datenmodell der Anwendung besteht aus sieben Tabellen.
Das folgende Mermaid-Diagramm beschreibt die Struktur:

erDiagram
    USERS {
        string id PK
        string username
        string email
        string password_hash
        string created_at
    }

    SUPERMARKETS {
        string id PK
        string name
        string location
        string website
    }

    PRODUCTS {
        string id PK
        string name
        string brand
        string category
        string created_by_user_id FK
        int    is_user_created
        string created_at
    }

    SUPERMARKET_PRODUCTS {
        string id PK
        string supermarket_id FK
        string product_id FK
        float  price
        int    available
        string last_updated
    }

    ORDERS {
        string id PK
        string user_id FK
        string order_date
        string supermarket_id FK
        float  total_amount
    }

    ORDER_ITEMS {
        string id PK
        string order_id FK
        string product_id FK
        int    quantity
        float  price_at_purchase
    }

    SAVED_PRODUCTS {
        string id PK
        string user_id FK
        string product_id FK
        string saved_at
    }

    USERS ||--o{ PRODUCTS            : "creates (optional)"
    USERS ||--o{ ORDERS              : "places"
    USERS ||--o{ SAVED_PRODUCTS      : "saves"

    SUPERMARKETS ||--o{ SUPERMARKET_PRODUCTS : "offers"
    SUPERMARKETS ||--o{ ORDERS               : "used_for"

    PRODUCTS ||--o{ SUPERMARKET_PRODUCTS : "priced_in"
    PRODUCTS ||--o{ ORDER_ITEMS          : "contained_in"
    PRODUCTS ||--o{ SAVED_PRODUCTS       : "bookmarked_as"

    ORDERS ||--o{ ORDER_ITEMS : "has_items"


Dieses Modell entspricht 1:1 der schema.sql und bildet die Grundlage für Suche, KPIs, Ersparnis-Berechnung und Merkliste.