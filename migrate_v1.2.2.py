import sqlite3
import os

db_path = os.path.join(os.getcwd(), 'aeropost.db')

def migrate():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Adicionando coluna 'must_change_password' na tabela 'users'...")
        cursor.execute("ALTER TABLE users ADD COLUMN must_change_password INTEGER DEFAULT 0")
        print("Coluna adicionada com sucesso.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("A coluna 'must_change_password' já existe.")
        else:
            print(f"Erro ao alterar tabela: {e}")
            
    conn.commit()
    conn.close()

if __name__ == '__main__':
    migrate()
