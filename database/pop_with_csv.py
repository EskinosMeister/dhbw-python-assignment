# pop_with_csv.py

"""
Label: Datenbank-Befüllung mit CSV-Dateien
Ersteller: Philip Welter, Jakub Nossowski, MArie Wütz
Datum: 2025-11-27
Version: 1.0.1
Lizenz: Proprietär (für Studienzwecke)

Kurzbeschreibung des Moduls:
    Dieses Skript dient zum initialen Befüllen der SQLite-Datenbank (`grocery.db`) mit 
    Beispieldaten aus verschiedenen CSV-Dateien. Es nutzt die Funktion `load_csv` 
    zum Einlesen und Einfügen der Daten in die entsprechenden Tabellen.
"""
import csv
from pathlib import Path

from db_init import get_connection

def load_csv(table_name, csv_path):
    """
    Label: Lädt Daten aus CSV in Tabelle
    Kurzbeschreibung:
        Öffnet eine CSV-Datei, liest die Daten ein und fügt sie in die angegebene Zieltabelle 
        in der Datenbank ein. Die Spaltennamen der CSV müssen mit denen der Tabelle übereinstimmen.

    Parameter:
        table_name (str): Der Name der Zieltabelle in der Datenbank.
        csv_path (str | Path): Der Pfad zur Quell-CSV-Datei.

    Return:
        - Keine (Funktion führt Datenoperationen durch)

    Tests:
        1. Dateneinfügung: Zeilen werden erfolgreich in die angegebene Tabelle eingefügt und committed.
        2. Leere Datei: Eine leere CSV-Datei wird ohne Fehler verarbeitet, und es werden keine Zeilen eingefügt.
        
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

    # creates a cursor automatically under the hood, making get_cursor redundant here
    conn.executemany(
        f"INSERT INTO {table_name} ({col_list}) VALUES ({placeholders})",
        [[row[c] for c in cols] for row in rows],
    )
    conn.commit()
    conn.close()


def seed_data():
    """
    Label: Befüllt Datenbank mit initialen Daten
    Kurzbeschreibung:
        Ruft die `load_csv`-Funktion sequenziell für alle relevanten Tabellen und deren 
        zugehörige CSV-Dateien auf, um die Datenbank mit Beispieldaten zu befüllen.

    Parameter:
        - Keine

    Return:
        - Keine (Funktion führt DB-Seeding durch)

    Tests:
        1. Vollständigkeit: Alle sechs Kerntabellen (`users`, `supermarkets`, `products`, etc.) werden mit Daten versorgt.
        2. Abhängigkeiten: Die Tabellen werden in der korrekten Reihenfolge geladen, um Foreign-Key-Abhängigkeiten zu erfüllen.
        
    """
    load_csv("users", "../data/users.csv")
    load_csv("supermarkets", "../data/supermarkets.csv")
    load_csv("products", "../data/products.csv")
    load_csv("supermarket_products", "../data/supermarket_products.csv")
    load_csv("orders", "../data/orders.csv")
    load_csv("order_items", "../data/order_items.csv")



if __name__ == "__main__":
    seed_data()
    print("DB mit .csv daten befüllt.")
