DROP TABLE IF EXISTS proofs;
DROP TABLE IF EXISTS movements;
DROP TABLE IF EXISTS items;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE, -- login for corporate users
    username TEXT UNIQUE, -- login for portaria
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('ADMIN', 'PORTARIA', 'FACILITIES', 'USER')),
    full_name TEXT NOT NULL,
    floor TEXT,
    company TEXT,
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
