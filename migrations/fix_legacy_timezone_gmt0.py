import sqlite3
import os

def migrate():
    # Detecta o banco de dados
    db_path = os.environ.get('DATABASE_URL', 'aeropost.db')
    print(f"Iniciando correção de fuso horário no banco: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 1. Ajustar tabela ITEMS
        print("Ajustando tabela 'items'...")
        cursor.execute("UPDATE items SET created_at = datetime(created_at, '-3 hours') WHERE created_at IS NOT NULL")
        cursor.execute("UPDATE items SET updated_at = datetime(updated_at, '-3 hours') WHERE updated_at IS NOT NULL")
        cursor.execute("UPDATE items SET last_notified_at = datetime(last_notified_at, '-3 hours') WHERE last_notified_at IS NOT NULL")

        # 2. Ajustar tabela MOVEMENTS
        print("Ajustando tabela 'movements'...")
        cursor.execute("UPDATE movements SET timestamp = datetime(timestamp, '-3 hours') WHERE timestamp IS NOT NULL")

        # 3. Ajustar tabela PROOFS
        print("Ajustando tabela 'proofs'...")
        cursor.execute("UPDATE proofs SET delivered_at = datetime(delivered_at, '-3 hours') WHERE delivered_at IS NOT NULL")

        # 4. Ajustar tabela USERS
        print("Ajustando tabela 'users'...")
        cursor.execute("UPDATE users SET created_at = datetime(created_at, '-3 hours') WHERE created_at IS NOT NULL")

        # 5. Ajustar tabela EMAIL_GROUPS
        print("Ajustando tabela 'email_groups'...")
        cursor.execute("UPDATE email_groups SET created_at = datetime(created_at, '-3 hours') WHERE created_at IS NOT NULL")

        conn.commit()
        print("✅ Correção de fuso horário (-3h) concluída com sucesso!")

    except Exception as e:
        conn.rollback()
        print(f"❌ Erro durante a migração: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
