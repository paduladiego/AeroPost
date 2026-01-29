import os
from flask import Flask
from dotenv import load_dotenv
from utils.db import init_app
from utils.middleware import PrefixMiddleware
from utils.auth import enforce_password_change_logic
from flask_mail import Mail

mail = Mail()

def create_app():
    app = Flask(__name__)
    
    # Carrega variáveis de ambiente do arquivo .env
    load_dotenv()

    # Configurações
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_only_for_mvp')
    # O DATABASE_URL no .env pode ser o caminho do SQLite ou URL do Postgres
    db_url = os.environ.get('DATABASE_URL', 'aeropost.db')
    # Se não for uma URL de banco, assume que é um arquivo SQLite
    if '://' not in db_url and not os.path.isabs(db_url):
        db_url = os.path.join(app.root_path, db_url)
    app.config['DATABASE'] = db_url
    # Versão do Sistema
    base_version = 'v4.3.1'
    app_suffix = os.environ.get('APP_SUFFIX', '') # Ex: '-demo' ou '-Kran'
    app.config['APP_VERSION'] = os.environ.get('APP_VERSION', f"{base_version}{app_suffix}")
    
    # Configurações de E-mail
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')
    
    mail.init_app(app)
    
    @app.context_processor
    def inject_utilities():
        import datetime
        from flask import session
        from utils.db import get_db
        
        # Garante que as unidades estejam disponíveis para o seletor no navbar
        units = []
        active_unit = None
        if 'user_id' in session:
            db = get_db()
            units = db.execute("SELECT id, name FROM settings_companies WHERE is_active = 1").fetchall()
            
            # Encontra o nome da unidade ativa
            role = session.get('role')
            # Se for apenas PORTARIA, remove outras unidades da lista de escolha
            if role == 'PORTARIA':
                units = [u for u in units if u['id'] == session.get('unit_id')]

            for unit in units:
                if unit['id'] == session.get('unit_id'):
                    active_unit = unit
                    break
                    
        return dict(
            app_version=app.config['APP_VERSION'],
            datetime=datetime,
            available_units=units,
            active_unit=active_unit
        )
    
    # Inicializa o Banco de Dados
    init_app(app)
    
    # Middleware para subdiretórios
    app.wsgi_app = PrefixMiddleware(app.wsgi_app)
    
    # Lógica de segurança e troca de senha
    @app.before_request
    def before_request():
        # 1. Garante que se o usuário está logado, ele tenha um unit_id na sessão
        from flask import session
        if 'user_id' in session and 'unit_id' not in session:
            from utils.db import get_db
            db = get_db()
            user = db.execute("SELECT default_unit_id FROM users WHERE id = ?", (session['user_id'],)).fetchone()
            if user and user['default_unit_id']:
                session['unit_id'] = user['default_unit_id']
            else:
                first_unit = db.execute("SELECT id FROM settings_companies WHERE is_active = 1 LIMIT 1").fetchone()
                if first_unit:
                    session['unit_id'] = first_unit['id']

        # 2. Lógica de troca de senha obrigatória
        return enforce_password_change_logic()

    # Registro de Blueprints
    from routes.main import main_bp
    from routes.auth import auth_bp
    from routes.portaria import portaria_bp
    from routes.facilities import facilities_bp
    from routes.settings import settings_bp
    from routes.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(portaria_bp)
    app.register_blueprint(facilities_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(admin_bp)

    # Rota para o Favicon
    @app.route('/favicon.ico')
    def favicon():
        from flask import send_from_directory
        return send_from_directory(os.path.join(app.root_path, 'landing', 'assets', 'favicon'),
                               'favicon.ico')

    # Rota para servir assets da landing page (necessário para os favicons no App)
    @app.route('/landing/<path:filename>')
    def serve_landing(filename):
        from flask import send_from_directory
        return send_from_directory(os.path.join(app.root_path, 'landing'), filename)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
    # app.run(host='0.0.0.0', port=5000, debug=True)
