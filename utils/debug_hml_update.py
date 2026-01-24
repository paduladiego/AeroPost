import sqlite3
import os
import glob

def diagnose():
    # 1. Localizar Backup
    backups = glob.glob('backups/aeropost_pre_v411_*.db')
    if not backups:
        print("Erro: Nenhum backup encontrado em backups/")
        return
    
    bkp_file = max(backups, key=os.path.getctime)
    atual_file = 'aeropost.db'

    print(f"--- Diagnóstico AeroPost ---")
    print(f"Banco Atual: {atual_file}")
    print(f"Banco Backup: {bkp_file}")

    conn_atual = sqlite3.connect(atual_file)
    conn_bkp = sqlite3.connect(bkp_file)

    def get_stats(conn):
        stats = {}
        c = conn.cursor()
        try:
            stats['companies'] = c.execute("SELECT COUNT(*) FROM settings_companies").fetchone()[0]
            stats['users'] = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            stats['items'] = c.execute("SELECT COUNT(*) FROM items").fetchone()[0]
            stats['locations'] = c.execute("SELECT COUNT(*) FROM settings_locations").fetchone()[0]
            
            # Verificar unit_id
            c.execute("PRAGMA table_info(items)")
            cols = [col[1] for col in c.fetchall()]
            if 'unit_id' in cols:
                stats['items_null_unit'] = c.execute("SELECT COUNT(*) FROM items WHERE unit_id IS NULL").fetchone()[0]
            else:
                stats['items_null_unit'] = "N/A (Antigo)"
        except Exception as e:
            print(f"Erro ao ler stats: {e}")
        return stats

    s_atual = get_stats(conn_atual)
    s_bkp = get_stats(conn_bkp)

    print("\n--- Comparativo de Registros ---")
    for key in s_bkp:
        print(f"{key:15}: Atual={s_atual.get(key, 0)} | Backup={s_bkp[key]}")

    print("\n--- Unidades no Banco Atual ---")
    units = conn_atual.execute("SELECT id, name FROM settings_companies").fetchall()
    if not units:
        print("Nenhuma unidade encontrada!")
    for uid, name in units:
        i_count = conn_atual.execute("SELECT COUNT(*) FROM items WHERE unit_id = ?", (uid,)).fetchone()[0]
        u_count = conn_atual.execute("SELECT COUNT(*) FROM users WHERE default_unit_id = ?", (uid,)).fetchone()[0]
        print(f"ID {uid}: {name} ({i_count} itens, {u_count} usuários)")

    print("\n--- Verificação de .env ---")
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            print(f.read())
    else:
        print(".env não encontrado!")

    conn_atual.close()
    conn_bkp.close()

if __name__ == "__main__":
    diagnose()
