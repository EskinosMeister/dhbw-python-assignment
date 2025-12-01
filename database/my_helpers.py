"""
Label: Allgemeine Hilfsfunktionen für die Datenbank
Ersteller: Philip Welter, Jakub Nossowski, Marie Wütz
Datum: 2025-11-27
Version: 1.0.0
Lizenz: Proprietär (für Studienzwecke)

Kurzbeschreibung des Moduls:
    Dieses Modul enthält allgemeine, wiederverwendbare Hilfsfunktionen, insbesondere die zentrale 
    Funktion zur Herstellung einer konfigurierten Verbindung zur SQLite-Datenbank (`grocery.db`).
"""

import sqlite3
from pathlib import Path

# BASE_DIR is in the project's root directory
BASE_DIR = Path(__file__).parent.parent.resolve()
DB_PATH = BASE_DIR / "grocery.db"


def get_connection():
    """
    Label: Datenbank-Verbindung herstellen
    Kurzbeschreibung:
        Erstellt und konfiguriert eine Verbindung zur SQLite-Datenbank, deren Pfad dynamisch 
        über BASE_DIR bestimmt wird. Die Datenbank wird erstellt, falls sie noch nicht existiert.

    Parameter:
        - Keine

    Return:
        sqlite3.Connection: Die konfigurierte Datenbank-Verbindung.

    Tests:
        1. Verbindungskonfiguration: Die Row-Factory ist auf sqlite3.Row gesetzt (Zugriff über Spaltenname).
        2. Integrität: Foreign Keys (Fremdschlüssel) sind in der Datenbankverbindung aktiviert.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn