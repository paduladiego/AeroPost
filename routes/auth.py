from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from utils.db import get_db
from utils.auth import login_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        login_input = request.form['login']
        password = request.form['password']
        db = get_db()
        error = None
        
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
            
            try:
                if user['must_change_password'] == 1:
                    session['must_change_password'] = True
                    flash('Por favor, redefina sua senha para continuar.', 'warning')
                    return redirect(url_for('auth.change_password'))
            except (IndexError, KeyError, sqlite3.OperationalError):
                pass

            return redirect(url_for('main.index'))

        flash(error, 'danger')

    return render_template('login.html')

@auth_bp.route('/register', methods=('GET', 'POST'))
def register():
    db = get_db()
    companies = db.execute("SELECT * FROM settings_companies WHERE is_active = 1").fetchall()

    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        company = request.form['company']
        floor = request.form['floor']
        password = request.form['password']
        
        allowed_domains_rows = db.execute("SELECT domain FROM settings_allowed_domains WHERE is_active = 1").fetchall()
        allowed_domains = [row['domain'] for row in allowed_domains_rows]
        
        domain_valid = False
        if not allowed_domains:
            domain_valid = True
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
            return redirect(url_for('auth.login'))

        flash(error, 'danger')

    return render_template('register.html', companies=companies)

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

@auth_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
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
        
        session.pop('must_change_password', None)
        
        flash('Senha alterada com sucesso!', 'success')
        return redirect(url_for('main.index'))
        
    return render_template('change_password.html')
