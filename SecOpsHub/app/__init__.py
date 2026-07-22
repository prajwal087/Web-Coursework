from functools import wraps
import logging
from logging.handlers import RotatingFileHandler
import os
import time
import secrets

from flask import Flask, flash, redirect, url_for, render_template, request, abort, jsonify, session as flask_session
from flask_login import LoginManager, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

from datetime import datetime
from app.database import init_db, get_db
from app.models.analyst import Analyst

# Configure logging
def setup_logging(app):
    """Setup application logging"""
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    file_handler = RotatingFileHandler('logs/secops_hub.log', maxBytes=10240000, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('SecOpsHub startup')


login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page'
login_manager.login_message_category = 'warning'

csrf = CSRFProtect()

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)


@login_manager.user_loader
def load_user(user_id):
    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM analysts WHERE id = %s", (int(user_id),))
            row = cur.fetchone()
        conn.close()
        return Analyst.from_row(row)
    except Exception as e:
        app.logger.error(f"Error loading user {user_id}: {str(e)}")
        return None


def role_required(*roles):
    """Decorator to require specific roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                app.logger.warning(
                    f"Access denied for user {current_user.id if current_user.is_authenticated else 'anonymous'} - required roles: {roles}"
                )
                flash('You do not have permission to access this page', 'error')
                return redirect(url_for('dashboard.index')), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def create_app():
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object('config.Config')
    
    # Setup logging
    setup_logging(app)
    
    # Initialize database
    try:
        init_db()
        app.logger.info("Database initialized successfully")
    except Exception as e:
        app.logger.error(f"Database initialization error: {str(e)}")
        raise
    
    # Initialize extensions
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    
    # Request timing middleware
    @app.before_request
    def start_timer():
        request._start_time = time.time()
    
    @app.after_request
    def log_request_duration(response):
        if hasattr(request, '_start_time'):
            elapsed = time.time() - request._start_time
            app.logger.info(f"{request.method} {request.path} -> {response.status_code} ({elapsed:.3f}s)")
        return response
    
    # HTTPS redirect middleware
    @app.before_request
    def redirect_https():
        if not request.is_secure and not app.debug and not app.config.get('TESTING'):
            host = request.host.split(':')[0]
            if host in ('localhost', '127.0.0.1', '::1'):
                return
            url = request.url.replace('http://', 'https://', 1)
            return redirect(url, 301)
    
    # Session fingerprint middleware
    @app.before_request
    def check_session_fingerprint():
        if current_user.is_authenticated and request.endpoint and 'static' not in request.endpoint:
            stored_ip = flask_session.get('_fingerprint_ip')
            stored_ua = flask_session.get('_fingerprint_ua')
            if stored_ip and stored_ua:
                current_ip = request.remote_addr or ''
                current_ua = request.user_agent.string if request.user_agent else ''
                if stored_ip != current_ip or stored_ua != current_ua:
                    app.logger.warning(f"Session fingerprint mismatch for user {current_user.id}")
                    from flask_login import logout_user
                    logout_user()
                    flask_session.clear()
                    flash('Session expired due to security change', 'warning')
                    return redirect(url_for('auth.login'))
    
    # Generate CSP nonce per request
    @app.before_request
    def generate_nonce():
        request.csp_nonce = secrets.token_hex(16)
    
    # Security headers middleware
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        nonce = getattr(request, 'csp_nonce', '')
        response.headers['Content-Security-Policy'] = (
            f"default-src 'self'; "
            f"script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com https://code.jquery.com; "
            f"style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            f"font-src 'self' https://cdn.jsdelivr.net; "
            f"img-src 'self' data:; "
            f"connect-src 'self'; "
            f"frame-ancestors 'none'"
        )
        return response
    
    # Set session fingerprint on login
    @app.before_request
    def set_fingerprint():
        if current_user.is_authenticated and not flask_session.get('_fingerprint_ip'):
            flask_session['_fingerprint_ip'] = request.remote_addr or ''
            flask_session['_fingerprint_ua'] = request.user_agent.string if request.user_agent else ''
    
    # Error handlers
    @app.errorhandler(400)
    def bad_request(e):
        app.logger.warning(f"400 Bad Request: {request.path}")
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({'error': 'Bad request'}), 400
        flash('Invalid request. Please check your input.', 'error')
        return render_template('errors/400.html'), 400
    
    @app.errorhandler(403)
    def forbidden(e):
        app.logger.warning(f"403 Forbidden: {request.path}")
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({'error': 'Forbidden'}), 403
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(404)
    def not_found(e):
        app.logger.warning(f"404 Not Found: {request.path}")
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({'error': 'Not found'}), 404
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(405)
    def method_not_allowed(e):
        app.logger.warning(f"405 Method Not Allowed: {request.method} {request.path}")
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({'error': 'Method not allowed'}), 405
        flash('Method not allowed.', 'error')
        return render_template('errors/405.html'), 405
    
    @app.errorhandler(413)
    def payload_too_large(e):
        app.logger.warning(f"413 Payload Too Large: {request.path}")
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({'error': 'Payload too large'}), 413
        flash('Upload size exceeds the limit.', 'error')
        return render_template('errors/413.html'), 413
    
    @app.errorhandler(500)
    def server_error(e):
        app.logger.error(f"500 Server Error: {str(e)}", exc_info=True)
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(429)
    def ratelimit_handler(e):
        app.logger.warning(f"Rate limit exceeded: {request.remote_addr}")
        flash('Too many requests. Please try again later.', 'error')
        return render_template('errors/429.html'), 429
    
    # Template filter for safe date formatting
    @app.template_filter('datetimeformat')
    def datetimeformat_filter(value, fmt='%Y-%m-%d %H:%M'):
        if value is None:
            return ''
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except (ValueError, TypeError):
                return value
        return value.strftime(fmt)

    # Template filter for sequential display numbering
    @app.template_filter('row_number')
    def row_number_filter(loop_index, page=None, per_page=10):
        if page is None or page < 2:
            return loop_index
        return (page - 1) * per_page + loop_index

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.cases import cases_bp
    from app.routes.evidence import evidence_bp
    from app.routes.playbook import playbooks_bp
    from app.routes.analysts import analysts_bp
    from app.routes.tools import tools_bp
    from app.routes.admin import admin_bp
    from app.routes.profile import profile_bp
    from app.routes.api import api_bp
    
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(cases_bp)
    app.register_blueprint(evidence_bp)
    app.register_blueprint(playbooks_bp)
    app.register_blueprint(analysts_bp)
    app.register_blueprint(tools_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(profile_bp)
    
    app.logger.info("Application created successfully")
    return app
