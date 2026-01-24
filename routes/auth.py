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
            
            # Define unit_id imediatamente após o login para evitar telas vazias
            db = get_db()
            if user['default_unit_id']:
                session['unit_id'] = user['default_unit_id']
            else:
                first_unit = db.execute("SELECT id FROM settings_companies WHERE is_active = 1 LIMIT 1").fetchone()
                if first_unit:
                    session['unit_id'] = first_unit['id']
            
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
            # Busca o ID da unidade selecionada pelo texto
            unit_id = db.execute("SELECT id FROM settings_companies WHERE name = ?", (company,)).fetchone()[0]
            
            db.execute(
                'INSERT INTO users (email, password_hash, role, full_name, floor, company, default_unit_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (email, generate_password_hash(password), 'USER', full_name, floor, company, unit_id)
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

        # REGRA DE SEGURANÇA: Admin principal (ID 1) só via banco
        if session['user_id'] == 1:
            flash('Erro de Segurança: A senha do administrador principal só pode ser alterada diretamente no banco de dados.', 'danger')
            return redirect(url_for('auth.profile'))

        db = get_db()
        db.execute(
            'UPDATE users SET password_hash = ?, must_change_password = 0 WHERE id = ?',
            (generate_password_hash(password), session['user_id'])
        )
        db.commit()
        
        session.pop('must_change_password', None)
        
        flash('Senha alterada com sucesso!', 'success')
        return redirect(url_for('main.index'))
        flash('Senha alterada com sucesso!', 'success')
        return redirect(url_for('main.index'))
        
    return render_template('change_password.html')

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        
        if user:
            from flask import current_app
            from itsdangerous import URLSafeTimedSerializer
            from utils.notifications import send_reset_email
            
            s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
            token = s.dumps(email, salt='password-reset-salt')
            
            if send_reset_email(email, token):
                flash('Um link de recuperação foi enviado para seu e-mail.', 'info')
            else:
                flash('Erro ao enviar e-mail. Tente novamente.', 'danger')
        else:
            # Por segurança, mostramos a mesma mensagem mesmo se o email não existir
            flash('Se o e-mail estiver cadastrado, você receberá um link de recuperação.', 'info')
            
        return redirect(url_for('auth.login'))
        
    return render_template('forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    from flask import current_app
    from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
    
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=3600) # 1 hora
    except (SignatureExpired, BadTimeSignature):
        flash('O link de recuperação é inválido ou expirou.', 'danger')
        return redirect(url_for('auth.forgot_password'))
        
    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('As senhas não coincidem.', 'danger')
            return render_template('reset_token.html', token=token)
            
        db = get_db()
        # Busca o ID do usuário pelo email para validar se é o Admin Principal
        user = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if user and user['id'] == 1:
            flash('Erro de Segurança: A senha do administrador principal só pode ser alterada diretamente no banco de dados.', 'danger')
            return redirect(url_for('auth.login'))

        db.execute(
            'UPDATE users SET password_hash = ?, must_change_password = 0 WHERE email = ?',
            (generate_password_hash(password), email)
        )
        db.commit()
        
        flash('Sua senha foi redefinida com sucesso! Faça login.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('reset_token.html', token=token)

@auth_bp.route('/profile', methods=['GET', 'POST'])
@auth_bp.route('/profile/<int:user_id>', methods=['GET', 'POST'])
@login_required
def profile(user_id=None):
    if session.get('role') == 'PORTARIA':
        flash('Acesso negado: Usuários de Portaria não podem editar perfil.', 'danger')
        return redirect(url_for('main.index'))
    
    db = get_db()
    current_user_id = session['user_id']
    is_admin = session.get('role') == 'ADMIN'
    is_facilities = session.get('role') in ['FACILITIES', 'FACILITIES_PORTARIA']
    
    # Se user_id não for informado, usa o do usuário logado
    target_user_id = user_id if user_id is not None else current_user_id
    
    # Busca dados do usuário alvo
    user = db.execute('SELECT * FROM users WHERE id = ?', (target_user_id,)).fetchone()
    if not user:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('admin.users_list'))

    # Verificação de Permissão:
    # 1. Se não for ele mesmo, deve ser ADMIN ou FACILITIES
    if target_user_id != current_user_id:
        if not (is_admin or is_facilities):
            flash('Acesso negado: Você não tem permissão para editar outros usuários.', 'danger')
            return redirect(url_for('main.index'))
        
        # 2. Se for FACILITIES, não pode editar usuários ADMIN
        if is_facilities and user['role'] == 'ADMIN':
            flash('Acesso negado: Apenas Administradores podem editar outros Administradores.', 'danger')
            return redirect(url_for('admin.users_list'))

    if request.method == 'POST':
        full_name = request.form['full_name']
        floor = request.form['floor']
        unit_id = request.form['unit_id']
        
        # Busca o nome da empresa correspondente ao ID para manter o campo 'company' consistente
        company_row = db.execute("SELECT name FROM settings_companies WHERE id = ?", (unit_id,)).fetchone()
        company_name = company_row['name'] if company_row else ''
        
        db.execute(
            'UPDATE users SET full_name = ?, floor = ?, company = ?, default_unit_id = ? WHERE id = ?',
            (full_name, floor, company_name, unit_id, target_user_id)
        )
        db.commit()
        
        # Sincroniza a sessão apenas se estiver editando o próprio perfil
        if target_user_id == current_user_id:
            session['name'] = full_name
            session['unit_id'] = int(unit_id)
            flash('Perfil atualizado com sucesso!', 'success')
            return redirect(url_for('main.index'))
        else:
            flash(f'Dados de {full_name} atualizados com sucesso.', 'success')
            return redirect(url_for('admin.users_list'))

    # Carrega lista de empresas para o dropdown
    companies = db.execute("SELECT * FROM settings_companies WHERE is_active = 1").fetchall()
    
    return render_template('profile.html', user=user, companies=companies, editing_other=(target_user_id != current_user_id))

@auth_bp.route('/check_user/<email>')
def check_user(email):
    db = get_db()
    user = db.execute('SELECT id FROM users WHERE email = ? AND is_active = 1', (email,)).fetchone()
    return {'exists': user is not None}
