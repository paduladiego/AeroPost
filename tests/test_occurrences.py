import pytest
from utils.db import get_db
from werkzeug.security import generate_password_hash

@pytest.fixture
def logged_in_facilities(client, auth, app):
    """Cria um usuário facilities com senha 'f123' e loga"""
    with app.app_context():
        db = get_db()
        # Garante que o usuário tem uma unidade padrão
        db.execute("INSERT OR IGNORE INTO settings_companies (id, name) VALUES (1, 'Unidade Teste')")
        db.execute(
            "INSERT INTO users (username, password_hash, role, full_name, default_unit_id) VALUES (?, ?, ?, ?, ?)",
            ('fac_occ', generate_password_hash('f123'), 'FACILITIES', 'Fac Occ', 1)
        )
        db.commit()
    auth.login('fac_occ', 'f123')
    # Seta a unidade na sessão (nossa rota de login já faz isso normalmente)
    with client.session_transaction() as sess:
        sess['unit_id'] = 1
    return client

def test_occurrence_wrong_password(logged_in_facilities, app):
    """Testa erro de senha ao registrar ocorrência"""
    with app.app_context():
        db = get_db()
        db.execute("INSERT INTO items (internal_id, type, status, unit_id) VALUES (?, ?, ?, ?)",
                   ('AP-ERR-001', 'Caixa', 'DISPONIVEL_PARA_RETIRADA', 1))
        db.commit()

    response = logged_in_facilities.post('/facilities/register-occurrence', data={
        'internal_id': 'AP-ERR-001',
        'action': 'EXTRAVIADO',
        'note': 'Sumiu do armario',
        'password': 'senha_errada'
    }, follow_redirects=True)

    assert b'Senha de confirmacao incorreta' in response.data
    
    with app.app_context():
        db = get_db()
        item = db.execute("SELECT status FROM items WHERE internal_id = 'AP-ERR-001'").fetchone()
        assert item['status'] == 'DISPONIVEL_PARA_RETIRADA'

def test_occurrence_lost_item_and_history(logged_in_facilities, app):
    """Testa registro de extravio e verificação no histórico"""
    with app.app_context():
        db = get_db()
        db.execute("INSERT INTO items (internal_id, type, status, unit_id) VALUES (?, ?, ?, ?)",
                   ('AP-LOST-001', 'Envelope', 'DISPONIVEL_PARA_RETIRADA', 1))
        db.commit()

    response = logged_in_facilities.post('/facilities/register-occurrence', data={
        'internal_id': 'AP-LOST-001',
        'action': 'EXTRAVIADO',
        'note': 'Nao foi encontrado no local indicado',
        'password': 'f123'
    }, follow_redirects=True)

    assert b'Ocorrencia de EXTRAVIADO registrada' in response.data
    
    with app.app_context():
        db = get_db()
        item = db.execute("SELECT status FROM items WHERE internal_id = 'AP-LOST-001'").fetchone()
        assert item['status'] == 'EXTRAVIADO'
        
        # Verificar histórico
        res_hist = logged_in_facilities.get('/history')
        assert b'AP-LOST-001' in res_hist.data
        assert b'Extraviado' in res_hist.data
        assert b'Nao foi encontrado no local indicado' in res_hist.data

def test_occurrence_recovery_workflow(logged_in_facilities, app):
    """Testa o fluxo de recuperação (Extraviado -> Em Facilities)"""
    with app.app_context():
        db = get_db()
        db.execute("INSERT INTO items (internal_id, type, status, unit_id) VALUES (?, ?, ?, ?)",
                   ('AP-REC-001', 'Pacote', 'EXTRAVIADO', 1))
        # Adiciona o proof de extravio manual
        db.execute("INSERT INTO proofs (item_id, signature_data, delivered_by, received_by_name, occurrence_note) VALUES "
                   "((SELECT id FROM items WHERE internal_id='AP-REC-001'), 'OCC_EXTRAVIADO', 1, 'SISTEMA', 'Sumiu')", )
        db.commit()

    # Tenta recuperar
    response = logged_in_facilities.post('/facilities/register-occurrence', data={
        'internal_id': 'AP-REC-001',
        'action': 'RECUPERADO',
        'note': 'Encontrado atras da mesa',
        'password': 'f123'
    }, follow_redirects=True)

    assert b'recuperado! Ele voltou para a aba' in response.data
    
    with app.app_context():
        db = get_db()
        item = db.execute("SELECT status FROM items WHERE internal_id = 'AP-REC-001'").fetchone()
        assert item['status'] == 'EM_FACILITIES'
        
        # Proof deve ter sido deletado
        proof = db.execute("SELECT * FROM proofs WHERE item_id = (SELECT id FROM items WHERE internal_id='AP-REC-001')").fetchone()
        assert proof is None
