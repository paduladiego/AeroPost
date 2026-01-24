import datetime
import random
import string
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from utils.db import get_db
from utils.auth import login_required, role_required

portaria_bp = Blueprint('portaria', __name__)

@portaria_bp.route('/portaria')
@login_required
@role_required(['PORTARIA', 'ADMIN', 'FACILITIES_PORTARIA'])
def dashboard():
    db = get_db()
    user_role = session.get('role')
    user_id = session.get('user_id')
    
    # Busca a unidade padrão do usuário para validação
    user_data = db.execute("SELECT default_unit_id FROM users WHERE id = ?", (user_id,)).fetchone()
    default_unit = user_data['default_unit_id'] if user_data else None

    # Se for APENAS portaria, força a visualização da sua unidade padrão
    if user_role == 'PORTARIA':
        if session.get('unit_id') != default_unit:
            session['unit_id'] = default_unit
        unit_id = default_unit
    else:
        unit_id = session.get('unit_id')

    today_date = datetime.date.today().strftime('%Y-%m-%d')

    # Itens recebidos hoje (considerando que o banco já armazena em horário local)
    today_items = db.execute(
        'SELECT * FROM items WHERE date(created_at) = ? '
        'AND unit_id = ? '
        'ORDER BY created_at DESC',
        (today_date, unit_id)
    ).fetchall()
    
    # Itens pendentes de dias anteriores
    pending_items = db.execute(
        'SELECT * FROM items WHERE status = "RECEBIDO_PORTARIA" '
        'AND date(created_at) < ? '
        'AND unit_id = ? '
        'ORDER BY created_at ASC',
        (today_date, unit_id)
    ).fetchall()
    
    item_types = db.execute("SELECT * FROM settings_item_types WHERE is_active = 1").fetchall()
    
    return render_template('portaria/dashboard.html', 
                           today_items=today_items, 
                           pending_items=pending_items, 
                           item_types=item_types,
                           today_date=today_date)

@portaria_bp.route('/portaria/register', methods=['POST'])
@login_required
@role_required(['PORTARIA', 'ADMIN', 'FACILITIES_PORTARIA'])
def register():
    type = request.form['type']
    tracking = request.form.get('tracking_code', '')
    sender = request.form['sender']
    
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    today = datetime.datetime.now().strftime('%Y%m%d')
    internal_id = f"AP-{today}-{suffix}"

    db = get_db()
    user_role = session.get('role')
    user_id = session.get('user_id')
    
    # Validação de Unidade para usuários de Portaria
    if user_role == 'PORTARIA':
        user_data = db.execute("SELECT default_unit_id FROM users WHERE id = ?", (user_id,)).fetchone()
        unit_id = user_data['default_unit_id'] if user_data else session.get('unit_id')
    else:
        unit_id = session.get('unit_id')

    db.execute(
        'INSERT INTO items (internal_id, tracking_code, type, sender, status, unit_id) VALUES (?, ?, ?, ?, ?, ?)',
        (internal_id, tracking, type, sender, 'RECEBIDO_PORTARIA', unit_id)
    )
    
    item_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
    db.execute(
        'INSERT INTO movements (item_id, user_id, action, unit_id) VALUES (?, ?, ?, ?)',
        (item_id, user_id, 'REGISTER_PORTARIA', unit_id)
    )
    db.commit()

    flash(f'Item {internal_id} registrado com sucesso!', 'success')
    return redirect(url_for('portaria.dashboard'))
