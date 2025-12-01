# Label: Datenbank-Vorbereitungs-Skript (Minimal)
# Ersteller: Philip Welter, Jakub Nossowski, Marie Wütz
# Datum: 2025-11-27
# Version: 1.0.0
# Lizenz: Proprietär (für Studienzwecke)
#
# Kurzbeschreibung des Moduls:
#   Dieses Skript automatisiert die Vorbereitung des Projekts, indem es die notwendigen 
#   Python-Abhängigkeiten installiert, die Datenbank zurücksetzt und die Tabellenstruktur neu erstellt.



# --- 1. Python-Abhängigkeiten ---
# Installiert alle benötigten Python-Pakete aus der requirements.txt Datei.
#!/bin/bash
pip install -r ../../requirements.txt

# --- 2. Datenbank-Zurücksetzung und Schema-Erstellung ---
# Setzt die Datenbank zurück (löscht die Datei und entfernt alle Tabellen über reset_db.py).

python ../../database/reset_db.py

# Erstellt die Tabellenstruktur (Schema) neu gemäß db_init.py.
python ../../database/db_init.py