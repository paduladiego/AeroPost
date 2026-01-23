import pytest
import datetime
from utils.db import get_db
from werkzeug.security import generate_password_hash

@pytest.fixture
def logged_in_portaria(client, auth, app):
    """Cria um usuário portaria e loga"""
    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO users (username, password_hash, role, full_name) VALUES (?, ?, ?, ?)",
            ('porteiro_test', generate_password_hash('p123'), 'PORTARIA', 'Porteiro Teste')
        )
        db.commit()
    auth.login('porteiro_test', 'p123')
    return client

def test_register_item_flow(logged_in_portaria, app):
    """Testa o registro de uma nova encomenda na portaria"""
    # 1. Registrar Item
    response = logged_in_portaria.post('/portaria/register', data={
        'type': 'Caixa',
        'tracking_code': 'TRK123456',
        'sender': 'Amazon Prime'
    }, follow_redirects=True)
    
    assert b'registrado com sucesso' in response.data
    
    with app.app_context():
        db = get_db()
        item = db.execute("SELECT * FROM items WHERE tracking_code = 'TRK123456'").fetchone()
        assert item is not None
        assert item['type'] == 'Caixa'
        assert item['sender'] == 'Amazon Prime'
        assert item['status'] == 'RECEBIDO_PORTARIA'
        
        # Verificar o ID Interno (Formato AP-YYYYMMDD-XXXX)
        today = datetime.datetime.now().strftime('%Y%m%d')
        assert item['internal_id'].startswith(f"AP-{today}-")
        
        # Verificar se registrou o movimento
        mov = db.execute("SELECT * FROM movements WHERE item_id = ?", (item['id'],)).fetchone()
        assert mov is not None
        assert mov['action'] == 'REGISTER_PORTARIA'

def test_portaria_dashboard_lists_items(logged_in_portaria, app):
    """Verifica se os itens registrados aparecem no dashboard da portaria"""
    # Registrar item via Rota (simulando fluxo real) em vez de SQL direto
    logged_in_portaria.post('/portaria/register', data={
        'type': 'Envelope',
        'tracking_code': 'TRK-DASHBOARD-TEST',
        'sender': 'Dashboard Test Sender'
    }, follow_redirects=True)

    response = logged_in_portaria.get('/portaria')
    assert b'Dashboard Test Sender' in response.data
