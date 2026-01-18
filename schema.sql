DROP TABLE IF EXISTS proofs;
DROP TABLE IF EXISTS movements;
DROP TABLE IF EXISTS items;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS settings_item_types;
DROP TABLE IF EXISTS settings_locations;
DROP TABLE IF EXISTS settings_companies;
DROP TABLE IF EXISTS settings_allowed_domains;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE, -- login for corporate users
    username TEXT UNIQUE, -- login for portaria
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('ADMIN', 'PORTARIA', 'FACILITIES', 'USER', 'FACILITIES_PORTARIA')),
    full_name TEXT NOT NULL,
    floor TEXT,
    company TEXT,
    is_active INTEGER DEFAULT 1,
    must_change_password INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    internal_id TEXT UNIQUE NOT NULL, -- AP-YYYYMMDD-XXXX
    tracking_code TEXT,
    type TEXT NOT NULL, -- ENVELOPE, CAIXA, OUTROS
    sender TEXT,
    recipient_email TEXT,
    recipient_name_manual TEXT,
    recipient_floor TEXT,
    location TEXT, -- Sala, Armario 1, 2, 3
    status TEXT NOT NULL DEFAULT 'RECEBIDO_PORTARIA',
    observation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (recipient_email) REFERENCES users (email)
);

CREATE TABLE movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES items (id),
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE proofs (
    item_id INTEGER PRIMARY KEY,
    signature_data TEXT NOT NULL, -- Base64
    delivered_by INTEGER NOT NULL,
    received_by_name TEXT NOT NULL,
    delivered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES items (id),
    FOREIGN KEY (delivered_by) REFERENCES users (id)
);

CREATE TABLE settings_item_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    is_active INTEGER DEFAULT 1
);

CREATE TABLE settings_locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    is_active INTEGER DEFAULT 1
);

CREATE TABLE settings_companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    is_active INTEGER DEFAULT 1
);

CREATE TABLE settings_allowed_domains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain TEXT NOT NULL UNIQUE, -- e.g. @dex.co
    is_active INTEGER DEFAULT 1
);
