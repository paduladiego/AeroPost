import os
import pytest
import tempfile
from app import create_app
from utils.db import get_db

@pytest.fixture
def app():
    # Cria um arquivo temporário para o banco de dados de teste
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app()
    app.config.update({
        'TESTING': True,
        'DATABASE': db_path,
        'SECRET_KEY': 'test_secret',
        'MAIL_SUPPRESS_SEND': True  # Não envia e-mails reais nos testes
    })

    # Inicializa o banco de dados de teste usando o schema.sql
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

    yield app

    # Limpeza após os testes
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

class AuthActions:
    def __init__(self, client):
        self._client = client

    def login(self, username='admin', password='admin123'):
        data = {
            'login': username,
            'password': password
        }
        return self._client.post('/login', data=data, follow_redirects=True)

    def logout(self):
        return self._client.get('/logout', follow_redirects=True)

@pytest.fixture
def auth(client):
    return AuthActions(client)
