import sqlite3
import os

DATABASE = 'aeropost.db'

def migrate():
    if not os.path.exists(DATABASE):
        print(f"Erro: {DATABASE} não encontrado.")
        return

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    print("Iniciando migração para v1.2.0...")

    # Novas Tabelas
    tables = [
        """
        CREATE TABLE IF NOT EXISTS settings_item_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            is_active INTEGER DEFAULT 1
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS settings_locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            is_active INTEGER DEFAULT 1
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS settings_companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            is_active INTEGER DEFAULT 1
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS settings_allowed_domains (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL UNIQUE,
            is_active INTEGER DEFAULT 1
        )
        """
    ]

    for table_sql in tables:
        cursor.execute(table_sql)

    # Dados Iniciais (Defaults)
    # Tipos
    types = ['ENVELOPE/CARTA', 'CAIXA/PACOTE', 'OUTROS']
    for t in types:
        cursor.execute("INSERT OR IGNORE INTO settings_item_types (name) VALUES (?)", (t,))

    # Locais
    locs = ['Armário 1', 'Armário 2', 'Armário 3', 'Sala Facilities']
    for l in locs:
        cursor.execute("INSERT OR IGNORE INTO settings_locations (name) VALUES (?)", (l,))

    # Empresas
    companies = ['Dexco', 'Deca', 'Outra']
    for c in companies:
        cursor.execute("INSERT OR IGNORE INTO settings_companies (name) VALUES (?)", (c,))

    # Domínios
    domains = ['@dex.co', '@deca.com.br']
    for d in domains:
        cursor.execute("INSERT OR IGNORE INTO settings_allowed_domains (domain) VALUES (?)", (d,))

    conn.commit()
    conn.close()
    print("Migração concluída com sucesso!")

if __name__ == '__main__':
    migrate()
