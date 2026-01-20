import sqlite3
import csv
import io
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, make_response
from utils.db import get_db
from utils.auth import login_required, role_required

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings')
@login_required
@role_required(['ADMIN', 'FACILITIES', 'FACILITIES_PORTARIA'])
def dashboard():
    db = get_db()
    
    item_types = db.execute("SELECT * FROM settings_item_types WHERE is_active = 1 ORDER BY name ASC").fetchall()
    locations = db.execute("SELECT * FROM settings_locations WHERE is_active = 1 ORDER BY name ASC").fetchall()
    companies = db.execute("SELECT * FROM settings_companies WHERE is_active = 1 ORDER BY name ASC").fetchall()
    email_groups = db.execute("SELECT * FROM email_groups ORDER BY name ASC").fetchall()
    domains = []
    
    if session['role'] == 'ADMIN':
        domains = db.execute("SELECT * FROM settings_allowed_domains WHERE is_active = 1 ORDER BY domain ASC").fetchall()
        
    return render_template('settings.html', 
                            item_types=item_types, 
                            locations=locations, 
                            companies=companies, 
                            domains=domains,
                            email_groups=email_groups)

@settings_bp.route('/settings/add/<category>', methods=['POST'])
@login_required
@role_required(['ADMIN', 'FACILITIES', 'FACILITIES_PORTARIA'])
def add(category):
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
                return redirect(url_for('settings.dashboard'))
            db.execute("INSERT INTO settings_allowed_domains (domain) VALUES (?)", (name,))
        else:
            flash('Ação não permitida ou categoria inválida.', 'danger')
            return redirect(url_for('settings.dashboard'))
            
        db.commit()
        flash('Item adicionado com sucesso.', 'success')
    except sqlite3.IntegrityError:
        flash('Erro: Item já existe.', 'danger')
        
    return redirect(url_for('settings.dashboard'))

@settings_bp.route('/settings/delete/<category>/<int:item_id>', methods=['POST'])
@login_required
@role_required(['ADMIN', 'FACILITIES', 'FACILITIES_PORTARIA'])
def delete(category, item_id):
    db = get_db()
    
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
        return redirect(url_for('settings.dashboard'))

    db.execute(query, (item_id,))
    db.commit()
    flash('Item removido.', 'success')
    return redirect(url_for('settings.dashboard'))

@settings_bp.route('/settings/email_groups/add', methods=['POST'])
@login_required
@role_required(['ADMIN', 'FACILITIES', 'FACILITIES_PORTARIA'])
def add_email_group():
    name = request.form['name'].strip()
    emails = request.form['emails'].strip().split(',')
    
    db = get_db()
    try:
        cursor = db.execute("INSERT INTO email_groups (name) VALUES (?)", (name,))
        group_id = cursor.lastrowid
        
        for email in emails:
            email = email.strip()
            if email:
                db.execute("INSERT INTO email_group_members (group_id, email) VALUES (?, ?)", (group_id, email))
        
        db.commit()
        flash(f'Grupo "{name}" criado com sucesso.', 'success')
    except sqlite3.IntegrityError:
        flash('Erro: Nome de grupo já existe.', 'danger')
        
    return redirect(url_for('settings.dashboard'))

@settings_bp.route('/settings/email_groups/delete/<int:group_id>', methods=['POST'])
@login_required
@role_required(['ADMIN', 'FACILITIES', 'FACILITIES_PORTARIA'])
def delete_email_group(group_id):
    db = get_db()
    db.execute("DELETE FROM email_groups WHERE id = ?", (group_id,))
    db.execute("DELETE FROM email_group_members WHERE group_id = ?", (group_id,))
    db.commit()
    flash('Grupo de e-mail removido.', 'success')
    return redirect(url_for('settings.dashboard'))

@settings_bp.route('/history/export')
@login_required
@role_required(['ADMIN', 'FACILITIES', 'FACILITIES_PORTARIA'])
def export():
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

@settings_bp.route('/panel/export')
@login_required
@role_required(['ADMIN', 'FACILITIES', 'FACILITIES_PORTARIA'])
def export_panel():
    db = get_db()
    
    # Exporta itens que NÃO foram entregues ainda (Etapas 1, 2 e 3)
    query = """
        SELECT i.internal_id, i.tracking_code, i.type, i.sender, i.recipient_email, i.recipient_name_manual, 
               i.location, i.status, i.created_at
        FROM items i
        WHERE i.status != 'ENTREGUE'
        ORDER BY i.created_at ASC
    """
    
    items = db.execute(query).fetchall()
    
    si = io.StringIO()
    cw = csv.writer(si, delimiter=';') 
    
    cw.writerow(['ID Interno', 'Código Rastreio', 'Tipo', 'Remetente', 'Destinatário', 'Local', 'Status Atual', 'Data Entrada'])
    
    for item in items:
        cw.writerow([
            item['internal_id'],
            item['tracking_code'] or '',
            item['type'],
            item['sender'],
            item['recipient_email'] or item['recipient_name_manual'] or '',
            item['location'] or '',
            item['status'],
            item['created_at'].strftime('%d/%m/%Y %H:%M:%S') if item['created_at'] else ''
        ])
        
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=painel_facilities.csv"
    output.headers["Content-type"] = "text/csv"
    return output
