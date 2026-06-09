from flask import Flask
from flask_login import LoginManager
from app.database import init_db, get_db
from app.models.analyst import Analyst

login_manager = LoginManager()
login_manager.login_view = 'auth.login'


@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM analysts WHERE id = %s", (int(user_id),))
            return Analyst.from_row(cur.fetchone())
    finally:
        conn.close()


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    init_db()
    login_manager.init_app(app)

    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.cases import cases_bp
    from app.routes.evidence import evidence_bp
    from app.routes.playbooks import playbooks_bp
    from app.routes.analysts import analysts_bp
    from app.routes.tools import tools_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(cases_bp)
    app.register_blueprint(evidence_bp)
    app.register_blueprint(playbooks_bp)
    app.register_blueprint(analysts_bp)
    app.register_blueprint(tools_bp)

    return app
