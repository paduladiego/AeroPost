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

    print("Starting migration v3.1.4 (Notifications)...")

    try:
        # Add last_notified_at to items table
        cursor.execute("ALTER TABLE items ADD COLUMN last_notified_at TIMESTAMP")
        print("Column 'last_notified_at' added to 'items' table.")

        # Initialize last_notified_at with updated_at for existing items
        cursor.execute("UPDATE items SET last_notified_at = updated_at WHERE last_notified_at IS NULL")
        print("Existing items updated with initial notification timestamp.")

        conn.commit()
        print("Migration v3.1.4 completed successfully.")

    except Exception as e:
        if "duplicate column name" in str(e).lower():
            print("Migration already applied: Column 'last_notified_at' exists.")
        else:
            print(f"Migration failed: {e}")
            conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
