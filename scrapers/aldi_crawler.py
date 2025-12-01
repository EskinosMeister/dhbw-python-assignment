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


def _find_unitprice(el):
    """Findet Grundpreis im Element"""
    return (
        el.find(string=re.compile(r"€/|je\s", re.I))
        or el.find("span", class_=re.compile(r"(baseprice|reference|price-per)", re.I))
        or el.find("div", class_=re.compile(r"(baseprice|reference|price-per)", re.I))
    )


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


def scrape_aldi_sued_top(product_name: str, top_n: int = 3,
                         insecure: bool = False, ca_file: Optional[str] = None) -> list[dict]:
    """
    Crawlt Aldi Süd nach Produkten.
    
    Args:
        product_name: Suchbegriff
        top_n: Anzahl der Treffer
        insecure: SSL-Verifizierung deaktivieren
        ca_file: Pfad zu CA-Zertifikat
        
    Returns:
        Liste mit Produkten (Titel, Preis, Grundpreis, URL, Timestamp, Query, Source)
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