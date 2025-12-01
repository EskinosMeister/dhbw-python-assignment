:: Label: Datenbank-Befüllungs-Startskript (Windows)
:: Ersteller: Philip Welter, Jakub Nossowski, Marie Wütz
:: Datum: 2025-11-27
:: Version: 1.0.0
:: Lizenz: Proprietär (für Studienzwecke)
::
:: Kurzbeschreibung des Moduls:
::   Dieses Skript dient als Startpunkt für die interaktive Datenbankbefüllung unter Windows. 
::   Es ruft das zentrale Python-Skript `populate_db.py` über einen absoluten Pfad auf.

REM --- 1. Pfad-Definition ---
:: Deaktiviert die Anzeige der Befehle im Fenster
@ECHO OFF
:: Speichert das Verzeichnis, in dem dieses Skript liegt, in der Variable SCRIPT_DIR
SET SCRIPT_DIR=%~dp0

REM --- 2. Ausführung ---
:: Führt das Python-Skript aus, das die eigentliche Logik zur Auswahl der Datenquelle (CSV/Beispiel) enthält.
:: Der Pfad wird dynamisch aus SCRIPT_DIR und relativen Pfaden konstruiert.
python "%SCRIPT_DIR%..\..\database\populate_db.py"

