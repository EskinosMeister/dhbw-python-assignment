## app.py läuft mit speichern und luftballons 

## app.py mit neuem layout und tabs

import sqlite3
import hashlib
import secrets
import csv
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

import streamlit as st
import aldi_crawler
from aldi_crawler import scrape_aldi_sued_top

DB_PATH = "prices.db"
METRO_CSV_PATH = Path("metro_products.csv")


# =======================
# DB (lokal)
# =======================
def db_connect():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def db_init():
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            pw_hash TEXT,
            salt TEXT,
            created_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS saved_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            source TEXT,
            query TEXT,
            title TEXT,
            price REAL,
            unit_price TEXT,
            url TEXT,
            ts_found TEXT,
            ts_saved TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()


def hash_password(password: str, salt: Optional[bytes] = None):
    if salt is None:
        salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return dk.hex(), salt.hex()


def verify_password(password: str, pw_hash_hex: str, salt_hex: str) -> bool:
    salt = bytes.fromhex(salt_hex)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return dk.hex() == pw_hash_hex


def create_user(username: str, password: str) -> tuple[bool, str]:
    try:
        conn = db_connect()
        cur = conn.cursor()
        pw_hash, salt = hash_password(password)
        cur.execute(
            "INSERT INTO users(username, pw_hash, salt, created_at) VALUES (?,?,?,?)",
            (username, pw_hash, salt, datetime.now().isoformat(timespec="seconds"))
        )
        conn.commit()
        return True, "Registrierung erfolgreich."
    except sqlite3.IntegrityError:
        return False, "Nutzername existiert bereits."
    finally:
        conn.close()


