/*
Label: Datenbank-Schema (Strukturdefinition)
Ersteller: Philip Welter, Jakub Nossowski, Marie Wütz
Datum: 2025-11-27
Version: 1.0.0

Kurzbeschreibung des Moduls:
    Definiert die vollständige Tabellenstruktur (Schema) der SQLite-Datenbank ('grocery.db') 
    für das Produkt- und Einkaufsverwaltungssystem.
*/

-- Aktiviert die Unterstützung für Foreign Keys, um die referentielle Integrität zu gewährleisten
PRAGMA foreign_keys = ON;

-- Tabelle 1: users (Nutzerkonten)
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    email TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);
-- Tabelle 2: supermarkets (Erfasste Märkte)
CREATE TABLE supermarkets (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    location TEXT,
    website TEXT
);

-- Tabelle 3: products (Produktstammdaten)
CREATE TABLE products (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    brand TEXT,
    category TEXT,
    created_by_user_id TEXT,
    is_user_created INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (created_by_user_id) REFERENCES users(id)
);

-- Tabelle 4: supermarket_products (Preisinformationen)
CREATE TABLE supermarket_products (
    id TEXT PRIMARY KEY,
    supermarket_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    price REAL NOT NULL,
    available INTEGER NOT NULL DEFAULT 1,
    last_updated TEXT NOT NULL,
    FOREIGN KEY (supermarket_id) REFERENCES supermarkets(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Tabelle 5: orders (Bestellungen/Einkäufe)
CREATE TABLE orders (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    order_date TEXT NOT NULL,
    supermarket_id TEXT NOT NULL,
    total_amount REAL NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (supermarket_id) REFERENCES supermarkets(id)
);

-- Tabelle 6: order_items (Positionen einer Bestellung)
CREATE TABLE order_items (
    id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    price_at_purchase REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Tabelle 7: saved_products (Merkliste des Users)
CREATE TABLE saved_products (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    saved_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
