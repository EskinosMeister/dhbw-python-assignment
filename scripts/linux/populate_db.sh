## Label: Datenbank-Befüllungs-Startskript
# Ersteller: Philip Welter, Jakub Nossowski, Marie Wütz
# Datum: 2025-11-27
# Version: 1.0.0
# Lizenz: Proprietär (für Studienzwecke)
#
# Kurzbeschreibung des Moduls:
#   Dieses Skript dient als einfacher Starter für den Datenbank-Befüllungsprozess. 
#   Es führt das Python-Skript `populate_db.py` aus, welches die eigentliche Logik zur 
#   interaktiven Auswahl der Befüllungsmethode (CSV oder Beispiele) enthält.

#!/bin/bash

# --- Start des Python-Befüllungsskripts ---
# Führt das Python-Skript aus, das die interaktive Logik zur Auswahl der Datenquelle enthält.

python ../../database/populate_db.py
