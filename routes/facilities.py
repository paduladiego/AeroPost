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
    stats = {
        'in_portaria': db.execute("SELECT COUNT(*) FROM items WHERE status = 'RECEBIDO_PORTARIA'").fetchone()[0],
        'in_facilities': db.execute("SELECT COUNT(*) FROM items WHERE status = 'EM_FACILITIES'").fetchone()[0],
        'ready': db.execute("SELECT COUNT(*) FROM items WHERE status = 'DISPONIVEL_PARA_RETIRADA'").fetchone()[0]
    }
    
    query_base = """
        SELECT i.*, u.floor as user_floor, u.company as user_company,
               (CASE WHEN u.id IS NOT NULL THEN 1 ELSE 0 END) as is_registered
        FROM items i 
        LEFT JOIN users u ON i.recipient_email = u.email
    """
    
    items_portaria = db.execute(query_base + " WHERE i.status = 'RECEBIDO_PORTARIA' ORDER BY i.created_at ASC").fetchall()
    items_facilities = db.execute(query_base + " WHERE i.status = 'EM_FACILITIES' ORDER BY i.updated_at ASC").fetchall()
    items_ready = db.execute(query_base + " WHERE i.status = 'DISPONIVEL_PARA_RETIRADA' ORDER BY i.updated_at DESC").fetchall()

    corp_users = db.execute("SELECT email, full_name FROM users WHERE is_active = 1 AND role != 'ADMIN' ORDER BY full_name ASC").fetchall()
    locations = db.execute("SELECT * FROM settings_locations WHERE is_active = 1 ORDER BY name ASC").fetchall()
    email_groups = db.execute("SELECT * FROM email_groups ORDER BY name ASC").fetchall()

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
    db.execute("UPDATE items SET status = 'EM_FACILITIES', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (item_id,))
    db.execute("INSERT INTO movements (item_id, user_id, action) VALUES (?, ?, ?)", (item_id, session['user_id'], 'COLLECT_FROM_PORTARIA'))
    db.commit()
    flash('Item coletado com sucesso.', 'success')
    return redirect(url_for('facilities.dashboard'))

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
    db.execute(
        "UPDATE items SET status = 'DISPONIVEL_PARA_RETIRADA', location = ?, recipient_email = ?, recipient_name_manual = ?, recipient_floor = ?, observation = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", 
        (location, rec_email, rec_manual, rec_floor, observation, item_id)
    )
    db.execute("INSERT INTO movements (item_id, user_id, action) VALUES (?, ?, ?)", (item_id, session['user_id'], f'ALLOCATED: {location} AND ID_RECIPIENT'))
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
        
    return redirect(url_for('facilities.dashboard'))

@facilities_bp.route('/facilities/update_location/<int:item_id>', methods=['POST'])
@login_required
@role_required(['FACILITIES', 'ADMIN', 'FACILITIES_PORTARIA'])
def update_location(item_id):
    location = request.form['location']
    db = get_db()
    db.execute("UPDATE items SET location = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (location, item_id))
    db.execute("INSERT INTO movements (item_id, user_id, action) VALUES (?, ?, ?)", (item_id, session['user_id'], f'LOCATION_CHANGED_TO: {location}'))
    db.commit()
    flash('Local atualizado com sucesso.', 'success')
    return redirect(url_for('facilities.dashboard'))

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
    
    db.execute("UPDATE items SET status = 'ENTREGUE', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (item_id,))
    
    placeholder_sig = "DATA:AUTHENTICATED_BY_PASSWORD"
    db.execute(
        "INSERT INTO proofs (item_id, signature_data, delivered_by, received_by_name) VALUES (?, ?, ?, ?)",
        (item_id, placeholder_sig, session['user_id'], user['full_name'])
    )
    
    db.execute("INSERT INTO movements (item_id, user_id, action) VALUES (?, ?, ?)", (item_id, session['user_id'], 'DELIVERED_VIA_PASSWORD'))
    db.commit()
    
    flash(f'Item entregue com sucesso para {user["full_name"]} via autenticação!', 'success')
    return redirect(url_for('facilities.dashboard'))

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
    db.execute("UPDATE items SET status = 'ENTREGUE', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (item_id,))
    
    db.execute(
        "INSERT INTO proofs (item_id, signature_data, delivered_by, received_by_name) VALUES (?, ?, ?, ?)",
        (item_id, signature, session['user_id'], received_by)
    )
    
    db.execute("INSERT INTO movements (item_id, user_id, action) VALUES (?, ?, ?)", (item_id, session['user_id'], 'DELIVERED'))
    db.commit()
    
    flash(f'Item entregue com sucesso para {received_by}!', 'success')
    return redirect(url_for('facilities.dashboard'))
