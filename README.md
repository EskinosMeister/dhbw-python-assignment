## an unapoletically bad readme file
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

# Anwendungsdurchlauf (playbook)
1. Login/Profilwahl (wie in Netflix)
2. Nutzer nach Profilauswahl Search (wie google).
   2.1. Nutzer gibt ein Produktname an
   2.2. System wählt Top 3 Ergebnisse bei jeweiligen Platform
   2.3. Die Ergebnisse werden unter Searchfeld aufgelistet
   2.4. Produktauswahl
