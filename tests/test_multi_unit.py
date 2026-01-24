import pytest
from utils.db import get_db
from werkzeug.security import generate_password_hash

@pytest.fixture
def multi_unit_setup(app):
    """Configura duas unidades e um usuário vinculado à Unidade A"""
    with app.app_context():
        db = get_db()
        # 1. Criar Unidades
        db.execute("INSERT INTO settings_companies (name) VALUES (?)", ("Unidade Central",)) # ID 1
        db.execute("INSERT INTO settings_companies (name) VALUES (?)", ("Unidade Jundiai",)) # ID 2
        
        # 2. Criar Usuário Admin vinculado à Unidade Central
        db.execute(
            "INSERT INTO users (username, password_hash, role, full_name, default_unit_id) VALUES (?, ?, ?, ?, ?)",
            ('admin_multi', generate_password_hash('admin123'), 'ADMIN', 'Admin Multi', 1)
        )
        db.commit()
    return {'unit_central': 1, 'unit_jundiai': 2}

def test_unit_isolation(client, auth, multi_unit_setup, app):
    """Verifica se um item registrado na Unidade A não aparece na Unidade B"""
    auth.login('admin_multi', 'admin123')
    
    # 1. Garantir que estamos na Unidade Central (ID 1)
    client.get('/set_unit/1', follow_redirects=True)
    
    # 2. Registrar item na Unidade Central
    with client.session_transaction() as sess:
        sess['unit_id'] = '1'
    
    client.post('/portaria/register', data={
        'type': 'Caixa',
        'tracking_code': 'TRK-CENTRAL',
        'sender': 'Fornecedor Central'
    }, follow_redirects=True)
    
    # Verifica se aparece no dashboard da portaria (Central)
    with client.session_transaction() as sess:
        sess['unit_id'] = '1'
    response = client.get('/portaria')
    assert b'TRK-CENTRAL' in response.data
    
    # 3. Mudar para Unidade Jundiai (ID 2)
    client.get('/set_unit/2', follow_redirects=True)
    
    # Verifica se o dashboard de Jundiai está VAZIO (não deve ver o item da Central)
    response = client.get('/portaria')
    assert b'TRK-CENTRAL' not in response.data
    assert b'Nenhum item' in response.data

def test_unit_switching_persistence(client, auth, multi_unit_setup, app):
    """Verifica se a troca de unidade persiste na sessão"""
    auth.login('admin_multi', 'admin123')
    
    # Mudar para Jundiai
    client.get('/set_unit/2', follow_redirects=True)
    
    # Fazer uma requisição qualquer e ver se as estatísticas do dashboard refletem a unidade 2
    response = client.get('/facilities')
    # No dashboard de facilities, a unidade ativa deve estar presente no contexto
    # Como não temos itens em Jundiai, as estatísticas devem ser 0
    assert b'<h3>0</h3>' in response.data

def test_registration_inherits_active_unit(client, auth, multi_unit_setup, app):
    """Verifica se o item novo herda o ID da unidade ativa na sessão"""
    auth.login('admin_multi', 'admin123')
    
    # Set Unidade Jundiai
    client.get('/set_unit/2', follow_redirects=True)
    
    # Registrar item
    client.post('/portaria/register', data={
        'type': 'Envelope',
        'tracking_code': 'TRK-JUNDIAI',
        'sender': 'Fornecedor Local'
    }, follow_redirects=True)
    
    with app.app_context():
        db = get_db()
        item = db.execute("SELECT unit_id FROM items WHERE tracking_code = 'TRK-JUNDIAI'").fetchone()
        assert item['unit_id'] == 2
