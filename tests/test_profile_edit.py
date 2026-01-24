import pytest
from utils.db import get_db
from werkzeug.security import generate_password_hash

@pytest.fixture
def users(app):
    with app.app_context():
        db = get_db()
        # Admin
        db.execute("INSERT INTO users (username, password_hash, role, full_name) VALUES (?, ?, ?, ?)",
                   ('admin_test', generate_password_hash('pass'), 'ADMIN', 'Admin Test'))
        # Facilities
        db.execute("INSERT INTO users (username, password_hash, role, full_name) VALUES (?, ?, ?, ?)",
                   ('fac_test', generate_password_hash('pass'), 'FACILITIES', 'Fac Test'))
        # User 1
        db.execute("INSERT INTO users (username, password_hash, role, full_name, email) VALUES (?, ?, ?, ?, ?)",
                   ('user1', generate_password_hash('pass'), 'USER', 'User One', 'user1@test.com'))
        # User 2
        db.execute("INSERT INTO users (username, password_hash, role, full_name, email) VALUES (?, ?, ?, ?, ?)",
                   ('user2', generate_password_hash('pass'), 'USER', 'User Two', 'user2@test.com'))
        db.commit()
        
        return {
            'admin': db.execute("SELECT id FROM users WHERE username = 'admin_test'").fetchone()['id'],
            'fac': db.execute("SELECT id FROM users WHERE username = 'fac_test'").fetchone()['id'],
            'user1': db.execute("SELECT id FROM users WHERE username = 'user1'").fetchone()['id'],
            'user2': db.execute("SELECT id FROM users WHERE username = 'user2'").fetchone()['id']
        }

def test_admin_can_edit_user(client, auth, users):
    auth.login('admin_test', 'pass')
    response = client.post(f'/profile/{users["user1"]}', data={
        'full_name': 'Updated User One',
        'floor': '10th Floor',
        'unit_id': 1
    }, follow_redirects=True)
    assert b'Dados de Updated User One atualizados com sucesso.' in response.data

def test_facilities_can_edit_user(client, auth, users):
    auth.login('fac_test', 'pass')
    response = client.post(f'/profile/{users["user1"]}', data={
        'full_name': 'Fac Updated User',
        'floor': '5th Floor',
        'unit_id': 1
    }, follow_redirects=True)
    assert b'Dados de Fac Updated User atualizados com sucesso.' in response.data

def test_facilities_cannot_edit_admin(client, auth, users):
    auth.login('fac_test', 'pass')
    response = client.get(f'/profile/{users["admin"]}', follow_redirects=True)
    assert b'Acesso negado: Apenas Administradores podem editar outros Administradores.' in response.data

def test_user_cannot_edit_others(client, auth, users):
    auth.login('user1', 'pass')
    response = client.get(f'/profile/{users["user2"]}', follow_redirects=True)
    assert b'Acesso negado: Você não tem permissão para editar outros usuários.' in response.data

def test_user_can_edit_self(client, auth, users):
    auth.login('user1', 'pass')
    response = client.post(f'/profile/{users["user1"]}', data={
        'full_name': 'Myself Updated',
        'floor': 'My Floor',
        'unit_id': 1
    }, follow_redirects=True)
    assert b'Perfil atualizado com sucesso!' in response.data
