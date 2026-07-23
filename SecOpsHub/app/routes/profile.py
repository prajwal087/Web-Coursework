from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.services import AnalystService, ActivityService
from app.helpers import validate_password_change, flash_errors

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')


@profile_bp.route('/')
@login_required
def index():
    cases = AnalystService.get_cases_by_analyst(current_user.id)
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

    if not current_user.check_password(current_pw):
        flash('Current password is incorrect', 'error')
        return redirect(url_for('profile.index'))

    try:
        current_user.set_password(new_pw)
        AnalystService.update_analyst_password(current_user.id, current_user.password_hash)
        ActivityService.log_activity(
            current_user.id, 'password_change',
            f'User {current_user.username} changed their password', request.remote_addr
        )
        flash('Password updated successfully', 'success')
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error changing password: {str(e)}")
        flash('An error occurred while updating password', 'error')
    return redirect(url_for('profile.index'))
