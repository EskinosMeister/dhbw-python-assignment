:: Label: Setup- und Initialisierungs-Skript (Windows Batch)
:: Ersteller: Philip Welter, Jakub Nossowski, Marie Wütz
:: Datum: 2025-11-27
:: Version: 1.0.0
:: Lizenz: Proprietär (für Studienzwecke)
::
:: Kurzbeschreibung des Moduls:
::   Dieses Skript automatisiert die Vorbereitung des Projekts für Windows, indem es Abhängigkeiten 
::   installiert und die Datenbankstruktur zurücksetzt sowie neu erstellt. Es verwendet 
::   dynamische Pfade für die Ausführung der Python-Skripte.

REM --- 1. Pfad-Definition ---
:: Deaktiviert die Anzeige der Befehle im Fenster
@ECHO OFF
:: Speichert das Verzeichnis, in dem dieses Skript liegt, in der Variable SCRIPT_DIR
SET SCRIPT_DIR=%~dp0

REM --- 2. Python-Abhängigkeiten ---
:: Installiert alle benötigten Python-Pakete aus der requirements.txt (Pfad: zwei Ebenen zurück)
pip install -r "%SCRIPT_DIR%..\..\requirements.txt"

REM --- 3. Datenbank-Zurücksetzung und Schema-Erstellung ---
:: Setzt die Datenbank zurück (löscht Datei und entfernt Tabellen)
python "%SCRIPT_DIR%..\..\database\reset_db.py"
:: Erstellt die Tabellenstruktur (Schema) neu
python "%SCRIPT_DIR%..\..\database\db_init.py"

