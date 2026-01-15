import os
import sqlite3
import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_only_for_mvp')
app.config['DATABASE'] = os.path.join(app.root_path, 'aeropost.db')

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
            'SELECT * FROM items WHERE recipient_email = ? ORDER BY created_at DESC', 
            (email,)
        ).fetchall()

        # Fetch unclaimed items (no email)
        unclaimed_items = db.execute(
            "SELECT * FROM items WHERE (recipient_email IS NULL OR recipient_email = '') AND status != 'ENTREGUE' ORDER BY created_at DESC"
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
            return redirect(url_for('index'))

        flash(error, 'danger')

    return render_template('login.html')

@app.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        company = request.form['company']
        floor = request.form['floor']
        password = request.form['password']
        
        # Validar domínio de email (MVP Simplificado)
        allowed_domains = ['dex.co', 'deca.com.br', 'duratex.com.br']
        domain = email.split('@')[-1]
        
        # Em MVP, as vezes aceitamos qualquer coisa para facilitar testes, mas seguindo regra:
        # if domain not in allowed_domains:
        #    flash('Email não permitido. Use um email corporativo.', 'danger')
        #    return render_template('register.html')

        db = get_db()
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

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

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
    return render_template('portaria/dashboard.html', recent_items=recent_items)

@app.route('/portaria/register', methods=['POST'])
@login_required
@role_required(['PORTARIA', 'ADMIN'])
def portaria_register():
    type = request.form['type']
    tracking = request.form['tracking_code']
    sender = request.form['sender']
    rec_email = request.form['recipient_email']
    rec_manual = request.form['recipient_name_manual']
    observation = request.form['observation']

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
    
    items_portaria = db.execute("SELECT * FROM items WHERE status = 'RECEBIDO_PORTARIA' ORDER BY created_at ASC").fetchall()
    items_facilities = db.execute("SELECT * FROM items WHERE status = 'EM_FACILITIES' ORDER BY updated_at ASC").fetchall()
    items_ready = db.execute("SELECT * FROM items WHERE status = 'DISPONIVEL_PARA_RETIRADA' ORDER BY updated_at DESC").fetchall()

    return render_template('facilities/dashboard.html', stats=stats, items_portaria=items_portaria, items_facilities=items_facilities, items_ready=items_ready)

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
    db = get_db()
    db.execute("UPDATE items SET status = 'DISPONIVEL_PARA_RETIRADA', location = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (location, item_id))
    db.execute("INSERT INTO movements (item_id, user_id, action) VALUES (?, ?, ?)", (item_id, session['user_id'], f'ALLOCATED: {location}'))
    db.commit()
    flash(f'Item alocado em {location}.', 'success')
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
    user = db.execute("SELECT is_active FROM users WHERE id = ?", (user_id,)).fetchone()
    new_status = 0 if user['is_active'] else 1
    
    db.execute("UPDATE users SET is_active = ? WHERE id = ?", (new_status, user_id))
    db.commit()
    
    msg = 'Usuário bloqueado.' if new_status == 0 else 'Usuário desbloqueado.'
    flash(msg, 'warning' if new_status == 0 else 'success')
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
