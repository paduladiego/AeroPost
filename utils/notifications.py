import threading
from flask_mail import Message
from flask import current_app, url_for
import logging

def _send_async_email(app, msg):
    """Função executada em thread separada para enviar o e-mail sem bloquear o app"""
    with app.app_context():
        try:
            from app import mail
            mail.send(msg)
        except Exception as e:
            logging.error(f"Erro no envio de e-mail assíncrono: {e}")

def send_collection_alert(recipient_email, item_id, item_type):
    """Envia um e-mail para o destinatário informando que o item está disponível (Assíncrono)"""
    from .db import get_db
    
    if not recipient_email or '@' not in recipient_email:
        return False
        
    try:
        # Link para cadastro (externo)
        register_link = url_for('auth.register', _external=True)
        
        msg = Message(
            subject=f"AeroPost - Encomenda {item_id} disponível para retirada",
            recipients=[recipient_email],
            body=f"""Olá!
            
Sua encomenda ({item_type}) ID {item_id} acaba de chegar e está disponível para retirada na sala de Facilities.

Por favor, apresente-se para retirar seu item.

--------------------------------------------------
Ainda não tem conta no AeroPost? 
Cadastre-se agora para acompanhar suas encomendas em tempo real:
{register_link}
--------------------------------------------------

Atenciosamente,
Equipe AeroPost / Facilities
"""
        )
        # Dispara a thread em background
        app = current_app._get_current_object()
        threading.Thread(target=_send_async_email, args=(app, msg)).start()
        
        # Atualiza o timestamp de última notificação no banco de forma síncrona (rápido)
        try:
            db = get_db()
            db.execute("UPDATE items SET last_notified_at = CURRENT_TIMESTAMP WHERE internal_id = ?", (item_id,))
            db.commit()
        except Exception as e:
            logging.error(f"Erro ao atualizar last_notified_at: {e}")

        return True
    except Exception as e:
        logging.error(f"Erro ao preparar envio de e-mail: {e}")
        return False

def send_reset_email(recipient_email, token):
    """Envia link de recuperação de senha (Assíncrono)"""
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
        # Dispara thread
        app = current_app._get_current_object()
        threading.Thread(target=_send_async_email, args=(app, msg)).start()
        return True
    except Exception as e:
        logging.error(f"Erro ao preparar e-mail de reset: {e}")
        return False

def send_support_ticket(user_name, user_email, description, app_version, page_url):
    """Envia um e-mail de suporte para o desenvolvedor (Assíncrono)"""
    # Fallback para e-mail se estiver vazio
    sender_info = user_email if user_email else "E-mail não informado"

    try:
        msg = Message(
            subject=f"🆘 Suporte AeroPost - {user_name}",
            recipients=["kran.technology@gmail.com"],
            reply_to=user_email if user_email else None,
            body=f"""Novo chamado de suporte recebido!

De: {user_name} ({sender_info})
Versão: {app_version}
Página: {page_url}

Descrição do Problema:
--------------------------------------------------
{description}
--------------------------------------------------

Este e-mail foi gerado automaticamente pelo sistema AeroPost.
"""
        )
        # Dispara thread
        app = current_app._get_current_object()
        threading.Thread(target=_send_async_email, args=(app, msg)).start()
        return True
    except Exception as e:
        logging.error(f"Erro ao preparar e-mail de suporte: {e}")
        return False
