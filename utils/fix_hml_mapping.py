import sqlite3
import os

def fix_mapping():
    db_path = 'aeropost.db'
    if not os.path.exists(db_path):
        print(f"Erro: {db_path} não encontrado.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("Corrigindo mapeamento: Unificando tudo em 'Dexco' (ID 1)...")

    try:
        # 1. Mover todos os ITENS para a unidade 1 (Dexco)
        cursor.execute("UPDATE items SET unit_id = 1")
        print(f"- {cursor.rowcount} itens movidos para Dexco (ID 1).")

        # 2. Mover todos os USUÁRIOS para a unidade 1
        cursor.execute("UPDATE users SET default_unit_id = 1")
        print(f"- {cursor.rowcount} usuários vinculados à Dexco (ID 1).")

        # 3. Mover todos os LOCAIS de alocação para a unidade 1
        cursor.execute("UPDATE settings_locations SET unit_id = 1")
        print(f"- {cursor.rowcount} locais vinculados à Dexco (ID 1).")

        # 4. Mover MOVIMENTOS e GRUPOS
        cursor.execute("UPDATE movements SET unit_id = 1")
        cursor.execute("UPDATE email_groups SET unit_id = 1")
        
        conn.commit()
        print("\nSucesso: Todos os dados foram unificados na unidade Dexco.")
        print("Ao fazer login, o conteúdo histórico deve aparecer normalmente.")

    except Exception as e:
        print(f"Erro na correção: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_mapping()
