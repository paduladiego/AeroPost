import os
import sqlite3
import datetime
import csv
import io
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, g, make_response
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_only_for_mvp')
app.config['DATABASE'] = os.path.join(app.root_path, 'aeropost.db')

# Middleware para lidar com subdiretórios (necessário para /Dexco/AeroPost)
class PrefixMiddleware(object):
    def __init__(self, app, prefix=''):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        if environ.get('HTTP_X_FORWARDED_PREFIX'):
            environ['SCRIPT_NAME'] = environ['HTTP_X_FORWARDED_PREFIX']
            path_info = environ.get('PATH_INFO', '')
            if path_info.startswith(environ['SCRIPT_NAME']):
                environ['PATH_INFO'] = path_info[len(environ['SCRIPT_NAME']):]
        return self.app(environ, start_response)

app.wsgi_app = PrefixMiddleware(app.wsgi_app)


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()
    print("Initialized the database.")

@app.cli.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()

@app.before_request
def enforce_password_change():
    if 'user_id' in session and session.get('must_change_password'):
        if request.endpoint not in ('change_password', 'logout', 'static'):
            return redirect(url_for('change_password'))

# --- Auth Decorators ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session or session['role'] not in roles:
                flash('Acesso negado para seu perfil.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- Routes ---
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    role = session.get('role')
    if role == 'PORTARIA':
        return redirect(url_for('portaria_dashboard'))
    elif role == 'FACILITIES' or role == 'ADMIN':
        return redirect(url_for('facilities_dashboard'))
    else:
        # User Dashboard logic
        db = get_db()
        # Get user email
        user = db.execute('SELECT email FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        email = user['email']
        
        # Fetch my items
        my_items = db.execute(
            'SELECT * FROM items WHERE recipient_email = ? OR recipient_name_manual = ? ORDER BY created_at DESC', 
            (email, email)
        ).fetchall()

        # Fetch unclaimed items (no email and no manual email identification)
        unclaimed_items = db.execute(
            "SELECT * FROM items WHERE (recipient_email IS NULL OR recipient_email = '') "
            "AND (recipient_name_manual NOT LIKE '%@%' OR recipient_name_manual IS NULL) "
            "AND status != 'ENTREGUE' ORDER BY created_at DESC"
        ).fetchall()
        
        return render_template('home_user.html', items=my_items, unclaimed_items=unclaimed_items)

@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        login_input = request.form['login'] # email or username
        password = request.form['password']
        db = get_db()
        error = None
        
        # Try finding by email or username
        user = db.execute(
            'SELECT * FROM users WHERE email = ? OR username = ?', (login_input, login_input)
        ).fetchone()

        if user is None:
            error = 'Usuário incorreto.'
        elif not check_password_hash(user['password_hash'], password):
            error = 'Senha incorreta.'
        elif user['is_active'] == 0:
            error = 'Usuário bloqueado. Contate o administrador.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['name'] = user['full_name']
            
            # Check for forced password change (safely handle if column missing during migration transition)
            try:
                if user['must_change_password'] == 1:
                    session['must_change_password'] = True
                    flash('Por favor, redefina sua senha para continuar.', 'warning')
                    return redirect(url_for('change_password'))
            except IndexError:
                # Column might not exist yet if migration failed
                pass

            return redirect(url_for('index'))

        flash(error, 'danger')

    return render_template('login.html')

@app.route('/register', methods=('GET', 'POST'))
def register():
    db = get_db()
    companies = db.execute("SELECT * FROM settings_companies WHERE is_active = 1").fetchall()

    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        company = request.form['company']
        floor = request.form['floor']
        password = request.form['password']
        
        # Validate domain dynamic
        allowed_domains_rows = db.execute("SELECT domain FROM settings_allowed_domains WHERE is_active = 1").fetchall()
        allowed_domains = [row['domain'] for row in allowed_domains_rows]
        
        # Check if email ends with any allowed domain
        domain_valid = False
        if not allowed_domains:
            domain_valid = True # If no domains configured, allow all (MVP)
        else:
            for d in allowed_domains:
                if email.endswith(d):
                    domain_valid = True
                    break
        
        if not domain_valid:
           flash(f'Email não permitido. Domínios aceitos: {", ".join(allowed_domains)}', 'danger')
           return render_template('register.html', companies=companies)

        error = None

        if db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone() is not None:
            error = 'Email já cadastrado.'

        if error is None:
            db.execute(
                'INSERT INTO users (email, password_hash, role, full_name, floor, company) VALUES (?, ?, ?, ?, ?, ?)',
                (email, generate_password_hash(password), 'USER', full_name, floor, company)
            )
            db.commit()
            flash('Cadastro realizado! Faça login.', 'success')
            return redirect(url_for('login'))

        flash(error, 'danger')

    return render_template('register.html', companies=companies)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('As senhas não coincidem.', 'danger')
            return render_template('change_password.html')
            
        if len(password) < 6:
            flash('A senha deve ter no mínimo 6 caracteres.', 'danger')
            return render_template('change_password.html')

        db = get_db()
        db.execute(
            'UPDATE users SET password_hash = ?, must_change_password = 0 WHERE id = ?',
            (generate_password_hash(password), session['user_id'])
        )
        db.commit()
        
        # Clear the flag in session
        session.pop('must_change_password', None)
        
        flash('Senha alterada com sucesso!', 'success')
        return redirect(url_for('index'))
        
    return render_template('change_password.html')

# --- Placeholders for core dashboards ---
# --- Core Core Routes ---
@app.route('/portaria')
@login_required
@role_required(['PORTARIA', 'ADMIN'])
def portaria_dashboard():
    db = get_db()
    # Get items registered today
    recent_items = db.execute(
        'SELECT * FROM items WHERE created_at >= date("now", "localtime") ORDER BY created_at DESC'
    ).fetchall()
    
    # Get Item Types
    item_types = db.execute("SELECT * FROM settings_item_types WHERE is_active = 1").fetchall()
    
    return render_template('portaria/dashboard.html', recent_items=recent_items, item_types=item_types)

@app.route('/portaria/register', methods=['POST'])
@login_required
@role_required(['PORTARIA', 'ADMIN'])
def portaria_register():
    type = request.form['type']
    tracking = request.form.get('tracking_code', '')
    sender = request.form['sender']
    
    # Recipient identification moved to Facilities V1.1
    rec_email = None
    rec_manual = None
    observation = None

    # Generate internal ID: AP-YYYYMMDD-XXXX (Random 4 chars for simplicity or sequential)
    import random, string
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    today = datetime.datetime.now().strftime('%Y%m%d')
    internal_id = f"AP-{today}-{suffix}"

    db = get_db()
    db.execute(
        'INSERT INTO items (internal_id, tracking_code, type, sender, recipient_email, recipient_name_manual, observation, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        (internal_id, tracking, type, sender, rec_email, rec_manual, observation, 'RECEBIDO_PORTARIA')
    )
    
    # Log movement
    item_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
    db.execute(
        'INSERT INTO movements (item_id, user_id, action) VALUES (?, ?, ?)',
        (item_id, session['user_id'], 'REGISTER_PORTARIA')
    )
    db.commit()

    flash(f'Item {internal_id} registrado com sucesso!', 'success')
    return redirect(url_for('portaria_dashboard'))

@app.route('/facilities')
@login_required
@role_required(['FACILITIES', 'ADMIN'])
def facilities_dashboard():
    db = get_db()
    # Stats
    stats = {
        'in_portaria': db.execute("SELECT COUNT(*) FROM items WHERE status = 'RECEBIDO_PORTARIA'").fetchone()[0],
        'in_facilities': db.execute("SELECT COUNT(*) FROM items WHERE status = 'EM_FACILITIES'").fetchone()[0],
        'ready': db.execute("SELECT COUNT(*) FROM items WHERE status = 'DISPONIVEL_PARA_RETIRADA'").fetchone()[0]
    }
    
    query_base = """
        SELECT i.*, u.floor as user_floor, u.company as user_company 
        FROM items i 
        LEFT JOIN users u ON i.recipient_email = u.email
    """
    
    items_portaria = db.execute(query_base + " WHERE i.status = 'RECEBIDO_PORTARIA' ORDER BY i.created_at ASC").fetchall()
    items_facilities = db.execute(query_base + " WHERE i.status = 'EM_FACILITIES' ORDER BY i.updated_at ASC").fetchall()
    items_ready = db.execute(query_base + " WHERE i.status = 'DISPONIVEL_PARA_RETIRADA' ORDER BY i.updated_at DESC").fetchall()

    # Fetch all active users (except Admins) for selection in v1.1
    corp_users = db.execute("SELECT email, full_name FROM users WHERE is_active = 1 AND role != 'ADMIN' ORDER BY full_name ASC").fetchall()

    # Fetch locations
    locations = db.execute("SELECT * FROM settings_locations WHERE is_active = 1").fetchall()

    return render_template('facilities/dashboard.html', 
                           stats=stats, 
                           items_portaria=items_portaria, 
                           items_facilities=items_facilities, 
                           items_ready=items_ready, 
                           corp_users=corp_users,
                           locations=locations)

@app.route('/facilities/collect/<int:item_id>', methods=['POST'])
@login_required
@role_required(['FACILITIES', 'ADMIN'])
def facilities_collect(item_id):
    db = get_db()
    db.execute("UPDATE items SET status = 'EM_FACILITIES', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (item_id,))
    db.execute("INSERT INTO movements (item_id, user_id, action) VALUES (?, ?, ?)", (item_id, session['user_id'], 'COLLECT_FROM_PORTARIA'))
    db.commit()
    flash('Item coletado com sucesso.', 'success')
    return redirect(url_for('facilities_dashboard'))

@app.route('/facilities/allocate/<int:item_id>', methods=['POST'])
@login_required
@role_required(['FACILITIES', 'ADMIN'])
def facilities_allocate(item_id):
    location = request.form['location']
    rec_email = request.form.get('recipient_email')
    rec_manual = request.form.get('recipient_name_manual')
    rec_floor = request.form.get('recipient_floor')

    # Auto-detect email in manual field if selection is empty
    if not rec_email and rec_manual and '@' in rec_manual:
        rec_email = rec_manual
    
    db = get_db()
    db.execute(
        "UPDATE items SET status = 'DISPONIVEL_PARA_RETIRADA', location = ?, recipient_email = ?, recipient_name_manual = ?, recipient_floor = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", 
        (location, rec_email, rec_manual, rec_floor, item_id)
    )
    db.execute("INSERT INTO movements (item_id, user_id, action) VALUES (?, ?, ?)", (item_id, session['user_id'], f'ALLOCATED: {location} AND ID_RECIPIENT'))
    db.commit()
    flash(f'Item alocado em {location} para {rec_email or rec_manual}.', 'success')
    return redirect(url_for('facilities_dashboard'))

@app.route('/delivery/password/<int:item_id>')
@login_required
@role_required(['FACILITIES', 'ADMIN'])
def delivery_password_page(item_id):
    db = get_db()
    item = db.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    
    # Logic to handle items with email in the manual field
    display_email = item['recipient_email']
    if not display_email and item['recipient_name_manual'] and '@' in item['recipient_name_manual']:
        display_email = item['recipient_name_manual']

    if not display_email:
        flash('Este item não possui um destinatário cadastrado para validar via senha.', 'danger')
        return redirect(url_for('facilities_dashboard'))
        
    return render_template('delivery_password.html', item=item, display_email=display_email)

@app.route('/delivery/confirm_password/<int:item_id>', methods=['POST'])
@login_required
@role_required(['FACILITIES', 'ADMIN'])
def delivery_password_confirm(item_id):
    email = request.form['email']
    password = request.form['password']
    
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    
    if user is None or not check_password_hash(user['password_hash'], password):
        flash('Senha incorreta para o destinatário informado.', 'danger')
        return redirect(url_for('delivery_password_page', item_id=item_id))
    
    # Update status
    db.execute("UPDATE items SET status = 'ENTREGUE', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (item_id,))
    
    # Save proof (Using a placeholder for signature)
    placeholder_sig = "DATA:AUTHENTICATED_BY_PASSWORD"
    db.execute(
        "INSERT INTO proofs (item_id, signature_data, delivered_by, received_by_name) VALUES (?, ?, ?, ?)",
        (item_id, placeholder_sig, session['user_id'], user['full_name'])
    )
    
    # Log movement
    db.execute("INSERT INTO movements (item_id, user_id, action) VALUES (?, ?, ?)", (item_id, session['user_id'], 'DELIVERED_VIA_PASSWORD'))
    db.commit()
    
    flash(f'Item entregue com sucesso para {user["full_name"]} via autenticação!', 'success')
    return redirect(url_for('facilities_dashboard'))

@app.route('/delivery/<int:item_id>')
@login_required
@role_required(['FACILITIES', 'ADMIN'])
def delivery_page(item_id):
    db = get_db()
    item = db.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    return render_template('delivery.html', item=item)

@app.route('/delivery/confirm/<int:item_id>', methods=['POST'])
@login_required
@role_required(['FACILITIES', 'ADMIN'])
def delivery_confirm(item_id):
    received_by = request.form['received_by_name']
    signature = request.form['signature_data']
    
    db = get_db()
    # Update status
    db.execute("UPDATE items SET status = 'ENTREGUE', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (item_id,))
    
    # Save proof
    db.execute(
        "INSERT INTO proofs (item_id, signature_data, delivered_by, received_by_name) VALUES (?, ?, ?, ?)",
        (item_id, signature, session['user_id'], received_by)
    )
    
    # Log movement
    db.execute("INSERT INTO movements (item_id, user_id, action) VALUES (?, ?, ?)", (item_id, session['user_id'], 'DELIVERED'))
    db.commit()
    
    flash(f'Item entregue com sucesso para {received_by}!', 'success')
    return redirect(url_for('facilities_dashboard'))

# --- Settings Routes ---
@app.route('/settings')
@login_required
@role_required(['ADMIN', 'FACILITIES'])
def settings_dashboard():
    db = get_db()
    
    # Fetch all data
    item_types = db.execute("SELECT * FROM settings_item_types WHERE is_active = 1").fetchall()
    locations = db.execute("SELECT * FROM settings_locations WHERE is_active = 1").fetchall()
    companies = db.execute("SELECT * FROM settings_companies WHERE is_active = 1").fetchall()
    domains = []
    
    if session['role'] == 'ADMIN':
        domains = db.execute("SELECT * FROM settings_allowed_domains WHERE is_active = 1").fetchall()
        
    return render_template('settings.html', 
                            item_types=item_types, 
                            locations=locations, 
                            companies=companies, 
                            domains=domains)

@app.route('/settings/add/<category>', methods=['POST'])
@login_required
@role_required(['ADMIN', 'FACILITIES'])
def settings_add(category):
    name = request.form['name'].strip()
    db = get_db()
    
    try:
        if category == 'type':
            db.execute("INSERT INTO settings_item_types (name) VALUES (?)", (name,))
        elif category == 'location':
            db.execute("INSERT INTO settings_locations (name) VALUES (?)", (name,))
        elif category == 'company':
            db.execute("INSERT INTO settings_companies (name) VALUES (?)", (name,))
        elif category == 'domain' and session['role'] == 'ADMIN':
            if not name.startswith('@'):
                flash('Domínio deve começar com @', 'warning')
                return redirect(url_for('settings_dashboard'))
            db.execute("INSERT INTO settings_allowed_domains (domain) VALUES (?)", (name,))
        else:
            flash('Ação não permitida ou categoria inválida.', 'danger')
            return redirect(url_for('settings_dashboard'))
            
        db.commit()
        flash('Item adicionado com sucesso.', 'success')
    except sqlite3.IntegrityError:
        flash('Erro: Item já existe.', 'danger')
        
    return redirect(url_for('settings_dashboard'))

@app.route('/settings/delete/<category>/<int:item_id>', methods=['POST'])
@login_required
@role_required(['ADMIN', 'FACILITIES'])
def settings_delete(category, item_id):
    db = get_db()
    
    # Soft delete (make inactive) or Hard delete? Assuming Hard delete for simplicity as per requirement "remove"
    # But schema script has is_active, let's use that for safety or just DELETE
    # "is_active DEFAULT 1" suggests we might want soft delete, but user said "remove". 
    # Let's do DELETE for now to keep lists clean, or use is_active=0 if we want to keep history.
    # Given MVP, let's DELETE for clean UI.
    
    query = ""
    if category == 'type':
        query = "DELETE FROM settings_item_types WHERE id = ?"
    elif category == 'location':
        query = "DELETE FROM settings_locations WHERE id = ?"
    elif category == 'company':
        query = "DELETE FROM settings_companies WHERE id = ?"
    elif category == 'domain' and session['role'] == 'ADMIN':
        query = "DELETE FROM settings_allowed_domains WHERE id = ?"
    else:
        # Invalid access
        return redirect(url_for('settings_dashboard'))

    db.execute(query, (item_id,))
    db.commit()
    flash('Item removido.', 'success')
    return redirect(url_for('settings_dashboard'))

@app.route('/history/export')
@login_required
@role_required(['ADMIN', 'FACILITIES'])
def history_export():
    db = get_db()
    
    query = """
        SELECT i.internal_id, i.tracking_code, i.type, i.sender, i.recipient_email, i.recipient_name_manual, 
               i.location, p.received_by_name, u.full_name as deliverer_name, p.delivered_at
        FROM items i
        LEFT JOIN proofs p ON i.id = p.item_id
        LEFT JOIN users u ON p.delivered_by = u.id
        WHERE i.status = 'ENTREGUE'
        ORDER BY p.delivered_at DESC
    """
    
    items = db.execute(query).fetchall()
    
    si = io.StringIO()
    cw = csv.writer(si, delimiter=';') 
    
    cw.writerow(['ID Interno', 'Código Rastreio', 'Tipo', 'Remetente', 'Destinatário (Email)', 'Destinatário (Manual)', 'Local Armazenado', 'Recebido Por', 'Entregue Por', 'Data Entrega'])
    
    for item in items:
        cw.writerow([
            item['internal_id'],
            item['tracking_code'] or '',
            item['type'],
            item['sender'],
            item['recipient_email'] or '',
            item['recipient_name_manual'] or '',
            item['location'] or '',
            item['received_by_name'],
            item['deliverer_name'],
            item['delivered_at'].strftime('%d/%m/%Y %H:%M:%S') if item['delivered_at'] else ''
        ])
        
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=relatorio_entregas.csv"
    output.headers["Content-type"] = "text/csv"
    return output

# --- User Management Routes ---
@app.route('/users')
@login_required
@role_required(['ADMIN', 'FACILITIES'])
def users_list():
    db = get_db()
    users = db.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
    return render_template('users.html', users=users)

@app.route('/users/create_portaria', methods=['POST'])
@login_required
@role_required(['ADMIN', 'FACILITIES'])
def user_create_portaria():
    full_name = request.form['full_name']
    username = request.form['username']
    password = request.form['password']
    
    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (username, role, full_name, password_hash) VALUES (?, ?, ?, ?)",
            (username, 'PORTARIA', full_name, generate_password_hash(password))
        )
        db.commit()
        flash(f'Usuário de Portaria {username} criado.', 'success')
    except sqlite3.IntegrityError:
        flash(f'Erro: Usuário {username} já existe.', 'danger')
        
    return redirect(url_for('users_list'))

@app.route('/users/promote/<int:user_id>', methods=['POST'])
@login_required
@role_required(['ADMIN', 'FACILITIES'])
def user_promote(user_id):
    db = get_db()
    target = db.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
    
    # Security: FACILITES cannot promote ADMINs or other STAFF to level higher than them (not applicable here but good to check)
    if target['role'] == 'ADMIN' and session['role'] != 'ADMIN':
        flash('Erro: Você não tem permissão para gerenciar Administradores.', 'danger')
        return redirect(url_for('users_list'))
        
    db.execute("UPDATE users SET role = 'FACILITIES' WHERE id = ?", (user_id,))
    db.commit()
    flash('Usuário promovido para FACILITIES.', 'success')
    return redirect(url_for('users_list'))

@app.route('/history')
@login_required
@role_required(['ADMIN', 'FACILITIES'])
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
    
    # Filters
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

@app.route('/users/demote/<int:user_id>', methods=['POST'])
@login_required
@role_required(['ADMIN', 'FACILITIES'])
def user_demote(user_id):
    db = get_db()
    target = db.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()

    # Security: Only ADMIN can demote and ADMIN (and FACILITIES cannot demote other STAFF)
    if target['role'] == 'ADMIN' and session['role'] != 'ADMIN':
        flash('Erro: Você não tem permissão para gerenciar Administradores.', 'danger')
        return redirect(url_for('users_list'))

    # Demote to USER by default
    db.execute("UPDATE users SET role = 'USER' WHERE id = ?", (user_id,))
    db.commit()
    flash('Usuário rebaixado para USER.', 'success')
    return redirect(url_for('users_list'))

@app.route('/users/toggle_block/<int:user_id>', methods=['POST'])
@login_required
@role_required(['ADMIN', 'FACILITIES'])
def user_toggle_block(user_id):
    db = get_db()
    user = db.execute("SELECT role, is_active FROM users WHERE id = ?", (user_id,)).fetchone()
    
    # Security: Only ADMIN can block another ADMIN
    if user['role'] == 'ADMIN' and session['role'] != 'ADMIN':
        flash('Erro: Você não tem permissão para bloquear um Administrador.', 'danger')
        return redirect(url_for('users_list'))

    new_status = 0 if user['is_active'] else 1
    
    db.execute("UPDATE users SET is_active = ? WHERE id = ?", (new_status, user_id))
    db.commit()
    
    msg = 'Usuário bloqueado.' if new_status == 0 else 'Usuário desbloqueado.'
    flash(msg, 'warning' if new_status == 0 else 'success')
    return redirect(url_for('users_list'))

@app.route('/users/reset_password/<int:user_id>', methods=['POST'])
@login_required
@role_required(['ADMIN', 'FACILITIES'])
def user_reset_password(user_id):
    db = get_db()
    target = db.execute("SELECT role, full_name, email FROM users WHERE id = ?", (user_id,)).fetchone()
    
    # Security: Only ADMIN can reset ADMIN
    if target['role'] == 'ADMIN' and session['role'] != 'ADMIN':
        flash('Erro: Você não tem permissão para gerenciar Administradores.', 'danger')
        return redirect(url_for('users_list'))

    default_password = 'mudar123'
    db.execute(
        "UPDATE users SET password_hash = ?, must_change_password = 1 WHERE id = ?", 
        (generate_password_hash(default_password), user_id)
    )
    db.commit()
    
    flash(f'Senha de {target["full_name"]} resetada para "{default_password}". O usuário deverá trocá-la no próximo login.', 'success')
    return redirect(url_for('users_list'))

# --- Admin Setup Script (For MVP simplicity) ---
@app.cli.command('create-admin')
def create_admin():
    """Creates a default admin user."""
    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (username, role, full_name, password_hash) VALUES (?, ?, ?, ?)",
            ('admin', 'ADMIN', 'Administrador', generate_password_hash('admin123'))
        )
        db.commit()
        print("Admin user created: admin / admin123")
    except sqlite3.IntegrityError:
        print("Admin user already exists.")

if __name__ == '__main__':
    app.run(debug=True)
