import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash
from utils.db import get_db
from utils.auth import login_required, role_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/users')
@login_required
@role_required(['ADMIN', 'FACILITIES', 'FACILITIES_PORTARIA'])
def users_list():
    db = get_db()
    active_users = db.execute('SELECT * FROM users WHERE is_active = 1 ORDER BY created_at DESC').fetchall()
    blocked_users = db.execute('SELECT * FROM users WHERE is_active = 0 ORDER BY created_at DESC').fetchall()
    units = db.execute("SELECT * FROM settings_companies WHERE is_active = 1").fetchall()
    return render_template('users.html', active_users=active_users, blocked_users=blocked_users, units=units)

@admin_bp.route('/users/create_portaria', methods=['POST'])
@login_required
@role_required(['ADMIN', 'FACILITIES', 'FACILITIES_PORTARIA'])
def user_create_portaria():
    full_name = request.form['full_name']
    username = request.form['username']
    password = request.form['password']
    unit_id = request.form.get('unit_id')
    
    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (username, role, full_name, password_hash, default_unit_id) VALUES (?, ?, ?, ?, ?)",
            (username, 'PORTARIA', full_name, generate_password_hash(password), unit_id)
        )
        db.commit()
        flash(f'Usuário de Portaria {username} criado.', 'success')
    except sqlite3.IntegrityError:
        flash(f'Erro: Usuário {username} já existe.', 'danger')
        
    return redirect(url_for('admin.users_list'))

@admin_bp.route('/users/promote/<int:user_id>', methods=['POST'])
@login_required
@role_required(['ADMIN', 'FACILITIES', 'FACILITIES_PORTARIA'])
def user_promote(user_id):
    db = get_db()
    target = db.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
    
    if target['role'] == 'ADMIN' and session['role'] != 'ADMIN':
        flash('Erro: Você não tem permissão para gerenciar Administradores.', 'danger')
        return redirect(url_for('admin.users_list'))
        
    db.execute("UPDATE users SET role = 'FACILITIES' WHERE id = ?", (user_id,))
    db.commit()
    flash('Usuário promovido para FACILITIES.', 'success')
    return redirect(url_for('admin.users_list'))

@admin_bp.route('/users/demote/<int:user_id>', methods=['POST'])
@login_required
@role_required(['ADMIN', 'FACILITIES', 'FACILITIES_PORTARIA'])
def user_demote(user_id):
    db = get_db()
    target = db.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()

    if target['role'] == 'ADMIN' and session['role'] != 'ADMIN':
        flash('Erro: Você não tem permissão para gerenciar Administradores.', 'danger')
        return redirect(url_for('admin.users_list'))

    db.execute("UPDATE users SET role = 'USER' WHERE id = ?", (user_id,))
    db.commit()
    flash('Usuário rebaixado para USER.', 'success')
    return redirect(url_for('admin.users_list'))

@admin_bp.route('/users/toggle_block/<int:user_id>', methods=['POST'])
@login_required
@role_required(['ADMIN', 'FACILITIES', 'FACILITIES_PORTARIA'])
def user_toggle_block(user_id):
    db = get_db()
    user = db.execute("SELECT role, is_active FROM users WHERE id = ?", (user_id,)).fetchone()
    
    if user['role'] == 'ADMIN' and session['role'] != 'ADMIN':
        flash('Erro: Você não tem permissão para bloquear um Administrador.', 'danger')
        return redirect(url_for('admin.users_list'))

    new_status = 0 if user['is_active'] else 1
    
    db.execute("UPDATE users SET is_active = ? WHERE id = ?", (new_status, user_id))
    db.commit()
    
    msg = 'Usuário bloqueado.' if new_status == 0 else 'Usuário desbloqueado.'
    flash(msg, 'warning' if new_status == 0 else 'success')
    return redirect(url_for('admin.users_list'))

@admin_bp.route('/users/reset_password/<int:user_id>', methods=['POST'])
@login_required
@role_required(['ADMIN', 'FACILITIES', 'FACILITIES_PORTARIA'])
def user_reset_password(user_id):
    db = get_db()
    target = db.execute("SELECT role, full_name, email FROM users WHERE id = ?", (user_id,)).fetchone()
    
    if target['role'] == 'ADMIN' and session['role'] != 'ADMIN':
        flash('Erro: Você não tem permissão para gerenciar Administradores.', 'danger')
        return redirect(url_for('admin.users_list'))

    # REGRA DE SEGURANÇA: Admin principal (ID 1) só via banco
    if user_id == 1:
        flash('Erro de Segurança: A senha do administrador principal não pode ser resetada via interface.', 'danger')
        return redirect(url_for('admin.users_list'))

    default_password = 'mudar123'
    db.execute(
        "UPDATE users SET password_hash = ?, must_change_password = 1 WHERE id = ?", 
        (generate_password_hash(default_password), user_id)
    )
    db.commit()
    
    flash(f'Senha de {target["full_name"]} resetada para "{default_password}". O usuário deverá trocá-la no próximo login.', 'success')
    return redirect(url_for('admin.users_list'))

@admin_bp.route('/users/grant_portaria/<int:user_id>', methods=['POST'])
@login_required
@role_required(['ADMIN', 'FACILITIES', 'FACILITIES_PORTARIA'])
def user_grant_portaria(user_id):
    db = get_db()
    target = db.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
    
    if target['role'] != 'FACILITIES':
        flash('Erro: Apenas usuários FACILITIES podem receber este acesso extra.', 'danger')
        return redirect(url_for('admin.users_list'))

    db.execute("UPDATE users SET role = 'FACILITIES_PORTARIA' WHERE id = ?", (user_id,))
    db.commit()
    flash('Acesso à Portaria concedido ao usuário Facilities.', 'success')
    return redirect(url_for('admin.users_list'))

@admin_bp.route('/users/revoke_portaria/<int:user_id>', methods=['POST'])
@login_required
@role_required(['ADMIN', 'FACILITIES', 'FACILITIES_PORTARIA'])
def user_revoke_portaria(user_id):
    db = get_db()
    target = db.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
    
    if target['role'] != 'FACILITIES_PORTARIA':
        flash('Erro: Este usuário não possui acesso duplo para ser revogado.', 'danger')
        return redirect(url_for('admin.users_list'))

    db.execute("UPDATE users SET role = 'FACILITIES' WHERE id = ?", (user_id,))
    db.commit()
    flash('Acesso à Portaria revogado. O usuário agora é apenas FACILITIES.', 'warning')
    return redirect(url_for('admin.users_list'))
