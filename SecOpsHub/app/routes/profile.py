from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.case import Case
from app.database import get_db
from app.helpers import log_activity, validate_password_change, flash_errors

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')


@profile_bp.route('/')
@login_required
def index():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM cases WHERE analyst_id = %s ORDER BY created_at DESC",
                (current_user.id,)
            )
            cases = [Case.from_row(r) for r in cur.fetchall()]
    finally:
        conn.close()
    return render_template('profile/index.html', cases=cases)


@profile_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    errors = validate_password_change(request.form)
    if errors:
        flash_errors(errors)
        return redirect(url_for('profile.index'))

    current_pw = request.form.get('current_password', '')
    new_pw = request.form.get('new_password', '')
    confirm_pw = request.form.get('confirm_password', '')

    if not current_user.check_password(current_pw):
        flash('Current password is incorrect', 'error')
        return redirect(url_for('profile.index'))

    conn = get_db()
    try:
        with conn.cursor() as cur:
            current_user.set_password(new_pw)
            cur.execute(
                "UPDATE analysts SET password_hash = %s WHERE id = %s",
                (current_user.password_hash, current_user.id)
            )
        conn.commit()
        log_activity('password_change', f'User {current_user.username} changed their password')
        flash('Password updated successfully', 'success')
    finally:
        conn.close()
    return redirect(url_for('profile.index'))
