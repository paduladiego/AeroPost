from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from utils.db import get_db
from utils.auth import login_required, role_required
from utils.notifications import send_support_ticket

main_bp = Blueprint('main', __name__)

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
        
        my_items = db.execute(
            'SELECT * FROM items WHERE recipient_email = ? OR recipient_name_manual = ? ORDER BY created_at DESC', 
            (email, email)
        ).fetchall()

        unclaimed_items = db.execute(
            "SELECT * FROM items WHERE (recipient_email IS NULL OR recipient_email = '') "
            "AND (recipient_name_manual NOT LIKE '%@%' OR recipient_name_manual IS NULL) "
            "AND status != 'ENTREGUE' ORDER BY created_at DESC"
        ).fetchall()
        
        return render_template('home_user.html', items=my_items, unclaimed_items=unclaimed_items)

@main_bp.route('/home')
@login_required
def home_user():
    db = get_db()
    user = db.execute('SELECT email FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    email = user['email']
    
    my_items = db.execute(
        'SELECT * FROM items WHERE recipient_email = ? OR recipient_name_manual = ? ORDER BY created_at DESC', 
        (email, email)
    ).fetchall()

    unclaimed_items = db.execute(
        "SELECT * FROM items WHERE (recipient_email IS NULL OR recipient_email = '') "
        "AND (recipient_name_manual NOT LIKE '%@%' OR recipient_name_manual IS NULL) "
        "AND status != 'ENTREGUE' ORDER BY created_at DESC"
    ).fetchall()
    
    return render_template('home_user.html', items=my_items, unclaimed_items=unclaimed_items)

@main_bp.route('/history')
@login_required
@role_required(['ADMIN', 'FACILITIES', 'FACILITIES_PORTARIA'])
def history():
    db = get_db()
    
    query = """
        SELECT i.*, p.signature_data, p.received_by_name, p.delivered_at, u.full_name as deliverer_name
        FROM items i
        JOIN proofs p ON i.id = p.item_id
        JOIN users u ON p.delivered_by = u.id
        WHERE i.status = 'ENTREGUE'
    """
    params = []
    
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
