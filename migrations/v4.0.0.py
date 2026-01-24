import sqlite3
import os

def migrate():
    # Tenta ler do .env ou usa o padrão
    db_path = os.environ.get('DATABASE_URL', 'aeropost.db')
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("Starting migration v4.0.0 (Multi-Unit Implementation)...")

    try:
        # 1. Adicionar colunas unit_id (permitindo NULL inicialmente para o populate)
        print("Adding unit_id columns...")
        
        # settings_locations
        try:
            cursor.execute("ALTER TABLE settings_locations ADD COLUMN unit_id INTEGER REFERENCES settings_companies(id)")
            print("- Added unit_id to settings_locations")
        except sqlite3.OperationalError:
            print("- unit_id already exists in settings_locations")

        # users
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN default_unit_id INTEGER REFERENCES settings_companies(id)")
            print("- Added default_unit_id to users")
        except sqlite3.OperationalError:
            print("- default_unit_id already exists in users")

        # items
        try:
            cursor.execute("ALTER TABLE items ADD COLUMN unit_id INTEGER REFERENCES settings_companies(id)")
            print("- Added unit_id to items")
        except sqlite3.OperationalError:
            print("- unit_id already exists in items")

        # email_groups
        try:
            cursor.execute("ALTER TABLE email_groups ADD COLUMN unit_id INTEGER REFERENCES settings_companies(id)")
            print("- Added unit_id to email_groups")
        except sqlite3.OperationalError:
            print("- unit_id already exists in email_groups")

        # movements
        try:
            cursor.execute("ALTER TABLE movements ADD COLUMN unit_id INTEGER REFERENCES settings_companies(id)")
            print("- Added unit_id to movements")
        except sqlite3.OperationalError:
            print("- unit_id already exists in movements")

        conn.commit()

        # 2. POPULATE (Data Migration)
        print("Migrating data to unified units...")
        
        # Garantir que existe pelo menos uma empresa cadastrada (Sede)
        companies = cursor.execute("SELECT id, name FROM settings_companies").fetchall()
        if not companies:
            print("No companies found. Creating 'Sede Central' as default.")
            cursor.execute("INSERT INTO settings_companies (name) VALUES (?)", ("Sede Central",))
            conn.commit()
            companies = cursor.execute("SELECT id, name FROM settings_companies").fetchall()
        
        default_unit = companies[0] # Usa a primeira encontrada como padrão
        print(f"Default unit for migration: {default_unit['name']} (ID: {default_unit['id']})")

        # Vincular Usuários baseado no texto do campo 'company'
        users = cursor.execute("SELECT id, company FROM users").fetchall()
        for user in users:
            match_id = default_unit['id']
            if user['company']:
                for comp in companies:
                    if comp['name'].lower() in user['company'].lower():
                        match_id = comp['id']
                        break
            cursor.execute("UPDATE users SET default_unit_id = ? WHERE id = ?", (match_id, user['id']))
        print(f"- Migrated {len(users)} users to their respective units.")

        # Vincular Locais (settings_locations) à unidade padrão por enquanto
        # (Em uma planta real, o admin teria que ajustar isso manualmente se houver multiplas)
        cursor.execute("UPDATE settings_locations SET unit_id = ? WHERE unit_id IS NULL", (default_unit['id'],))
        print("- Linked all locations to default unit.")

        # Vincular Itens
        # Se o item tem localização, herda a unidade do local. Se não, herda da empresa do destinatário.
        cursor.execute("""
            UPDATE items 
            SET unit_id = COALESCE(
                (SELECT unit_id FROM settings_locations WHERE name = items.location),
                (SELECT default_unit_id FROM users WHERE email = items.recipient_email),
                ?
            )
            WHERE unit_id IS NULL
        """, (default_unit['id'],))
        print("- Linked all items to detected units.")

        # Vincular Movements e Email Groups
        cursor.execute("UPDATE movements SET unit_id = ? WHERE unit_id IS NULL", (default_unit['id'],))
        cursor.execute("UPDATE email_groups SET unit_id = ? WHERE unit_id IS NULL", (default_unit['id'],))

        conn.commit()
        print("Migration v4.0.0 completed successfully.")

    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
