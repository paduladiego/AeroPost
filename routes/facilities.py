import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from utils.db import get_db
from utils.auth import login_required, role_required
from utils.notifications import send_collection_alert

facilities_bp = Blueprint('facilities', __name__)

@facilities_bp.route('/facilities')
@login_required
@role_required(['FACILITIES', 'ADMIN', 'FACILITIES_PORTARIA'])
def dashboard():
    db = get_db()
    unit_id = session.get('unit_id')
    stats = {
        'in_portaria': db.execute("SELECT COUNT(*) FROM items WHERE status = 'RECEBIDO_PORTARIA' AND unit_id = ?", (unit_id,)).fetchone()[0],
        'in_facilities': db.execute("SELECT COUNT(*) FROM items WHERE status = 'EM_FACILITIES' AND unit_id = ?", (unit_id,)).fetchone()[0],
        'ready': db.execute("SELECT COUNT(*) FROM items WHERE status = 'DISPONIVEL_PARA_RETIRADA' AND unit_id = ?", (unit_id,)).fetchone()[0]
    }
    
    query_base = """
        SELECT i.*, u.floor as user_floor, u.company as user_company,
               (CASE WHEN u.id IS NOT NULL THEN 1 ELSE 0 END) as is_registered
        FROM items i 
        LEFT JOIN users u ON i.recipient_email = u.email
    """
    
    items_portaria = db.execute(query_base + " WHERE i.status = 'RECEBIDO_PORTARIA' AND i.unit_id = ? ORDER BY i.created_at ASC", (unit_id,)).fetchall()
    items_facilities = db.execute(query_base + " WHERE i.status = 'EM_FACILITIES' AND i.unit_id = ? ORDER BY i.updated_at ASC", (unit_id,)).fetchall()
    items_ready = db.execute(query_base + " WHERE i.status = 'DISPONIVEL_PARA_RETIRADA' AND i.unit_id = ? ORDER BY i.updated_at DESC", (unit_id,)).fetchall()

    corp_users = db.execute("SELECT email, full_name FROM users WHERE is_active = 1 AND role != 'ADMIN' AND default_unit_id = ? ORDER BY full_name ASC", (unit_id,)).fetchall()
    locations = db.execute("SELECT * FROM settings_locations WHERE is_active = 1 AND unit_id = ? ORDER BY name ASC", (unit_id,)).fetchall()
    email_groups = db.execute("SELECT * FROM email_groups WHERE unit_id = ? ORDER BY name ASC", (unit_id,)).fetchall()

    return render_template('facilities/dashboard.html', 
                           stats=stats, 
                           items_portaria=items_portaria, 
                           items_facilities=items_facilities, 
                           items_ready=items_ready, 
                           corp_users=corp_users,
                           locations=locations,
                           email_groups=email_groups)

