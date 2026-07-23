from flask import Blueprint, render_template, request, redirect, url_for, flash, session as flask_session
from flask_login import login_user, logout_user, login_required, current_user
from app.services import AnalystService, ActivityService
from app import limiter
from app.helpers import validate_analyst, flash_errors, is_account_locked, record_login_attempt
from config import Config
import logging

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            ip = request.remote_addr or ''

            if not username or not password:
                flash('Username and password are required', 'error')
                return render_template('auth/login.html'), 400

            if is_account_locked(username, ip, Config.MAX_LOGIN_ATTEMPTS, Config.ACCOUNT_LOCKOUT_MINUTES):
                flash('Account temporarily locked due to too many failed attempts. Try again later.', 'error')
                logger.warning(f"Locked login attempt for user: {username} from {ip}")
                return render_template('auth/login.html'), 429

            analyst = AnalystService.get_analyst_by_username(username)
            if analyst and analyst.check_password(password):
                record_login_attempt(username, ip, success=True)
                flask_session.permanent = True
                flask_session['_fingerprint_ip'] = ip
                flask_session['_fingerprint_ua'] = request.user_agent.string if request.user_agent else ''
                login_user(analyst)
                logger.info(f"User {username} logged in successfully")
                return redirect(url_for('dashboard.index'))

            record_login_attempt(username, ip, success=False)
            logger.warning(f"Failed login attempt for user: {username} from {ip}")
            flash('Invalid credentials', 'error')
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            flash('An error occurred during login', 'error')

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def register():
    if request.method == 'POST':
        try:
            errors = validate_analyst(request.form, require_password=True)
            if errors:
                flash_errors(errors)
                return render_template('auth/register.html'), 400

            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')

            if AnalystService.check_duplicate(username, email):
                flash('Username or email already exists', 'error')
                return render_template('auth/register.html'), 400

            AnalystService.create_analyst_with_password(username, email, password, 'analyst')
            logger.info(f"New analyst registered: {username}")
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            flash('An error occurred during registration', 'error')

    return render_template('auth/register.html')


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    username = current_user.username if current_user.is_authenticated else 'unknown'
    logger.info(f"User logged out: {username}")
    logout_user()
    return redirect(url_for('auth.login'))
