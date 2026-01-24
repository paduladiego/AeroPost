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

    print("Starting migration v4.1.0 (Audit and Occurrences)...")

    try:
        # Add occurrence_note to proofs table
        print("Checking for 'occurrence_note' in 'proofs' table...")
        
        # O SQLite não dá erro se a coluna já existir em algumas versões de comando, 
        # mas aqui fazemos a verificação manual para ser seguro e idempotente.
        cursor.execute("PRAGMA table_info(proofs)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'occurrence_note' not in columns:
            cursor.execute("ALTER TABLE proofs ADD COLUMN occurrence_note TEXT")
            print("- Column 'occurrence_note' added to 'proofs' table.")
        else:
            print("- Column 'occurrence_note' already exists in 'proofs' table.")

        conn.commit()
        print("Migration v4.1.0 completed successfully.")

    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
