import pytest
from utils.db import get_db
from werkzeug.security import generate_password_hash

def test_login_page_loads(client):
    """Verifica se a página de login carrega"""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'AeroPost' in response.data

def test_admin_login_success(client, auth, app):
    """Testa o login com sucesso do administrador padrão"""
    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO users (username, password_hash, role, full_name) VALUES (?, ?, ?, ?)",
            ('admin_test', generate_password_hash('test123'), 'ADMIN', 'Admin Teste')
        )
        db.commit()

    response = auth.login('admin_test', 'test123')
    assert b'Admin Teste' in response.data
    assert b'Sair' in response.data

def test_login_invalid_credentials(auth):
    """Testa falha de login com credenciais erradas"""
    response = auth.login('errado', 'senha_errada')
    assert b'Usu\xc3\xa1rio incorreto' in response.data or b'Senha incorreta' in response.data
