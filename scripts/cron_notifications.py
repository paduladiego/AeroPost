import os
import sys
import sqlite3
from datetime import datetime, timedelta

# Adiciona o diretório raiz ao path para importar módulos locais
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from utils.notifications import send_collection_alert

def run_cron():
    app = create_app()
    with app.app_context():
        db_path = app.config['DATABASE']
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        print(f"[{datetime.now()}] Iniciando verificação de notificações pendentes...")

        # Busca itens disponíveis para retirada que não foram notificados nos últimos 3 dias
        # Considera modified_at se last_notified_at for NULL (embora a migração tenha preenchido)
        query = """
            SELECT * FROM items 
            WHERE status = 'DISPONIVEL_PARA_RETIRADA' 
            AND (
                last_notified_at IS NULL 
                OR datetime(last_notified_at) <= datetime('now', '-3 days')
            )
        """
        items = cursor.execute(query).fetchall()

        if not items:
            print("Nenhum item pendente de nova notificação.")
            return

        for item in items:
            rec_email = item['recipient_email']
            # Se não tem e-mail corporativo, tenta o manual se for um e-mail
            if not rec_email and item['recipient_name_manual'] and '@' in item['recipient_name_manual']:
                rec_email = item['recipient_name_manual']

            if rec_email:
                print(f"Reenviando alerta para {rec_email} (Item: {item['internal_id']})")
                
                # Verifica se é um grupo
                group = cursor.execute("SELECT id FROM email_groups WHERE name = ?", (rec_email,)).fetchone()
                
                success = False
                if group:
                    members = cursor.execute("SELECT email FROM email_group_members WHERE group_id = ?", (group['id'],)).fetchall()
                    for member in members:
                        if send_collection_alert(member['email'], item['internal_id'], item['type']):
                            success = True
                else:
                    if send_collection_alert(rec_email, item['internal_id'], item['type']):
                        success = True
                
                if success:
                    print(f"Notificação enviada com sucesso para {item['internal_id']}")
                else:
                    print(f"Falha ao enviar notificação para {item['internal_id']}")
            else:
                print(f"Item {item['internal_id']} sem e-mail para notificação.")

        conn.close()
        print(f"[{datetime.now()}] Cron finalizado.")

if __name__ == "__main__":
    run_cron()
