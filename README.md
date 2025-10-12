## an unapologetically bad readme file
# Was wir haben möchten
- GUI als Hauptoberfläche
  1. Search
  2. Profile (login)
  3. Wishlist
  4. (Warenkorb)
- backend
  1. Datenbank
    - Wir möchten SQLite anwenden.
    - Alle Daten werden auf einer Lokalen, diskbasierten db gespeichert.
    - später wird die Datenbank automatisch bei der Installation der App aufgestellt (alle CREATE TABLE, etc)
  2. Nutzerlogin/unterscheidung
    - muss nochn entschieden werden ob mit passwort oder nicht.
    - wenn mit passwort dann hashing
    - Nutzerauswahl, switchen zwischen Konten
  3. Webcrawler
    - Zugriff auf 3 bekannte Produktplatformen/Vergleichsportale (Check24, Idealo, Amazon)
    - Ablesen von vollständigen Produktname, Preis, Link zu Produkt von Top 3 Ergebnissen jeweils
  4. (Filter für Wischliste/Warenkorb)

# Anwendungsdurchlauf (playbook)
1. Login/Profilwahl (wie in Netflix)
2. Nutzer nach Profilauswahl Search (wie google).
  1. Nutzer gibt ein Produktname an
  2. System wählt Top 3 Ergebnisse bei jeweiligen Platform
  3. Die Ergebnisse werden unter Searchfeld aufgelistet
  4. Nutzer wählt ein der Produkte
3. Wunschliste
  1. Das gewählte Produkt wird zu der Wunschliste (userspezifisch) hinzugefügt
  2. Der Nutzer sieht hier alle von ihm bereits ausgewählte Produkte
     - (Bild)
     - bestellt?
     - Produktname
     - Preis
     - Link (/Button der zu Produktseite schickt)
     - Löschen?
  4. Der Nutzer kann jedes Produkt löschen, oder als bestellt markieren / archivieren.
  5. (Der Nutzer kann nach Produktname oder Preis filtern)
  6. (sperater Warenkorb für schon bestellte/archivierte Produkte)
4. Der User loggt aus
