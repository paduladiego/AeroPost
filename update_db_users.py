import sqlite3
from app import app, get_db

def migrate():
    with app.app_context():
        db = get_db()
        try:
            # Add is_active column, default to 1 (True)
            db.execute("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1")
            db.commit()
            print("Successfully added 'is_active' column to users table.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("Column 'is_active' already exists.")
            else:
                print(f"Error: {e}")

if __name__ == "__main__":
    migrate()
