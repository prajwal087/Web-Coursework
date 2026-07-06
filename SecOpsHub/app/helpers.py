import re
from functools import wraps
from flask import flash, request, render_template
from flask_login import current_user
from markupsafe import escape

from app.database import get_db
from app.validators import PasswordValidator, EmailValidator, UsernameValidator

VALID_SEVERITIES = {'low', 'medium', 'high', 'critical'}
VALID_STATUSES = {'open', 'in_progress', 'resolved', 'closed'}
VALID_ROLES = {'analyst', 'lead'}
VALID_SOURCES = {'manual', 'ip_intel', 'port_scan', 'password_analyzer', 'cve_feed'}


def sanitize_input(text):
    """Sanitize user input to prevent XSS attacks"""
    if not text:
        return text
    return str(escape(text.strip()))


def validate_form(validator_func, template, *extra_template_args):
    """Decorator that validates form data using a validator function."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if request.method == 'POST':
                errors = validator_func(request.form)
                if errors:
                    flash_errors(errors)
                    return render_template(template, *extra_template_args, **kwargs), 400
            return f(*args, **kwargs)
        return wrapper
    return decorator


def is_account_locked(username, ip_address, max_attempts=10, window_minutes=10):
    """Check if an account is temporarily locked due to too many failed attempts."""
    from app.database import get_db
    from datetime import datetime, timedelta, timezone
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
            cur.execute("""
                SELECT COUNT(*) AS cnt FROM login_attempts
                WHERE (username = %s OR ip_address = %s)
                  AND attempted_at > %s
                  AND success = 0
            """, (username, ip_address, cutoff))
            row = cur.fetchone()
            return (row['cnt'] or 0) >= max_attempts
    finally:
        conn.close()


def record_login_attempt(username, ip_address, success=False):
    """Record a login attempt in the database."""
    from app.database import get_db
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO login_attempts (username, ip_address, success) VALUES (%s, %s, %s)",
                (username, ip_address, 1 if success else 0)
            )
        conn.commit()
    finally:
        conn.close()


def validate_case(data):
    errors = []
    title = data.get('title', '').strip()
    if not title:
        errors.append('Title is required')
    else:
        title = sanitize_input(title)
        if len(title) > 200:
            errors.append('Title must be 200 characters or fewer')
    
    severity = data.get('severity', '').strip().lower()
    if severity not in VALID_SEVERITIES:
        errors.append(f'Invalid severity. Must be one of: {", ".join(sorted(VALID_SEVERITIES))}')
    return errors


def validate_analyst(data, require_password=True):
    errors = []
    
    # Validate username
    username = data.get('username', '').strip()
    valid, msg = UsernameValidator.validate(username)
    if not valid:
        errors.append(msg)
    else:
        username = sanitize_input(username)
    
    # Validate email
    email = data.get('email', '').strip()
    valid, msg = EmailValidator.validate(email)
    if not valid:
        errors.append(msg)
    else:
        email = sanitize_input(email)
    
    # Validate password
    password = data.get('password', '')
    if require_password:
        if not password:
            errors.append('Password is required')
        else:
            valid, msg = PasswordValidator.validate(password)
            if not valid:
                errors.append(msg)
    elif password:  # Optional password check if provided
        valid, msg = PasswordValidator.validate(password)
        if not valid:
            errors.append(msg)
    
    # Validate role
    role = data.get('role', '').strip().lower()
    if role and role not in VALID_ROLES:
        errors.append(f'Invalid role. Must be one of: {", ".join(sorted(VALID_ROLES))}')
    
    return errors


def validate_evidence(data):
    errors = []
    title = data.get('title', '').strip()
    if not title:
        errors.append('Title is required')
    elif len(sanitize_input(title)) > 200:
        errors.append('Title must be 200 characters or fewer')

    content = data.get('content', '').strip()
    if not content:
        errors.append('Content is required')
    else:
        content = sanitize_input(content)
    
    source = data.get('source', '').strip().lower()
    if source not in VALID_SOURCES:
        errors.append(f'Invalid source. Must be one of: {", ".join(sorted(VALID_SOURCES))}')
    return errors


def validate_playbook(data):
    errors = []
    name = data.get('name', '').strip()
    if not name:
        errors.append('Name is required')
    elif len(name) > 200:
        errors.append('Name must be 200 characters or fewer')
    else:
        name = sanitize_input(name)
    return errors


def validate_password_change(data):
    errors = []
    current_pw = data.get('current_password', '')
    if not current_pw:
        errors.append('Current password is required')
    
    new_pw = data.get('new_password', '')
    if not new_pw:
        errors.append('New password is required')
    else:
        valid, msg = PasswordValidator.validate(new_pw)
        if not valid:
            errors.append(msg)
    
    confirm = data.get('confirm_password', '')
    if new_pw and confirm != new_pw:
        errors.append('Passwords do not match')
    return errors


def flash_errors(errors):
    for e in errors:
        flash(e, 'error')


ITEMS_PER_PAGE = 10


def paginate(cur, base_query, count_query, page, params=None):
    page = max(1, page)
    offset = (page - 1) * ITEMS_PER_PAGE
    if params is None:
        cur.execute(count_query)
        total = list(cur.fetchone().values())[0]
        cur.execute(base_query + " LIMIT %s OFFSET %s", (ITEMS_PER_PAGE, offset))
    else:
        cur.execute(count_query, params)
        total = list(cur.fetchone().values())[0]
        cur.execute(base_query + " LIMIT %s OFFSET %s", (*params, ITEMS_PER_PAGE, offset))
    rows = cur.fetchall()
    total_pages = max(1, (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    return rows, total_pages, page, total


def log_activity(action, details=''):
    if not current_user.is_authenticated:
        return
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO activity_log (analyst_id, action, details) VALUES (%s, %s, %s)",
                (current_user.id, action, details)
            )
        conn.commit()
    except Exception as e:
        import logging
        logging.error(f"Error logging activity: {str(e)}")
    finally:
        conn.close()
