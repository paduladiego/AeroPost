from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from utils.db import get_db
from utils.auth import login_required, role_required
from utils.notifications import send_support_ticket

main_bp = Blueprint('main', __name__)

# Mapeamento de ações para nomes amigáveis no histórico
ITEM_ACTION_MAP = {
    'REGISTER_PORTARIA': '📦 Recebido na Portaria',
    'COLLECT_FROM_PORTARIA': '🚚 Coletado pelo Facilities',
    'DELIVERED': '✅ Entregue ao Destinatário',
    'DELIVERED_VIA_PASSWORD': '🔑 Entregue via Autenticação por Senha',
    'RECOVERED_ITEM': '♻️ Item Recuperado',
    'RECORDED_OCCURRENCE: EXTRAVIADO': '⚠️ Registrada Ocorrência: EXTRAVIADO',
    'RECORDED_OCCURRENCE: DEVOLVIDO': '⚠️ Registrada Ocorrência: DEVOLVIDO'
}

@main_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    role = session.get('role')
    if role == 'PORTARIA':
        return redirect(url_for('portaria.dashboard'))
    elif role in ('FACILITIES', 'ADMIN', 'FACILITIES_PORTARIA'):
        return redirect(url_for('facilities.dashboard'))
    else:
        db = get_db()
        user = db.execute('SELECT email FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        email = user['email']
        
        unit_id = session.get('unit_id')
        my_items = db.execute(
            'SELECT * FROM items WHERE (recipient_email = ? OR recipient_name_manual = ?) AND unit_id = ? ORDER BY created_at DESC', 
            (email, email, unit_id)
        ).fetchall()

        unclaimed_items = db.execute(
            "SELECT * FROM items WHERE (recipient_email IS NULL OR recipient_email = '') "
            "AND (recipient_name_manual NOT LIKE '%@%' OR recipient_name_manual IS NULL) "
            "AND status != 'ENTREGUE' AND unit_id = ? ORDER BY created_at DESC",
            (unit_id,)
        ).fetchall()
        
        return render_template('home_user.html', items=my_items, unclaimed_items=unclaimed_items)

@main_bp.route('/home')
@login_required
def home_user():
    db = get_db()
    user = db.execute('SELECT email FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    email = user['email']
    
    unit_id = session.get('unit_id')
    my_items = db.execute(
        'SELECT * FROM items WHERE (recipient_email = ? OR recipient_name_manual = ?) AND unit_id = ? ORDER BY created_at DESC', 
        (email, email, unit_id)
    ).fetchall()

    unclaimed_items = db.execute(
        "SELECT * FROM items WHERE (recipient_email IS NULL OR recipient_email = '') "
        "AND (recipient_name_manual NOT LIKE '%@%' OR recipient_name_manual IS NULL) "
        "AND status != 'ENTREGUE' AND unit_id = ? ORDER BY created_at DESC",
        (unit_id,)
    ).fetchall()
    
    return render_template('home_user.html', items=my_items, unclaimed_items=unclaimed_items)

@main_bp.route('/history')
@login_required
@role_required(['ADMIN', 'FACILITIES', 'FACILITIES_PORTARIA'])
def history():
    db = get_db()
    
    unit_id = session.get('unit_id')
    query = """
        SELECT i.*, p.signature_data, p.received_by_name, p.delivered_at, u.full_name as deliverer_name, p.occurrence_note
        FROM items i
        JOIN proofs p ON i.id = p.item_id
        JOIN users u ON p.delivered_by = u.id
        WHERE i.status IN ('ENTREGUE', 'EXTRAVIADO', 'DEVOLVIDO') AND i.unit_id = ?
    """
    params = [unit_id]
    
    search = request.args.get('q')
    if search:
        query += " AND (i.internal_id LIKE ? OR i.tracking_code LIKE ? OR i.sender LIKE ? OR p.received_by_name LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term, term])
        
    start_date = request.args.get('start_date')
    if start_date:
        query += " AND date(p.delivered_at) >= ?"
        params.append(start_date)
        
    end_date = request.args.get('end_date')
    if end_date:
        query += " AND date(p.delivered_at) <= ?"
        params.append(end_date)
        
    query += " ORDER BY p.delivered_at DESC"
    
    items = db.execute(query, params).fetchall()
    return render_template('history.html', items=items)

@main_bp.route('/report-problem', methods=['POST'])
@login_required
def report_problem():
    from flask import current_app
    description = request.form.get('description')
    user_name = session.get('name')
    page_url = request.referrer or "URL desconhecida"
    app_version = current_app.config.get('APP_VERSION', 'v2.1.0')
    
    db = get_db()
    user = db.execute('SELECT email FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    user_email = user['email'] if user else None
    
    if send_support_ticket(user_name, user_email, description, app_version, page_url):
        flash('Seu relato foi enviado com sucesso para o suporte! Obrigado pelo feedback.', 'success')
    else:
        flash('Houve um erro ao enviar seu relato. Por favor, tente novamente mais tarde.', 'danger')
        
    return redirect(request.referrer or url_for('main.index'))
@main_bp.route('/set_unit/<int:unit_id>')
@login_required
def set_unit(unit_id):
    db = get_db()
    # Verifica se a unidade existe e está ativa
    unit = db.execute("SELECT id FROM settings_companies WHERE id = ? AND is_active = 1", (unit_id,)).fetchone()
    if unit:
        session['unit_id'] = unit['id']
        flash(f'Unidade alterada com sucesso.', 'info')
    
    return redirect(request.referrer or url_for('main.index'))

@main_bp.route('/api/item/history/<int:item_id>')
@login_required
def get_item_history(item_id):
    db = get_db()
    # 1. Busca dados básicos do item
    item = db.execute("SELECT internal_id, status, sender, observation FROM items WHERE id = ?", (item_id,)).fetchone()
    if not item:
        return {"error": "Item não encontrado"}, 404

    # 2. Busca todas as movimentações com o nome do usuário responsável
    movements = db.execute("""
        SELECT m.timestamp, m.action, u.full_name as user_name
        FROM movements m
        JOIN users u ON m.user_id = u.id
        WHERE m.item_id = ?
        ORDER BY m.timestamp ASC
    """, (item_id,)).fetchall()
    
    # 3. Busca detalhes extras do comprovante se houver (quem recebeu de fato)
    proof = db.execute("""
        SELECT p.received_by_name, p.occurrence_note
        FROM proofs p
        WHERE p.item_id = ?
    """, (item_id,)).fetchone()
    
    history_data = []
    for m in movements:
        raw_action = m['action']
        
        # Parse delimiter da nota se houver (Audit Trail v4.3.0+)
        note_from_movement = ""
        if " | " in raw_action:
            parts = raw_action.split(" | ", 1)
            raw_action = parts[0]
            note_from_movement = parts[1]

        display_action = ITEM_ACTION_MAP.get(raw_action, raw_action)
        
        # Tratamento especial para strings dinâmicas
        if raw_action.startswith('ALLOCATED:'):
            display_action = '📍 Alocado para Retirada'
        elif raw_action.startswith('LOCATION_CHANGED_TO:'):
            display_action = '🔄 Local de Armazenamento Alterado'

        entry = {
            'timestamp': m['timestamp'],
            'action': display_action,
            'user': m['user_name'],
            'details': '-'
        }
        
        # Lógica de detalhes refinada
        if raw_action == 'REGISTER_PORTARIA':
            entry['details'] = item['sender']
        elif raw_action.startswith('ALLOCATED:'):
            # Extrai o local: "ALLOCATED: Local Name AND ID_RECIPIENT" -> "Local Name"
            local_part = raw_action.replace('ALLOCATED: ', '').split(' AND ')[0]
            obs_part = note_from_movement or item['observation'] or ""
            entry['details'] = f"{local_part} - {obs_part}" if obs_part else local_part
        elif raw_action.startswith('RECORDED_OCCURRENCE') or raw_action == 'RECOVERED_ITEM':
            # Prioriza a nota salva no movimento
            entry['details'] = note_from_movement or (proof['occurrence_note'] if proof else '-')
        elif raw_action.startswith('LOCATION_CHANGED_TO:'):
             # Extrai o novo local
             local_part = raw_action.replace('LOCATION_CHANGED_TO: ', '')
             entry['details'] = note_from_movement or local_part or '-'
        elif raw_action in ('DELIVERED', 'DELIVERED_VIA_PASSWORD'):
             entry['details'] = f"Recebido por: {proof['received_by_name']}" if proof else '-'

        history_data.append(entry)
        
    return {
        "internal_id": item['internal_id'],
        "status": item['status'],
        "history": history_data
    }, 200
