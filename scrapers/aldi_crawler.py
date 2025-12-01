# --- aldi_crawler.py ---

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
    Erzeugt und konfiguriert eine `requests.Session` für wiederverwendbare HTTP-Requests.

    Die Session enthält:
    - Standard-HTTP-Header, die typische Browseranfragen simulieren
    - Automatisches Wiederholen (Retry) bei bestimmten HTTP-Fehlern
    - Optionales SSL-Verhalten

    Args:
        insecure (bool, optional): 
            Wenn True, wird die SSL-Zertifikatsprüfung deaktiviert. 
            Standard ist False.
        ca_file (str, optional): 
            Pfad zu einem CA-Bundle für HTTPS-Verbindungen. 
            Fällt auf Umgebungsvariablen `REQUESTS_CA_BUNDLE` oder `ALDI_CA_FILE` zurück, falls None.

    Returns:
        requests.Session: Eine konfigurierte Session-Instanz, die für HTTP/HTTPS-Requests verwendet werden kann.

    Beispiele:
        >>> session = make_session()
        >>> response = session.get("https://example.com")
        >>> print(response.status_code)

        >>> session = make_session(insecure=True)
        >>> response = session.get("https://self-signed.example.com")
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
    """Extrahiert Preis aus Text (unterstützt deutsches Format)"""
    cleaned = text.replace(".", "").replace(",", ".")
    m = re.search(r"(\d+(?:\.\d+)?)", cleaned)
    return float(m.group(1)) if m else None


def _find_title(el):
    """Findet Produkt-Titel im Element"""
    return (
        el.find("h2", class_="at-all-productName-lbl")
        or el.find("h2", attrs={"data-qa": "m-article-tile__title"})
        or el.find(["h1", "h2", "h3"])
    )


def _find_price(el):
    """Findet Preis im Element"""
    cand = (
        el.find("span", class_="at-product-price_lbl")
        or el.find("span", attrs={"data-qa": "m-price__price-part"})
        or el.find("div", attrs={"data-qa": "m-price__price-part"})
        or el.find(string=re.compile(r"€"))
    )
    return cand


def _find_link(el, base_url):
    """Findet Produkt-Link im Element"""
    a = el.select_one('a[href*="/p/"]') or el.find("a", href=True)
    return urljoin(base_url, a["href"]) if a and a.has_attr("href") else None


def _candidate_cards(soup: BeautifulSoup):
    """Findet alle Produkt-Karten auf der Seite"""
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

def split_after_last_caps(s: str):
    words = s.split()
    last_caps_index = -1
    
    # Find the index of the last fully capitalized word
    for i, word in enumerate(words):
        if word.isupper():
            last_caps_index = i
    
    if last_caps_index == -1:
        # No capital words, return original string and empty string
        return s, ""
    
    # Rebuild the two parts of the string
    in_caps = " ".join(words[:last_caps_index + 1])
    normal = " ".join(words[last_caps_index + 1:])
    return in_caps, normal


def scrape_aldi_sued_top(query: str, top_n: int = 3,
                         insecure: bool = False, ca_file: Optional[str] = None) -> list[dict]:
    """
    Crawlt Aldi Süd nach Produkten.
    
    Args:
        query: Suchbegriff
        top_n: Anzahl der Treffer
        insecure: SSL-Verifizierung deaktivieren
        ca_file: Pfad zu CA-Zertifikat
        
    Returns:
        Liste von Produkt-Dictionaries (Supermarketname, Produktname, Preis, URL, is_live Wahrheitswert und Timestamp)
    """
    base_url = "https://www.aldi-sued.de/de/suchergebnis.html"
    session = make_session(insecure=insecure, ca_file=ca_file)

    url = f"{base_url}?{urlencode({'search': query})}"
    
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
        brand, product_name = split_after_last_caps(title)
        price_raw = price_el.get_text(" ", strip=True) if hasattr(price_el, "get_text") else str(price_el)
        price = _extract_price_float(price_raw)
        
        if price is None:
            continue

        product_url = _find_link(card, base_url) or url
        

        results.append(
            {
                "supermarket_name": "Aldi Süd",
                "name": product_name,
                "price": price,
                "brand": brand,
                "product_url": product_url,
                "is_live": True,
                "timestamp": datetime.now().isoformat(timespec="seconds"),
            }
        )
        
        if len(results) >= top_n:
            break

    return results