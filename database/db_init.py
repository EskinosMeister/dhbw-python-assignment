# db_init.py
"""
Label: Datenbankstruktur-Initialisierung
Ersteller: Philip Welter, Jakub Nossowski, Marie Wütz
Datum: 2025-11-27
Version: 1.0.0
Lizenz: Proprietär (für Studienzwecke)

Kurzbeschreibung des Moduls:
    Dieses Skript dient zur einmaligen Erstellung der Datenbanktabellen. Es liest das SQL-Schema 
    aus der Datei 'schema.sql' und führt es über eine Datenbankverbindung aus. Es wird für die 
    Basisstruktur der Anwendung benötigt.

"""
from my_helpers import get_connection
from pathlib import Path

# Absolute path to schema.sql
SCHEMA_FILE = Path(__file__).parent / "schema.sql"

def init_tables():
    """
    Label: Tabellen initialisieren
    Kurzbeschreibung:
        Stellt eine Verbindung zur Datenbank her, liest das gesamte SQL-Schema aus der 
        Datei 'schema.sql' und führt alle enthaltenen SQL-Anweisungen aus, um die Tabellen zu erstellen.

    Parameter:
        - Keine (nimmt die Datenbankverbindung über get_connection() und die Schema-Datei automatisch)

    Return:
        - Keine (Funktion führt Operationen auf der DB durch)

    Tests:
        1. Erfolg: Die Datenbankverbindung wird erfolgreich geöffnet und das SQL-Skript wird ohne Fehler ausgeführt.
        2. Dateiprüfung: Die Datei 'schema.sql' existiert im erwarteten Pfad und kann gelesen werden.
    """
    conn = get_connection()
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_tables()
    print("DB initialisiert")  