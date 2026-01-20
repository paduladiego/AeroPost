import sqlite3
import os

def migrate():
    # Tenta ler do .env ou usa o padrão
    db_path = os.environ.get('DATABASE_URL', 'aeropost.db')
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("Starting migration v2.1.0...")

    try:
        # Create email_groups table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("Table 'email_groups' created.")

        # Create email_group_members table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_group_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            email TEXT NOT NULL,
            FOREIGN KEY (group_id) REFERENCES email_groups (id) ON DELETE CASCADE
        )
        """)
        print("Table 'email_group_members' created.")

        conn.commit()
        print("Migration v2.1.0 completed successfully.")

    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
