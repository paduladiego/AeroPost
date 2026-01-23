import pytest
from utils.db import get_db
from werkzeug.security import generate_password_hash

@pytest.fixture
def logged_in_facilities(client, auth, app):
    """Cria um usuário facilities e loga"""
    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO users (username, password_hash, role, full_name) VALUES (?, ?, ?, ?)",
            ('fac_test', generate_password_hash('f123'), 'FACILITIES', 'Fac Test')
        )
        db.commit()
    auth.login('fac_test', 'f123')
    return client

@pytest.fixture
def test_recipient(app):
    """Cria um usuário comum (destinatário)"""
    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO users (email, password_hash, role, full_name) VALUES (?, ?, ?, ?)",
            ('destinario@teste.com', generate_password_hash('senha123'), 'USER', 'Destinatario Teste')
        )
        db.commit()
    return 'destinario@teste.com'

def test_full_facilities_workflow(logged_in_facilities, test_recipient, app):
    """Testa o fluxo completo: Coleta -> Alocação -> Entrega via Senha"""
    
    # 1. Preparar Item na Portaria
    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO items (internal_id, type, sender, status) VALUES (?, ?, ?, ?)",
            ('AP-FLOW-001', 'Caixa', 'Amazon', 'RECEBIDO_PORTARIA')
        )
        db.commit()
        item_id = db.execute("SELECT id FROM items WHERE internal_id = 'AP-FLOW-001'").fetchone()[0]

    # 2. Coletar (Portaria -> Facilities)
    logged_in_facilities.post(f'/facilities/collect/{item_id}', follow_redirects=True)
    with app.app_context():
        db = get_db()
        item = db.execute("SELECT status FROM items WHERE id = ?", (item_id,)).fetchone()
        assert item['status'] == 'EM_FACILITIES'

    # 3. Alocar (Triagem -> Disponível)
    logged_in_facilities.post(f'/facilities/allocate/{item_id}', data={
        'location': 'Armario A1',
        'recipient_email': test_recipient,
        'recipient_name_manual': 'Destinatario Manual',
        'recipient_floor': '10',
        'observation': 'Cuidado Fragil'
    }, follow_redirects=True)
    
    with app.app_context():
        db = get_db()
        item = db.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
        assert item['status'] == 'DISPONIVEL_PARA_RETIRADA'
        assert item['location'] == 'Armario A1'
        assert item['recipient_email'] == test_recipient

    # 4. Entrega via Senha
    # O destinatário confirma sua própria senha
    response = logged_in_facilities.post(f'/delivery/confirm_password/{item_id}', data={
        'email': test_recipient,
        'password': 'senha123'
    }, follow_redirects=True)
    
    assert b'Item entregue com sucesso' in response.data
    
    with app.app_context():
        db = get_db()
        item_final = db.execute("SELECT status FROM items WHERE id = ?", (item_id,)).fetchone()
        assert item_final['status'] == 'ENTREGUE'
        
        # Verificar comprovante (proof)
        proof = db.execute("SELECT * FROM proofs WHERE item_id = ?", (item_id,)).fetchone()
        assert proof is not None
        assert proof['received_by_name'] == 'Destinatario Teste'
