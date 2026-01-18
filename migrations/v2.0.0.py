import sqlite3
import os

db_path = os.path.join(os.getcwd(), 'aeropost.db')

def migrate():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Iniciando migração para v2.0.0 (Suporte ao papel FACILITIES_PORTARIA)...")
        
        # O SQLite não permite alterar CHECK constraints. 
        # Precisamos recriar a tabela para atualizar a constraint do ROLE.
        
        # 1. Renomear tabela atual
        cursor.execute("ALTER TABLE users RENAME TO users_old")
        
        # 2. Criar nova tabela com a constraint atualizada
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                username TEXT UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('ADMIN', 'PORTARIA', 'FACILITIES', 'USER', 'FACILITIES_PORTARIA')),
                full_name TEXT NOT NULL,
                floor TEXT,
                company TEXT,
                is_active INTEGER DEFAULT 1,
                must_change_password INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 3. Copiar dados (mapeando as colunas existentes)
        # Note: must_change_password pode ou não existir dependendo se a v1.2.2 rodou
        cursor.execute("PRAGMA table_info(users_old)")
        columns = [col[1] for col in cursor.fetchall()]
        
        col_list = "id, email, username, password_hash, role, full_name, floor, company, is_active, created_at"
        select_list = col_list
        if "must_change_password" in columns:
            col_list += ", must_change_password"
            select_list += ", must_change_password"
        
        cursor.execute(f"INSERT INTO users ({col_list}) SELECT {select_list} FROM users_old")
        
        # 4. Remover tabela antiga
        cursor.execute("DROP TABLE users_old")
        
        print("Migração v2.0.0 concluída com sucesso.")
        
    except Exception as e:
        conn.rollback()
        print(f"Erro na migração: {e}")
    finally:
        conn.commit()
        conn.close()

if __name__ == '__main__':
    migrate()
