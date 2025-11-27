# reset_db.py
# this only works, if all resources are free. If the server uses grocery.db, the reset won't work
"""
Label: Datenbank-Zurücksetzungs-Skript
Ersteller: Philip Welter, Jakub Nossowski, Marie Wütz
Datum: 2025-11-27
Version: 1.0.1
Lizenz: Proprietär (für Studienzwecke)

Kurzbeschreibung des Moduls:
    Dieses Skript dient zum vollständigen Zurücksetzen der SQLite-Datenbank. 
    Es löscht die physische Datenbankdatei (`grocery.db`) und führt zusätzlich 
    SQL-Anweisungen aus, um alle Tabellen explizit zu entfernen (DROP). 
    Hinweis: Funktioniert nur, wenn keine andere Anwendung (z.B. der Flask-Server) 
    die Datenbankdatei aktuell geöffnet hat.

"""
from my_helpers import get_connection, DB_PATH

destroy_schema = """
-- Aktiviert Foreign Key Support
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS saved_products;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS supermarket_products;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS supermarkets;
DROP TABLE IF EXISTS users;
"""


def main():
    """
    Label: Datenbank zurücksetzen
    Kurzbeschreibung:
        Führt den Reset-Prozess durch. Prüft, ob die Datenbankdatei existiert, und löscht sie. 
        Danach wird eine Verbindung hergestellt und das 'destroy_schema'-SQL ausgeführt, um 
        auch etwaige Überreste von Tabellen zu entfernen.

    Parameter:
        - Keine

    Return:
        - Keine (Funktion führt Dateisystem- und DB-Operationen durch und gibt Statusmeldungen aus)

    Tests:
        1. Dateilöschung: Die Datei 'grocery.db' wird erfolgreich aus dem Dateisystem entfernt, wenn sie existiert.
        2. Schema-Zerstörung: Alle Kerntabellen (`users`, `orders` etc.) werden durch das SQL-Skript gelöscht.
    """
    # 1. Datenbankdatei physisch löschen
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"Bestehende {DB_PATH} gelöscht.")
    # 2. Verbindung herstellen (erstellt neue, leere DB) und Schema löschen
    # (Diese Schritte sind redundant nach Dateilöschung, dienen aber der Robustheit, 
    # falls die DB-Datei nicht gelöscht werden konnte)
    conn = get_connection()
    conn.executescript(destroy_schema)
    conn.commit()
    print("Schema zerstört.")
    conn.close()


if __name__ == "__main__":
    main()
