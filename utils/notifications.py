from flask_mail import Message
from flask import current_app

def send_collection_alert(recipient_email, item_id, item_type):
    """Envia um e-mail para o destinatário informando que o item está disponível"""
    from app import mail # Import aqui para evitar circular dependecy se necessário
    
    if not recipient_email or '@' not in recipient_email:
        return False
        
    try:
        msg = Message(
            subject=f"AeroPost - Encomenda {item_id} disponível para retirada",
            recipients=[recipient_email],
            body=f"""Olá!
            
Sua encomenda ({item_type}) ID {item_id} acaba de chegar e está disponível para retirada na sala de Facilities.

Por favor, apresente-se para retirar seu item.

Atenciosamente,
Equipe AeroPost / Facilities
"""
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
        return False
