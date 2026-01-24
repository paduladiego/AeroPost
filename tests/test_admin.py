import pytest
from utils.db import get_db
from werkzeug.security import generate_password_hash

@pytest.fixture
def logged_in_admin(client, auth, app):
    """Cria um admin real no banco de teste e loga"""
    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO users (username, password_hash, role, full_name) VALUES (?, ?, ?, ?)",
            ('admin_master', generate_password_hash('master123'), 'ADMIN', 'Admin Master')
        )
        db.commit()
    auth.login('admin_master', 'master123')
    return client

def test_crud_settings(logged_in_admin, app):
    """Testa adicionar e deletar tipos, locais e empresas"""
    # 1. Adicionar e Deletar Tipo de Item
    logged_in_admin.post('/settings/add/type', data={'name': 'Envelope Especial'}, follow_redirects=True)
    with app.app_context():
        db = get_db()
        item = db.execute("SELECT id FROM settings_item_types WHERE name = 'Envelope Especial'").fetchone()
        assert item is not None
        logged_in_admin.post(f'/settings/delete/type/{item["id"]}', follow_redirects=True)
        assert db.execute("SELECT id FROM settings_item_types WHERE id = ?", (item["id"],)).fetchone() is None

    # 2. Adicionar e Deletar Local
    logged_in_admin.post('/settings/add/location', data={'name': 'Gaveta 99'}, follow_redirects=True)
    with app.app_context():
        db = get_db()
        loc = db.execute("SELECT id FROM settings_locations WHERE name = 'Gaveta 99'").fetchone()
        assert loc is not None
        logged_in_admin.post(f'/settings/delete/location/{loc["id"]}', follow_redirects=True)
        assert db.execute("SELECT id FROM settings_locations WHERE id = ?", (loc["id"],)).fetchone() is None

    # 3. Adicionar e Deletar Empresa
    logged_in_admin.post('/settings/add/company', data={'name': 'Empresa Teste SA'}, follow_redirects=True)
    with app.app_context():
        db = get_db()
        comp = db.execute("SELECT id FROM settings_companies WHERE name = 'Empresa Teste SA'").fetchone()
        assert comp is not None
        logged_in_admin.post(f'/settings/delete/company/{comp["id"]}', follow_redirects=True)
        assert db.execute("SELECT id FROM settings_companies WHERE id = ?", (comp["id"],)).fetchone() is None

    # 4. Adicionar e Deletar Domínio (Apenas Admin)
    logged_in_admin.post('/settings/add/domain', data={'name': '@teste.com'}, follow_redirects=True)
    with app.app_context():
        db = get_db()
        dom = db.execute("SELECT id FROM settings_allowed_domains WHERE domain = '@teste.com'").fetchone()
        assert dom is not None
        logged_in_admin.post(f'/settings/delete/domain/{dom["id"]}', follow_redirects=True)
        assert db.execute("SELECT id FROM settings_allowed_domains WHERE id = ?", (dom["id"],)).fetchone() is None

def test_user_management(logged_in_admin, app):
    """Testa criação de portaria, bloqueio e reset de senha"""
    # 0. Criar uma Unidade para o teste
    logged_in_admin.post('/settings/add/company', data={'name': 'Unidade Teste 1'}, follow_redirects=True)
    with app.app_context():
        db = get_db()
        unit = db.execute("SELECT id FROM settings_companies WHERE name = 'Unidade Teste 1'").fetchone()
        unit_id = unit['id']

    # 1. Criar Usuário Portaria
    logged_in_admin.post('/users/create_portaria', data={
        'full_name': 'Porteiro de Teste',
        'username': 'porteiro1',
        'password': 'password123',
        'unit_id': unit_id
    }, follow_redirects=True)
    
    with app.app_context():
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = 'porteiro1'").fetchone()
        assert user is not None
        assert user['role'] == 'PORTARIA'
        assert user['default_unit_id'] == unit_id

    # 2. Bloquear Usuário
    logged_in_admin.post(f'/users/toggle_block/{user["id"]}', follow_redirects=True)
    with app.app_context():
        db = get_db()
        user_blocked = db.execute("SELECT is_active FROM users WHERE id = ?", (user['id'],)).fetchone()
        assert user_blocked['is_active'] == 0

    # 3. Reset de Senha
    response = logged_in_admin.post(f'/users/reset_password/{user["id"]}', follow_redirects=True)
    assert b'mudar123' in response.data
    assert b'resetada' in response.data
    with app.app_context():
        db = get_db()
        user_reset = db.execute("SELECT must_change_password FROM users WHERE id = ?", (user['id'],)).fetchone()
        assert user_reset['must_change_password'] == 1

def test_email_groups_crud(logged_in_admin, app):
    """Testa CRUD de grupos de e-mail"""
    # 1. Criar Grupo
    logged_in_admin.post('/settings/email_groups/add', data={
        'name': 'Grupo TI',
        'emails': 'ti1@exemplo.com, ti2@exemplo.com'
    }, follow_redirects=True)
    
    with app.app_context():
        db = get_db()
        group = db.execute("SELECT * FROM email_groups WHERE name = 'Grupo TI'").fetchone()
        assert group is not None
        members = db.execute("SELECT email FROM email_group_members WHERE group_id = ?", (group['id'],)).fetchall()
        assert len(members) == 2

    # 2. Editar Grupo
    logged_in_admin.post(f'/settings/email_groups/edit/{group["id"]}', data={
        'name': 'Grupo TI VIP',
        'emails': 'vip@exemplo.com'
    }, follow_redirects=True)
    
    with app.app_context():
        db = get_db()
        group_edited = db.execute("SELECT name FROM email_groups WHERE id = ?", (group['id'],)).fetchone()
        assert group_edited['name'] == 'Grupo TI VIP'
        members_edited = db.execute("SELECT email FROM email_group_members WHERE group_id = ?", (group['id'],)).fetchall()
        assert len(members_edited) == 1
        assert members_edited[0]['email'] == 'vip@exemplo.com'

    # 3. Deletar Grupo
    logged_in_admin.post(f'/settings/email_groups/delete/{group["id"]}', follow_redirects=True)
    with app.app_context():
        db = get_db()
        assert db.execute("SELECT id FROM email_groups WHERE id = ?", (group["id"],)).fetchone() is None
        assert db.execute("SELECT id FROM email_group_members WHERE group_id = ?", (group["id"],)).fetchone() is None
