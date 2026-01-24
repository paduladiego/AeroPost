import sqlite3
import os
from datetime import datetime, timedelta

def populate_full_lifecycle():
    # Tenta ler do .env ou usa o padrão
    db_path = os.environ.get('DATABASE_URL', 'aeropost.db')
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("Populating full lifecycle test data for Desire Studio divisions...")

    try:
        # 1. Garantir Unidades (Divisões da Desire Studio Ltda)
        divisions = ["Newdreams", "Kran", "Mojuganide", "Desire", "YXO"]
        for div in divisions:
            cursor.execute("INSERT OR IGNORE INTO settings_companies (name, is_active) VALUES (?, 1)", (div,))
        conn.commit()

        units = cursor.execute("SELECT id, name FROM settings_companies WHERE is_active = 1").fetchall()
        
        # Filtra apenas as unidades que acabamos de garantir (para evitar poluir se houver outras)
        active_units = [u for u in units if u['name'] in divisions]

        # 2. Garantir um Usuário para os movimentos (Admin)
        admin = cursor.execute("SELECT id FROM users WHERE role = 'ADMIN' LIMIT 1").fetchone()
        if not admin:
            print("Notice: No ADMIN user found. Creating dummy movements unlinked or with ID 1.")
            admin_id = 1
        else:
            admin_id = admin['id']

        # 3. Mapeamento de Estágios e Dados por Unidade
        # Vamos criar um set de dados completo para cada divisão
        
        for unit in active_units:
            uid = unit['id']
            name = unit['name']
            pfx = name[:3].upper()
            
            print(f"Populating unit: {name} ({pfx})")

            # Garantir Local padrão para a unidade
            loc_name = f"Recepção {name}"
            cursor.execute("INSERT OR IGNORE INTO settings_locations (name, unit_id) VALUES (?, ?)", (loc_name, uid))

            # --- ITEM 1: PORTARIA ---
            cursor.execute("""
                INSERT OR IGNORE INTO items (internal_id, tracking_code, type, sender, status, unit_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (f'AP-{pfx}-PORT-01', f'TRK-{pfx}-001', 'Caixa', 'Fornecedor XYZ', 'RECEBIDO_PORTARIA', uid))

            # --- ITEM 2: EM FACILITIES (TRIAGEM) ---
            cursor.execute("""
                INSERT OR IGNORE INTO items (internal_id, tracking_code, type, sender, status, unit_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (f'AP-{pfx}-FACI-02', f'TRK-{pfx}-002', 'Envelope', 'Sedex Internacional', 'EM_FACILITIES', uid))

            # --- ITEM 3: DISPONÍVEL (ALOCADO) ---
            cursor.execute("""
                INSERT OR IGNORE INTO items (internal_id, tracking_code, type, sender, status, unit_id, location, recipient_name_manual)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (f'AP-{pfx}-RDY-03', f'TRK-{pfx}-003', 'Pacote', 'Amazon Brasil', 'DISPONIVEL_PARA_RETIRADA', uid, loc_name, f'Colaborador {name}'))

            # --- ITEM 4: ENTREGUE (HISTÓRICO) ---
            item_id_hist = f'AP-{pfx}-HIST-04'
            cursor.execute("""
                INSERT OR IGNORE INTO items (internal_id, tracking_code, type, sender, status, unit_id, location, recipient_name_manual)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (item_id_hist, f'TRK-{pfx}-004', 'Outros', 'Mercado Livre', 'ENTREGUE', uid, loc_name, 'Joao Silva Demo'))
            
            # Precisamos do ID real do item entregue para o Proof
            db_item = cursor.execute("SELECT id FROM items WHERE internal_id = ?", (item_id_hist,)).fetchone()
            if db_item:
                item_db_id = db_item['id']
                # Proof (Assinatura base64 dummy)
                cursor.execute("""
                    INSERT OR IGNORE INTO proofs (item_id, signature_data, delivered_by, received_by_name, delivered_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (item_db_id, 'DATA:DUMMY_SIGNATURE_AUTO_GEN', admin_id, 'Joao Silva Demo', datetime.now() - timedelta(days=1)))
                
                # Movimento de Entrega
                cursor.execute("""
                    INSERT OR IGNORE INTO movements (item_id, user_id, action, unit_id)
                    VALUES (?, ?, ?, ?)
                """, (item_db_id, admin_id, 'DELIVERED', uid))

            # --- ITEM 5: DEVOLVIDO (OCORRÊNCIA) ---
            item_id_dev = f'AP-{pfx}-DEV-05'
            cursor.execute("""
                INSERT OR IGNORE INTO items (internal_id, tracking_code, type, sender, status, unit_id, location, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (item_id_dev, f'TRK-{pfx}-005', 'Caixa', 'Fornecedor Errado', 'DEVOLVIDO', uid, loc_name, datetime.now()))
            
            db_item_dev = cursor.execute("SELECT id FROM items WHERE internal_id = ?", (item_id_dev,)).fetchone()
            if db_item_dev:
                cursor.execute("""
                    INSERT OR IGNORE INTO proofs (item_id, signature_data, delivered_by, received_by_name, delivered_at, occurrence_note)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (db_item_dev['id'], 'OCCURRENCE_DEVOLVIDO', admin_id, 'SISTEMA: DEVOLVIDO', datetime.now(), 'Destinatário recusou o recebimento.'))

            # --- ITEM 6: EXTRAVIADO (OCORRÊNCIA) ---
            item_id_lost = f'AP-{pfx}-LOST-06'
            cursor.execute("""
                INSERT OR IGNORE INTO items (internal_id, tracking_code, type, sender, status, unit_id, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (item_id_lost, f'TRK-{pfx}-006', 'Envelope', 'Correios', 'EXTRAVIADO', uid, datetime.now()))
            
            db_item_lost = cursor.execute("SELECT id FROM items WHERE internal_id = ?", (item_id_lost,)).fetchone()
            if db_item_lost:
                cursor.execute("""
                    INSERT OR IGNORE INTO proofs (item_id, signature_data, delivered_by, received_by_name, delivered_at, occurrence_note)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (db_item_lost['id'], 'OCCURRENCE_EXTRAVIADO', admin_id, 'SISTEMA: EXTRAVIADO', datetime.now(), 'Item não localizado na triagem.'))

        conn.commit()
        print(f"Success! Full lifecycle items created for divisions: {', '.join(divisions)}.")

    except Exception as e:
        print(f"Error populating data: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    populate_full_lifecycle()