@facilities_bp.route('/facilities/collect/<int:item_id>', methods=['POST'])
@login_required
@role_required(['FACILITIES', 'ADMIN', 'FACILITIES_PORTARIA'])
def collect(item_id):
    db = get_db()
    unit_id = session.get('unit_id')
    db.execute("UPDATE items SET status = 'EM_FACILITIES', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (item_id,))
    db.execute("INSERT INTO movements (item_id, user_id, action, unit_id) VALUES (?, ?, ?, ?)", (item_id, session['user_id'], 'COLLECT_FROM_PORTARIA', unit_id))
    db.commit()
    flash('Item coletado com sucesso.', 'success')
    return redirect(url_for('facilities.dashboard', tab='portaria'))

@facilities_bp.route('/facilities/allocate/<int:item_id>', methods=['POST'])
@login_required
@role_required(['FACILITIES', 'ADMIN', 'FACILITIES_PORTARIA'])
def allocate(item_id):
    location = request.form['location']
    rec_email = request.form.get('recipient_email')
    rec_manual = request.form.get('recipient_name_manual')
    rec_floor = request.form.get('recipient_floor')
    observation = request.form.get('observation')

    if rec_email == '__NEW__':
        rec_email = None

    if not rec_email and rec_manual and '@' in rec_manual:
        rec_email = rec_manual
    
    db = get_db()
    unit_id = session.get('unit_id')
    db.execute(
        "UPDATE items SET status = 'DISPONIVEL_PARA_RETIRADA', location = ?, recipient_email = ?, recipient_name_manual = ?, recipient_floor = ?, observation = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", 
        (location, rec_email, rec_manual, rec_floor, observation, item_id)
    )
    db.execute("INSERT INTO movements (item_id, user_id, action, unit_id) VALUES (?, ?, ?, ?)", (item_id, session['user_id'], f'ALLOCATED: {location} AND ID_RECIPIENT | {observation or ""}', unit_id))
    db.commit()

    # Envio de Notificação por E-mail
    if rec_email:
        # Busca o tipo do item para o e-mail
        item = db.execute("SELECT type, internal_id FROM items WHERE id = ?", (item_id,)).fetchone()
        
        # Verifica se o rec_email é um GRUPO (identificado pelo prefixo [G] ou similar, ou busca direta)
        group = db.execute("SELECT id FROM email_groups WHERE name = ?", (rec_email,)).fetchone()
        
        if group:
            members = db.execute("SELECT email FROM email_group_members WHERE group_id = ?", (group['id'],)).fetchall()
            emails_sent = 0
            for member in members:
                if send_collection_alert(member['email'], item['internal_id'], item['type']):
                    emails_sent += 1
            
            flash(f'Item alocado para o grupo "{rec_email}". {emails_sent} notificações enviadas!', 'success')
        else:
            if send_collection_alert(rec_email, item['internal_id'], item['type']):
                flash(f'Item alocado em {location} para {rec_email or rec_manual}. Notificação enviada!', 'success')
            else:
                flash(f'Item alocado em {location}, mas houve um erro ao enviar o e-mail.', 'warning')
    else:
        flash(f'Item alocado em {location} para {rec_manual}. (Sem e-mail para notificar)', 'success')
        
    return redirect(url_for('facilities.dashboard', tab='triagem'))

@facilities_bp.route('/facilities/update_location/<int:item_id>', methods=['POST'])
@login_required
@role_required(['FACILITIES', 'ADMIN', 'FACILITIES_PORTARIA'])
def update_location(item_id):
    new_location = request.form['location']
    db = get_db()
    
    # Busca o local atual antes de atualizar
    current_item = db.execute("SELECT location FROM items WHERE id = ?", (item_id,)).fetchone()
    old_location = current_item['location'] if current_item else "?"
    
    unit_id = session.get('unit_id')
    db.execute("UPDATE items SET location = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_location, item_id))
    
    # Registra no histórico: NovoLocal | Velho -> Novo
    action_str = f'LOCATION_CHANGED_TO: {new_location} | {old_location} ➔ {new_location}'
    db.execute("INSERT INTO movements (item_id, user_id, action, unit_id) VALUES (?, ?, ?, ?)", 
               (item_id, session['user_id'], action_str, unit_id))
    
    db.commit()
    flash('Local atualizado com sucesso.', 'success')
    return redirect(url_for('facilities.dashboard', tab='entregar'))

@facilities_bp.route('/delivery/password/<int:item_id>')
@login_required
@role_required(['FACILITIES', 'ADMIN', 'FACILITIES_PORTARIA'])
def delivery_password_page(item_id):
    db = get_db()
    item = db.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    
    # Prioritiza e-mail vindo da URL (digitado na tela de assinatura)
    display_email = request.args.get('email')
    
    if not display_email:
        display_email = item['recipient_email']
        if not display_email and item['recipient_name_manual'] and '@' in item['recipient_name_manual']:
            display_email = item['recipient_name_manual']

    if not display_email:
        flash('Este item não possui um destinatário cadastrado para validar via senha.', 'danger')
        return redirect(url_for('facilities.dashboard'))
        
    return render_template('delivery_password.html', item=item, display_email=display_email)

@facilities_bp.route('/delivery/confirm_password/<int:item_id>', methods=['POST'])
@login_required
@role_required(['FACILITIES', 'ADMIN', 'FACILITIES_PORTARIA'])
def delivery_password_confirm(item_id):
    email = request.form['email']
    from werkzeug.security import check_password_hash
    password = request.form['password']
    
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    
    if user is None or not check_password_hash(user['password_hash'], password):
        flash('Senha incorreta para o destinatário informado.', 'danger')
        return redirect(url_for('facilities.delivery_password_page', item_id=item_id))
    
    unit_id = session.get('unit_id')
    db.execute("UPDATE items SET status = 'ENTREGUE', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (item_id,))
    
    placeholder_sig = "DATA:AUTHENTICATED_BY_PASSWORD"
    db.execute(
        "INSERT OR REPLACE INTO proofs (item_id, signature_data, delivered_by, received_by_name, delivered_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
        (item_id, placeholder_sig, session['user_id'], user['full_name'])
    )
    
    db.execute("INSERT INTO movements (item_id, user_id, action, unit_id) VALUES (?, ?, ?, ?)", (item_id, session['user_id'], 'DELIVERED_VIA_PASSWORD', unit_id))
    db.commit()
    
    flash(f'Item entregue com sucesso para {user["full_name"]} via autenticação!', 'success')
    return redirect(url_for('facilities.dashboard', tab='entregar'))

@facilities_bp.route('/delivery/<int:item_id>')
@login_required
@role_required(['FACILITIES', 'ADMIN', 'FACILITIES_PORTARIA'])
def delivery_page(item_id):
    db = get_db()
    item = db.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    return render_template('delivery.html', item=item)

@facilities_bp.route('/delivery/confirm/<int:item_id>', methods=['POST'])
@login_required
@role_required(['FACILITIES', 'ADMIN', 'FACILITIES_PORTARIA'])
def delivery_confirm(item_id):
    received_by = request.form['received_by_name']
    signature = request.form['signature_data']
    
    db = get_db()
    unit_id = session.get('unit_id')
    db.execute("UPDATE items SET status = 'ENTREGUE', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (item_id,))
    
    db.execute(
        "INSERT OR REPLACE INTO proofs (item_id, signature_data, delivered_by, received_by_name, delivered_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
        (item_id, signature, session['user_id'], received_by)
    )
    
    db.execute("INSERT INTO movements (item_id, user_id, action, unit_id) VALUES (?, ?, ?, ?)", (item_id, session['user_id'], 'DELIVERED', unit_id))
    db.commit()
    
    flash(f'Item entregue com sucesso para {received_by}!', 'success')
    return redirect(url_for('facilities.dashboard', tab='entregar'))

@facilities_bp.route('/facilities/resend_alert/<int:item_id>', methods=['POST'])
@login_required
@role_required(['FACILITIES', 'ADMIN', 'FACILITIES_PORTARIA'])
def resend_alert(item_id):
    db = get_db()
    item = db.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    
    if not item:
        flash('Item não encontrado.', 'danger')
        return redirect(url_for('facilities.dashboard', tab='entregar'))

    rec_email = item['recipient_email']
    if not rec_email and item['recipient_name_manual'] and '@' in item['recipient_name_manual']:
        rec_email = item['recipient_name_manual']

    if rec_email:
        # Verifica se é um grupo
        group = db.execute("SELECT id FROM email_groups WHERE name = ?", (rec_email,)).fetchone()
        
        if group:
            members = db.execute("SELECT email FROM email_group_members WHERE group_id = ?", (group['id'],)).fetchall()
            emails_sent = 0
            for member in members:
                if send_collection_alert(member['email'], item['internal_id'], item['type']):
                    emails_sent += 1
            flash(f'Alertas reenviados para o grupo "{rec_email}". {emails_sent} notificações enviadas!', 'success')
        else:
            if send_collection_alert(rec_email, item['internal_id'], item['type']):
                flash(f'Alerta de reenvio enviado para {rec_email}!', 'success')
            else:
                flash(f'Erro ao reenviar e-mail para {rec_email}.', 'warning')
    else:
        flash('Destinatário não possui e-mail cadastrado.', 'warning')

    return redirect(url_for('facilities.dashboard', tab='entregar'))

@facilities_bp.route('/facilities/register-occurrence', methods=['POST'])
@login_required
@role_required(['FACILITIES', 'ADMIN', 'FACILITIES_PORTARIA'])
def register_occurrence():
    from werkzeug.security import check_password_hash
    db = get_db()
    
    internal_id = request.form.get('internal_id')
    action = request.form.get('action')
    note = request.form.get('note')
    password = request.form.get('password')
    unit_id = session.get('unit_id')
    
    # 1. Validar Senha do Operador
    user = db.execute("SELECT password_hash FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    if not check_password_hash(user['password_hash'], password):
        flash('Senha de confirmação incorreta. O registro não foi salvo.', 'danger')
        return redirect(url_for('facilities.dashboard', tab='entregar')) # Abre o modal via JS

    # 2. Buscar o Item
    item = db.execute("SELECT * FROM items WHERE internal_id = ? AND unit_id = ?", (internal_id, unit_id)).fetchone()
    if not item:
        flash(f'Item com ID "{internal_id}" não encontrado nesta unidade.', 'danger')
        return redirect(url_for('facilities.dashboard'))

    # 3. Processar Ação
    if action in ('EXTRAVIADO', 'DEVOLVIDO'):
        # Move para o histórico com nota
        db.execute("UPDATE items SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (action, item['id']))
        
        # Insere ou Atualiza Proof (Comprovante será a nota de ocorrência)
        db.execute("INSERT OR REPLACE INTO proofs (item_id, signature_data, delivered_by, received_by_name, delivered_at, occurrence_note) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?)",
                   (item['id'], f"OCCURRENCE_{action}", session['user_id'], f"SISTEMA: {action}", note))
        
        db.execute("INSERT INTO movements (item_id, user_id, action, unit_id) VALUES (?, ?, ?, ?)", 
                   (item['id'], session['user_id'], f'RECORDED_OCCURRENCE: {action} | {note or ""}', unit_id))
        
        flash(f'Ocorrência de {action} registrada para o item {internal_id}.', 'warning')

    elif action == 'RECUPERADO':
        # REGRA: Se o item está DEVOLVIDO ou ENTREGUE, apenas ADMIN pode recuperar
        if item['status'] in ['DEVOLVIDO', 'ENTREGUE'] and session.get('role') != 'ADMIN':
            flash('Apenas administradores podem recuperar itens marcados como devolvidos ou já entregues.', 'danger')
            return redirect(url_for('facilities.dashboard'))

        # Volta para triagem (Alocar Local)
        db.execute("UPDATE items SET status = 'EM_FACILITIES', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (item['id'],))
        
        # Insere nota de recuperação na prova (ou substitui a anterior) para rastro
        db.execute("INSERT OR REPLACE INTO proofs (item_id, signature_data, delivered_by, received_by_name, delivered_at, occurrence_note) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?)",
                   (item['id'], "OCCURRENCE_RECUPERADO", session['user_id'], "SISTEMA: RECUPERADO", note))
        
        db.execute("INSERT INTO movements (item_id, user_id, action, unit_id) VALUES (?, ?, ?, ?)", 
                   (item['id'], session['user_id'], f'RECOVERED_ITEM | {note or ""}', unit_id))
        
        flash(f'Item {internal_id} recuperado! Ele voltou para a aba "2. Alocar Local".', 'success')

    db.commit()
    return redirect(url_for('facilities.dashboard'))

@facilities_bp.route('/facilities/check-item-status/<internal_id>')
@login_required
@role_required(['FACILITIES', 'ADMIN', 'FACILITIES_PORTARIA'])
def check_item_status(internal_id):
    db = get_db()
    unit_id = session.get('unit_id')
    item = db.execute("SELECT status FROM items WHERE internal_id = ? AND unit_id = ?", (internal_id, unit_id)).fetchone()
    
    if item:
        return {"status": item['status']}, 200
    return {"error": "Item não encontrado"}, 404
