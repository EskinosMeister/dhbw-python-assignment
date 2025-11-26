# database.py
"""
Label: Datenbank-Management-Skript
Ersteller: Philip Welter, Jakub Nossowski, Marie Wuetz
Datum: 2025-11-26
Version: 1.0.0
Lizenz: Proprietär (für Studienzwecke)

Kurzbeschreibung des Moduls:
    Dieses Skript verwaltet die SQLite-Datenbank (grocery.db). Es stellt Kernfunktionen zur 
    Initialisierung der Datenbankstruktur, zum Aufbau von Verbindungen und zum Laden von 
    Anfangsdaten (Seeding) aus CSV-Dateien bereit.

"""
import sqlite3
import csv
from pathlib import Path

DB_PATH = "grocery.db"


def get_connection():
    """
   Label: Datenbank-Verbindung herstellen
    Kurzbeschreibung:
        Öffnet eine Verbindung zur SQLite-Datenbank, wie in DB_PATH definiert. 
        Die Verbindung wird so konfiguriert, dass Zeilen als `sqlite3.Row` zurückgegeben 
        werden (Zugriff über Spaltennamen) und Foreign Keys aktiviert sind.

    Parameter:
        - Keine

    Return:
        sqlite3.Connection: Die konfigurierte Datenbank-Verbindung.

    Tests:
        1. Verbindung herstellen: Erwartet eine gültige DB-Verbindung.
        2. Konfigurations-Check: Foreign Keys sind aktiviert und Row Factory ist auf sqlite3.Row gesetzt.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """  
     Label: Datenbankstruktur initialisieren
    Kurzbeschreibung:
        Initialisiert die Datenbankstruktur, indem das SQL-Schema aus der Datei 
        'schema.sql' ausgeführt wird.

    Parameter:
        - Keine

    Return:
        - Keine (Funktion führt Operationen auf der DB durch)

    Tests:
        1. Ausführung: 'schema.sql' wird erfolgreich ausgeführt und die Tabellenstruktur wird erstellt.
        2. Existenz: Die Datenbankdatei `grocery.db` wird bei Erstausführung erstellt.
        
        """
    conn = get_connection()
    with open("schema.sql", "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


def load_csv(table_name, csv_path):
    """
    Label: Daten aus CSV laden
    Kurzbeschreibung:
        Lädt Daten aus einer angegebenen CSV-Datei in eine spezifische Zieltabelle der Datenbank. 
        Die Spaltennamen der CSV-Datei müssen mit den Spaltennamen der Zieltabelle übereinstimmen.

    Parameter:
        table_name (str): Der Name der Zieltabelle in der Datenbank.
        csv_path (str | Path): Der Dateipfad zur Quell-CSV-Datei.

    Return:
        - Keine (Funktion fügt Daten in die Tabelle ein)

    Tests:
        1. Dateneinfügung: Zeilen werden erfolgreich in die angegebene Tabelle eingefügt und committed.
        2. Leere Datei: Eine leere oder ungültige CSV-Datei führt nicht zu einem Fehler und es werden keine Zeilen eingefügt.

    """
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

    conn.executemany(
        f"INSERT INTO {table_name} ({col_list}) VALUES ({placeholders})",
        [[row[c] for c in cols] for row in rows],
    )
    conn.commit()
    conn.close()


def seed_data():
    """
    Label: Datenbank mit Beispieldaten befüllen
    Kurzbeschreibung:
        Führt die vollständige Initialisierung und Befüllung der Datenbank durch. 
        Zuerst wird die Struktur erstellt (`init_db`), dann werden alle vordefinierten 
        CSV-Dateien aus dem 'data/' Verzeichnis in die entsprechenden Tabellen geladen (`load_csv`).

    Parameter:
        - Keine

    Return:
        - Keine (Funktion führt DB-Seeding durch)

    Tests:
        1. Vollständigkeit: Alle sechs Kerntabellen (`users`, `supermarkets`, `products`, etc.) enthalten nach Aufruf Daten.
        2. Integrität: Foreign-Key-Beziehungen zwischen den geladenen Daten sind gültig.
        
        """
    init_db()
    load_csv("users", "data/users.csv")
    load_csv("supermarkets", "data/supermarkets.csv")
    load_csv("products", "data/products.csv")
    load_csv("supermarket_products", "data/supermarket_products.csv")
    load_csv("orders", "data/orders.csv")
    load_csv("order_items", "data/order_items.csv")


if __name__ == "__main__":
    seed_data()
    print("DB initialisiert und mit Beispieldaten befüllt.")
