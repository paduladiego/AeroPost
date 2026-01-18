from app import app, init_db, get_db
from werkzeug.security import generate_password_hash
import sqlite3

if __name__ == "__main__":
    with app.app_context():
        print("Initializing database...")
        init_db()
        print("Database initialized.")
        
        print("Creating admin user...")
        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (username, role, full_name, password_hash) VALUES (?, ?, ?, ?)",
                ('admin', 'ADMIN', 'Administrador Sistema', generate_password_hash('admin123'))
            )
            db.commit()
            print("Admin user created: admin / admin123")
        except sqlite3.IntegrityError:
            print("Admin user already exists.")
