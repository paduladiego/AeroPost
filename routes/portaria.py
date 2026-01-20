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
    recent_items = db.execute(
        'SELECT * FROM items WHERE status = "RECEBIDO_PORTARIA" OR created_at >= date("now", "localtime") ORDER BY status = "RECEBIDO_PORTARIA" DESC, created_at DESC'
    ).fetchall()
    
    item_types = db.execute("SELECT * FROM settings_item_types WHERE is_active = 1").fetchall()
    
    return render_template('portaria/dashboard.html', recent_items=recent_items, item_types=item_types)

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
    db.execute(
        'INSERT INTO items (internal_id, tracking_code, type, sender, status) VALUES (?, ?, ?, ?, ?)',
        (internal_id, tracking, type, sender, 'RECEBIDO_PORTARIA')
    )
    
    item_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
    db.execute(
        'INSERT INTO movements (item_id, user_id, action) VALUES (?, ?, ?)',
        (item_id, session['user_id'], 'REGISTER_PORTARIA')
    )
    db.commit()

    flash(f'Item {internal_id} registrado com sucesso!', 'success')
    return redirect(url_for('portaria.dashboard'))