def authenticate(username: str, password: str) -> Optional[dict]:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("SELECT id, pw_hash, salt FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    user_id, pw_hash, salt = row
    if verify_password(password, pw_hash, salt):
        return {"id": user_id, "username": username}
    return None


def save_product(user_id: int, item: Dict):
    """Speichert EIN einzelnes Produkt"""
    conn = db_connect()
    cur = conn.cursor()
    now = datetime.now().isoformat(timespec="seconds")
    cur.execute("""
        INSERT INTO saved_products(user_id, source, query, title, price, unit_price, url, ts_found, ts_saved)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (
        user_id,
        item.get("source"),
        item.get("query"),
        item.get("title"),
        float(item.get("price")) if item.get("price") is not None else None,
        item.get("unit_price"),
        item.get("url"),
        item.get("timestamp") or now,
        now
    ))
    conn.commit()
    conn.close()


def get_saved_products(user_id: int) -> List[Dict]:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, source, query, title, price, unit_price, url, ts_found, ts_saved
        FROM saved_products WHERE user_id=?
        ORDER BY ts_saved DESC
    """, (user_id,))
    rows = cur.fetchall()
    conn.close()
    keys = ["id", "source", "query", "title", "price", "unit_price", "url", "ts_found", "ts_saved"]
    return [dict(zip(keys, r)) for r in rows]


def delete_product(user_id: int, product_id: int):
    """Löscht EIN einzelnes Produkt"""
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM saved_products WHERE user_id=? AND id=?", (user_id, product_id))
    conn.commit()
    conn.close()


# =======================
# METRO als CSV-Quelle
# =======================
def _norm_price(v):
    if v is None or v == "":
        return None
    s = str(v).replace(".", "").replace(",", ".")
    m = re.search(r"(\d+(?:\.\d+)?)", s)
    return float(m.group(1)) if m else None


@st.cache_data(show_spinner=False)
def _load_metro_csv_file(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


@st.cache_data(show_spinner=False)
def _load_metro_csv_bytes(b: bytes) -> list[dict]:
    text = b.decode("utf-8")
    return list(csv.DictReader(text.splitlines()))


def scrape_metro_top_from_csv(product_name: str, top_n: int = 3) -> list[dict]:
    """CSV-Quelle: filtert auf query==product_name (case-insensitive) oder Titel enthält Suchwort."""
    rows = st.session_state.get("metro_csv_rows")
    if rows is None:
        rows = _load_metro_csv_file(METRO_CSV_PATH)
        st.session_state["metro_csv_rows"] = rows

    q = product_name.casefold().strip()

    def _match(r: dict) -> bool:
        rq = (r.get("query") or "").casefold().strip()
        title = (r.get("title") or "").casefold()
        return (rq == q) or (q in title)

    hits = []
    for r in rows:
        if _match(r):
            hits.append({
                "source": r.get("source") or "METRO",
                "query": product_name,
                "title": r.get("title") or "",
                "price": _norm_price(r.get("price")),
                "unit_price": r.get("unit_price"),
                "url": r.get("url"),
                "timestamp": r.get("timestamp") or datetime.now().isoformat(timespec="seconds"),
            })
            if len(hits) >= top_n:
                break
    return hits


# =======================
# UI
# =======================
def show_login_register():
    st.header("Login / Register")
    tab_login, tab_register = st.tabs(["Login", "Registrieren"])

    with tab_login:
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Benutzername")
            password = st.text_input("Passwort", type="password")
            submitted = st.form_submit_button("Anmelden")
            if submitted:
                user = authenticate(username, password)
                if user:
                    st.session_state["user"] = user
                    st.success(f"Willkommen, {user['username']}!")
                    st.rerun()
                else:
                    st.error("Login fehlgeschlagen.")

    with tab_register:
        with st.form("register_form", clear_on_submit=True):
            username = st.text_input("Benutzername (neu)")
            password = st.text_input("Passwort", type="password")
            password2 = st.text_input("Passwort wiederholen", type="password")
            submitted = st.form_submit_button("Registrieren")
            if submitted:
                if not username or not password:
                    st.error("Bitte Benutzername und Passwort ausfüllen.")
                elif password != password2:
                    st.error("Passwörter stimmen nicht überein.")
                else:
                    ok, msg = create_user(username, password)
                    st.success(msg) if ok else st.error(msg)


# Ersetze nur die show_search_and_results Funktion in deiner app.py

def show_search_and_results(user_id: int):
    st.header("Suche")
    
    with st.expander("METRO CSV laden (optional)"):
        up = st.file_uploader("metro_products.csv", type="csv", accept_multiple_files=False, key="metro_csv_up")
        if up is not None:
            rows = _load_metro_csv_bytes(up.getvalue())
            st.session_state["metro_csv_rows"] = rows
            st.success(f"CSV geladen: {len(rows)} Zeilen (nur für diese Session).")
        else:
            if "metro_csv_rows" not in st.session_state:
                rows = _load_metro_csv_file(METRO_CSV_PATH)
                if rows:
                    st.session_state["metro_csv_rows"] = rows
                    st.caption(f"Standarddatei erkannt: {METRO_CSV_PATH} ({len(rows)} Zeilen)")

    # SCHRITT 1: SUCHEN
    with st.form("search_form"):
        c1, c2, c3 = st.columns([3, 1, 1.6])
        with c1:
            query = st.text_input("Suchprodukt (z. B. 'Milch')", "")
        with c2:
            top_n = st.number_input("Anzahl Treffer je Quelle", min_value=1, max_value=10, value=3, step=1)
        with c3:
            source_choice = st.selectbox("Quelle", ["Aldi Süd", "METRO (CSV)", "Beide"], index=0)
        submitted = st.form_submit_button("Suchen")

    # SCHRITT 2: ERGEBNISSE ZEIGEN UND SPEICHERN
    if submitted and query.strip():
        with st.spinner("Suche läuft..."):
            items: List[Dict] = []
            if source_choice in ("Aldi Süd", "Beide"):
                try:
                    items.extend(scrape_aldi_sued_top(query.strip(), top_n=int(top_n)))
                except Exception as e:
                    st.error(f"Fehler bei Aldi-Suche: {e}")
            if source_choice in ("METRO (CSV)", "Beide"):
                items.extend(scrape_metro_top_from_csv(query.strip(), top_n=int(top_n)))

        if not items:
            st.warning("Keine Treffer gefunden.")
            return

        st.success(f"✅ {len(items)} Produkt(e) gefunden")
        
        # ALLE Produkte in EINEM Form mit Checkboxen
        with st.form("save_form"):
            st.subheader("Produkte zum Speichern auswählen")
            
            selections = []
            for idx, item in enumerate(items):
                col1, col2 = st.columns([1, 9])
                with col1:
                    # Checkbox für jedes Produkt
                    selected = st.checkbox("", key=f"cb_{idx}", label_visibility="collapsed")
                    selections.append(selected)
                with col2:
                    st.markdown(f"**{item['title']}**")
                    st.caption(f"💰 {item['price']:.2f} € | 📦 {item['source']} | {item.get('unit_price', 'N/A')}")
                st.divider()
            
            # EIN Submit-Button für ALLE ausgewählten Produkte
            save_submitted = st.form_submit_button("✅ Ausgewählte speichern", type="primary")
            
            if save_submitted:
                # Speichere alle ausgewählten Produkte
                to_save = [items[i] for i, sel in enumerate(selections) if sel]
                
                if to_save:
                    try:
                        save_products_for_user(user_id, to_save)
                        st.success(f"🎉 {len(to_save)} Produkt(e) erfolgreich gespeichert!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ Fehler beim Speichern: {e}")
                else:
                    st.warning("⚠️ Keine Produkte ausgewählt!")


def show_saved_products(user_id: int):
    st.header("📦 Meine gespeicherten Produkte")
    
    rows = get_saved_products(user_id)
    
    if not rows:
        st.info("ℹ️ Noch keine Produkte gespeichert. Suche oben nach Produkten!")
        return

    st.success(f"✅ Du hast {len(rows)} Produkt(e) gespeichert")
    st.markdown("---")
    
    # NEUE METHODE: Jedes Produkt hat seinen eigenen Löschen-Button
    for row in rows:
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.markdown(f"**{row['title']}**")
            st.caption(f"Preis: {row['price']:.2f} € | Quelle: {row['source']} | {row.get('unit_price', 'N/A')}")
            st.caption(f"Gespeichert am: {row['ts_saved'][:10]}")
            if row.get('url'):
                st.caption(f"🔗 [{row['url']}]({row['url']})")
        
        with col2:
            # Jedes Produkt hat seinen eigenen Löschen-Button
            button_key = f"delete_{row['id']}"
            if st.button("🗑️ Löschen", key=button_key, type="secondary"):
                try:
                    delete_product(user_id, row['id'])
                    st.success("✅ Gelöscht!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Fehler: {e}")
        
        st.markdown("---")


# =======================
# App-Start
# =======================
def main():
    st.set_page_config(page_title="Produkte-Crawler", page_icon="🛒", layout="wide")
    db_init()

    st.title("🛒 Produkt-Suche & Preisvergleich")
    st.caption("Finde die besten Preise bei Aldi Süd und METRO")

    if "user" in st.session_state:
        col1, col2 = st.columns([6, 1])
        with col1:
            st.info(f"👤 Eingeloggt als **{st.session_state['user']['username']}**")
        with col2:
            if st.button("Logout"):
                st.session_state.pop("user")
                st.rerun()
    
    if "user" not in st.session_state:
        show_login_register()
        return

    user = st.session_state["user"]

    # Tabs für bessere Übersicht
    tab1, tab2 = st.tabs(["🔍 Suchen", "📦 Meine Produkte"])
    
    with tab1:
        show_search_and_results(user_id=user["id"])
    
    with tab2:
        show_saved_products(user_id=user["id"])


if __name__ == "__main__":
    main()