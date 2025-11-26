# --- aldi_crawler.py ---
"""
Label: Aldi Süd Web-Crawler
Ersteller: [Ihr Name/Matrikelnummer]
Datum: 2025-11-26
Version: 1.0.0
Lizenz: Proprietär (für Studienzwecke)

Kurzbeschreibung des Moduls:
    Stellt Funktionen zum Crawling der Aldi Süd Suchergebnisseite bereit. 
    Ziel ist die Extraktion von Produktnamen, Preisen, Grundpreisen und URLs für Preisvergleiche.
    Das Modul verwendet `requests` und `BeautifulSoup` und implementiert robuste 
    Fehlerbehandlung und Wiederholungsversuche (Retries).

"""
import os
from typing import Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import re
from datetime import datetime
from urllib.parse import urlencode, urljoin

# Versuche truststore zu laden (optional)
try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass


def make_session(insecure: bool = False, ca_file: Optional[str] = None) -> requests.Session:
    """
    Label: Erstellt eine konfigurierte Requests-Session
    Kurzbeschreibung:
        Initialisiert eine requests.Session mit Standard-Headern (User-Agent) und einer 
        HTTPAdapter-Konfiguration für automatische Wiederholungsversuche (Retries) 
        bei temporären Serverfehlern (429, 5xx). Erlaubt optional die Deaktivierung der SSL-Verifizierung.

    Parameter:
        insecure (bool, optional): Deaktiviert SSL-Verifizierung, wenn True. Default ist False.
        ca_file (str, optional): Pfad zu einer benutzerdefinierten CA-Zertifikatsdatei.

    Return:
        requests.Session: Die konfigurierte Session für HTTP-Anfragen.

    Tests:
        1. Erfolgreicher Aufruf: Eine gültige requests.Session mit 3 Retries und User-Agent-Header wird zurückgegeben.
        2. Insecure-Flag: Wenn True, ist s.verify auf False gesetzt. 
    
    """
    s = requests.Session()
    s.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
    })
    retries = Retry(
        total=3, 
        backoff_factor=0.6, 
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.mount("http://", HTTPAdapter(max_retries=retries))

    if insecure:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        s.verify = False
    else:
        # ENV-Fallbacks erlauben start ohne UI
        ca_env = ca_file or os.getenv("REQUESTS_CA_BUNDLE") or os.getenv("ALDI_CA_FILE")
        if ca_env:
            s.verify = ca_env
    return s


def _extract_price_float(text: str):
    """
    Label: Extrahiert den Preis als Fließkommazahl
    Kurzbeschreibung:
        Extrahiert eine Dezimalzahl (Preis) aus einem Text-String. 
        Unterstützt das deutsche Format (Komma als Dezimaltrennzeichen).

    Parameter:
        text (str): Der Roh-String, der den Preis enthält (z.B. "1,99 €").

    Return:
        float | None: Der extrahierte Preis als Fließkommazahl oder None, falls keine Zahl gefunden wird.

    Tests:
        1. Erfolgreiche Extraktion (Deutsch): Eingabe "1,99 €" liefert float 1.99.
        2. Fehlerfall: Eingabe "Kein Preis" liefert None.
    
    """
    cleaned = text.replace(".", "").replace(",", ".")
    m = re.search(r"(\d+(?:\.\d+)?)", cleaned)
    return float(m.group(1)) if m else None


def _find_title(el):
    """
    Label: Findet den Produkt-Titel
    Kurzbeschreibung:
        Sucht im übergebenen BeautifulSoup-Element nach dem Produkt-Titel anhand verschiedener 
        bekannter CSS-Klassen oder HTML-Tags, die Aldi Süd verwendet.

    Parameter:
        el (BeautifulSoup Tag): Das Elternelement (Produktkarte), in dem gesucht wird.

    Return:
        BeautifulSoup Tag | None: Das gefundene Tag-Element, das den Titel enthält.

    Tests:
        1. Treffer: Findet den Titel in einer typischen Produktkarte mit der Klasse `at-all-productName-lbl`.
        2. Fallback: Findet den Titel in generischen Tags wie h1, h2 oder h3.
    """
    return (
        el.find("h2", class_="at-all-productName-lbl")
        or el.find("h2", attrs={"data-qa": "m-article-tile__title"})
        or el.find(["h1", "h2", "h3"])
    )


def _find_price(el):
    """
    Label: Findet das Preis-Element
    Kurzbeschreibung:
        Sucht im übergebenen BeautifulSoup-Element nach dem Element, das den Hauptpreis enthält, 
        basierend auf verschiedenen bekannten Aldi Süd CSS-Klassen oder dem Vorkommen des Währungszeichens (€).

    Parameter:
        el (BeautifulSoup Tag): Das Elternelement (Produktkarte), in dem gesucht wird.

    Return:
        BeautifulSoup Tag | None: Das gefundene Tag-Element, das den Preis enthält.

    Tests:
        1. Treffer: Findet den Preis in der Klasse `at-product-price_lbl`.
        2. Fallback: Findet einen Preis-String, der das "€"-Zeichen enthält.
    """
    cand = (
        el.find("span", class_="at-product-price_lbl")
        or el.find("span", attrs={"data-qa": "m-price__price-part"})
        or el.find("div", attrs={"data-qa": "m-price__price-part"})
        or el.find(string=re.compile(r"€"))
    )
    return cand


def _find_unitprice(el):
    """
    Label: Findet das Grundpreis-Element
    Kurzbeschreibung:
        Sucht im übergebenen BeautifulSoup-Element nach dem Grundpreis pro Einheit, 
        basierend auf Mustern wie "€/" oder spezifischen Klassen wie "baseprice".

    Parameter:
        el (BeautifulSoup Tag): Das Elternelement (Produktkarte), in dem gesucht wird.

    Return:
        BeautifulSoup Tag | None: Das gefundene Tag-Element, das den Grundpreis enthält.

    Tests:
        1. Treffer: Findet Grundpreis durch das Muster "€/" oder "je " (unabhängig von Groß-/Kleinschreibung).
        2. Klassensuche: Findet Grundpreis in Elementen mit der Klasse `baseprice`.
    """
    return (
        el.find(string=re.compile(r"€/|je\s", re.I))
        or el.find("span", class_=re.compile(r"(baseprice|reference|price-per)", re.I))
        or el.find("div", class_=re.compile(r"(baseprice|reference|price-per)", re.I))
    )


def _find_link(el, base_url):
    """Label: Findet den Produkt-Link
    Kurzbeschreibung:
        Sucht im übergebenen BeautifulSoup-Element nach dem Link zum Produktdetailseite. 
        Die gefundene URL wird mit der Basis-URL (`base_url`) zu einer vollständigen URL kombiniert.

    Parameter:
        el (BeautifulSoup Tag): Das Elternelement (Produktkarte), in dem gesucht wird.
        base_url (str): Die Basis-URL für die URL-Kombination.

    Return:
        str | None: Die vollständige Produkt-URL oder None, wenn kein Link gefunden wird.

    Tests:
        1. Treffer: Findet Links, die den Pfad "/p/" enthalten.
        2. Kombinierung: Liefert eine vollständige, absolute URL zurück.
    """
    a = el.select_one('a[href*="/p/"]') or el.find("a", href=True)
    return urljoin(base_url, a["href"]) if a and a.has_attr("href") else None


def _candidate_cards(soup: BeautifulSoup):
    """
    Label: Identifiziert Produkt-Karten
    Kurzbeschreibung:
        Findet alle HTML-Elemente auf der Seite, die als Produkt-Karte (Container für Titel, Preis, etc.) 
        in Frage kommen, indem verschiedene spezifische CSS-Selektoren oder Data-Attribute verwendet werden.

    Parameter:
        soup (BeautifulSoup): Das geparste HTML-Dokument.

    Return:
        list[BeautifulSoup Tag]: Eine Liste von potenziellen Produktkarten-Elementen.

    Tests:
        1. Treffer: Findet Elemente mit Data-Attributen, die 'article' enthalten.
        2. Fallback: Bei fehlenden Cards werden die Elternelemente der Titel-Elemente als Card verwendet.
    """
    cards = soup.select(
        "article[data-qa*='article'],"
        "div[data-qa*='article'],"
        "li[data-qa*='article'],"
        "div.m-article-tile, li.m-article-tile, div.at-product-tile, li.at-product-tile"
    )
    if cards:
        return cards
    titles = soup.select("h2.at-all-productName-lbl, h2[data-qa='m-article-tile__title']")
    return [t.parent if t and t.parent else t for t in titles]


def scrape_aldi_sued_top(product_name: str, top_n: int = 3,
                         insecure: bool = False, ca_file: Optional[str] = None) -> list[dict]:
    """
    Label: Haupt-Crawling-Funktion für Aldi Süd
    Kurzbeschreibung:
        Führt eine Produktsuche auf der Aldi Süd Webseite durch, parst die Ergebnisseite und 
        extrahiert die Top-N Produkte mit ihren Preisdetails und URLs.

    Parameter:
        product_name (str): Der Suchbegriff (z.B. "Milch").
        top_n (int, optional): Die maximale Anzahl an Treffern, die zurückgegeben werden soll. Default ist 3.
        insecure (bool, optional): Deaktiviert SSL-Verifizierung. Default ist False.
        ca_file (str, optional): Pfad zu einer benutzerdefinierten CA-Zertifikatsdatei.
        
    Return:
        list[dict]: Eine Liste von Dictionaries, die jeweils die Felder 
                    'source', 'query', 'title', 'price', 'unit_price', 'url' und 'timestamp' enthalten.

    Tests:
        1. Erfolg: Bei gültiger Suche werden bis zu 'top_n' Ergebnisse mit Titel, Preis (float) und URL zurückgegeben.
        2. Fehler/Leere Suche: Bei einem RequestException oder wenn keine Karten gefunden werden, wird eine leere Liste zurückgegeben.
        3. Preisextraktion: Es werden nur Ergebnisse zurückgegeben, bei denen der Preis erfolgreich in eine Fließkommazahl konvertiert werden konnte.
    """
    base_url = "https://www.aldi-sued.de/de/suchergebnis.html"
    session = make_session(insecure=insecure, ca_file=ca_file)

    url = f"{base_url}?{urlencode({'search': product_name})}"
    
    try:
        resp = session.get(url, timeout=12)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Fehler beim Abrufen: {e}")
        return []

    soup = BeautifulSoup(resp.content, "html.parser")
    cards = _candidate_cards(soup)

    results = []
    for card in cards:
        title_el = _find_title(card) or _find_title(soup)
        price_el = _find_price(card) or _find_price(soup)
        
        if not (title_el and price_el):
            continue

        title = title_el.get_text(" ", strip=True)
        price_raw = price_el.get_text(" ", strip=True) if hasattr(price_el, "get_text") else str(price_el)
        price = _extract_price_float(price_raw)
        
        if price is None:
            continue

        unit_el = _find_unitprice(card)
        unit_price = unit_el.get_text(" ", strip=True) if hasattr(unit_el, "get_text") else (unit_el.strip() if unit_el else None)
        product_url = _find_link(card, base_url) or url

        results.append({
            "source": "Aldi Süd",
            "query": product_name,
            "title": title,
            "price": price,
            "unit_price": unit_price,
            "url": product_url,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        })
        
        if len(results) >= top_n:
            break

    return results