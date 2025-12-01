"""
Label: Interaktives Datenbank-Befüllungsskript
Ersteller: Philip Welter, Jakub Nossowski, Marie Wütz
Datum: 2025-11-27
Version: 1.0.0
Lizenz: Proprietär (für Studienzwecke)

Kurzbeschreibung des Moduls:
    Dieses Skript dient als zentrale Schnittstelle für die Befüllung der Datenbank. 
    Es bietet dem User eine interaktive Auswahl, ob die Daten aus statischen CSV-Dateien 
    oder aus fest codierten Beispieldaten geladen werden sollen. Die eigentliche Logik wird 
    über subprocess-Aufrufe an die entsprechenden Skripte delegiert.
"""
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()


def main():
    """
    Label: Startfunktion zur Datenbefüllung
    Kurzbeschreibung:
        Zeigt dem User die verfügbaren Optionen zur Datenbankbefüllung an (CSV oder Beispiele) 
        und führt das gewählte Skript (`pop_with_csv.py` oder `pop_with_example.py`) 
        mittels subprocess.run() im aktuellen Verzeichnis aus.

    Parameter:
        - Keine

    Return:
        - Keine (Funktion führt Unterprozesse aus und beendet sich)

    Tests:
        1. CSV-Auswahl (Eingabe '1'): Das Skript 'pop_with_csv.py' wird erfolgreich gestartet und ausgeführt.
        2. Beispiel-Auswahl (Eingabe '2'): Das Skript 'pop_with_example.py' wird erfolgreich gestartet und ausgeführt.
        3. Fehlerhafte Eingabe: Bei einer ungültigen Eingabe wird eine Fehlermeldung ausgegeben und das Programm beendet.
        
    """
    
    print("How do you want to populate the database?")
    print("1) Using CSV files")
    print("2) Using example data")

    choice = input("Enter 1 or 2: ").strip()

    if choice == "1":
        print("Running pop_with_csv.py...\n")
        subprocess.run(["python", "pop_with_csv.py"], check=True, cwd=BASE_DIR)

    elif choice == "2":
        print("Running pop_with_example.py...\n")
        subprocess.run(["python", "pop_with_example.py"], check=True, cwd=BASE_DIR)

    else:
        print("Invalid option. Exiting.")


if __name__ == "__main__":
    main()
