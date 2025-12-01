:: Label: Startskript der Flask-Anwendung (Windows)
:: Ersteller: Philip Welter, Jakub Nossowski, Marie Wütz
:: Datum: 2025-11-27
:: Version: 1.0.0
:: Lizenz: Proprietär (für Studienzwecke)
::
:: Kurzbeschreibung des Moduls:
::   Dieses Skript startet die zentrale Flask-Anwendung (`app.py`) unter Windows. 
::   Es verwendet den absoluten Pfad, um sicherzustellen, dass die Datei von überall aus korrekt gestartet wird.

REM --- 1. Pfad-Definition ---
:: Deaktiviert die Anzeige der Befehle im Fenster
@ECHO OFF
:: Speichert das Verzeichnis, in dem dieses Skript liegt, in der Variable SCRIPT_DIR
SET SCRIPT_DIR=%~dp0

REM --- 2. Anwendungsstart ---
:: Führt die zentrale Flask-Anwendungsdatei 'app.py' mit dem Python-Interpreter aus.
:: Der Pfad wird dynamisch aus SCRIPT_DIR und relativen Pfaden konstruiert.
python "%SCRIPT_DIR%..\..\app.py"
