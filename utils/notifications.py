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

def send_reset_email(recipient_email, token):
    """Envia link de recuperação de senha"""
    from app import mail
    from flask import url_for
    
    try:
        reset_link = url_for('auth.reset_password', token=token, _external=True)
        
        msg = Message(
            subject="AeroPost - Recuperação de Senha",
            recipients=[recipient_email],
            body=f"""Olá!
            
Recebemos uma solicitação para redefinir sua senha no AeroPost.

Clique no link abaixo para criar uma nova senha:
{reset_link}

Se você não solicitou isso, apenas ignore este e-mail.

Atenciosamente,
Equipe AeroPost
"""
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Erro ao enviar e-mail de reset: {e}")
        return False
