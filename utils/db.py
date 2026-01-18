import sqlite3
import os
from flask import g, current_app

def get_db():
    if 'db' not in g:
        db_url = current_app.config['DATABASE']
        
        if db_url.startswith('postgresql://') or db_url.startswith('postgres://'):
            import psycopg2
            from psycopg2.extras import DictCursor
            g.db_type = 'postgres'
            conn = psycopg2.connect(db_url, cursor_factory=DictCursor)
            g.db = conn
        else:
            # Assume SQLite
            g.db_type = 'sqlite'
            path = db_url.replace('sqlite:///', '')
            # Se não for um caminho absoluto e não começar com ./ ou ../, assume que é relativo à raiz
            if not os.path.isabs(path) and not path.startswith('.'):
                path = os.path.join(current_app.root_path, path)
                
            conn = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)
            conn.row_factory = sqlite3.Row
            g.db = conn
            
    return g.db

def query_db(query, args=(), one=False):
    """Executa uma query compatível com SQLite e Postgres"""
    db = get_db()
    db_type = g.get('db_type', 'sqlite')
    
    # Compatibilidade de Placeholders: SQLite (?) vs Postgres (%s)
    if db_type == 'postgres':
        query = query.replace('?', '%s')
    
    cur = db.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    db_type = g.get('db_type', 'sqlite')
    
    with current_app.open_resource('schema.sql', mode='r') as f:
        sql_script = f.read()
        
    cursor = db.cursor()
    if db_type == 'postgres':
        cursor.execute(sql_script)
    else:
        cursor.executescript(sql_script)
    db.commit()
    cursor.close()

def init_app(app):
    app.teardown_appcontext(close_db)
    @app.cli.command('init-db')
    def init_db_command():
        init_db()
        print("Banco de Dados inicializado.")

    @app.cli.command('create-admin')
    def create_admin_command():
        from werkzeug.security import generate_password_hash
        db = get_db()
        db_type = g.get('db_type', 'sqlite')
        
        username = 'admin'
        password = generate_password_hash('admin123')
        full_name = 'Administrador Sistema'
        email = 'admin@aeropost.local'

        # Placeholder universal
        placeholder = '%s' if db_type == 'postgres' else '?'
        
        sql = f"""
            INSERT INTO users (username, password, full_name, email, role, is_active, must_change_password)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, 'admin', 1, 0)
        """
        
        cursor = db.cursor()
        try:
            cursor.execute(sql, (username, password, full_name, email))
            db.commit()
            print("Usuário Admin criado com sucesso!")
            print("Login: admin / Senha: admin123")
        except Exception as e:
            print(f"Erro ao criar admin (provavelmente já existe): {e}")
        finally:
            cursor.close()
