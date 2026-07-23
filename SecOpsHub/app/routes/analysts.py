from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.services import AnalystService, ActivityService
from app import role_required
from app.helpers import validate_analyst, flash_errors

analysts_bp = Blueprint('analysts', __name__, url_prefix='/analysts')


@analysts_bp.route('/')
@login_required
def list_view():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '').strip()
    try:
        analysts, total_pages, current_page, total_items = AnalystService.get_all_analysts_paginated(
            page=page, search_query=q if q else None
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error listing analysts: {str(e)}")
        flash('An error occurred while loading analysts', 'error')
        return redirect(url_for('dashboard.index'))
    return render_template('analysts/list.html', analysts=analysts,
                           page=current_page, total_pages=total_pages,
                           total_items=total_items, search_query=q)


@analysts_bp.route('/<int:id>')
@login_required
def view(id):
    analyst = AnalystService.get_analyst_with_cases(id)
    if analyst is None:
        flash('Analyst not found', 'error')
        return redirect(url_for('analysts.list_view'))
    return render_template('analysts/view.html', analyst=analyst)


@analysts_bp.route('/new', methods=['GET', 'POST'])
@login_required
@role_required('lead')
def new():
    if request.method == 'POST':
        errors = validate_analyst(request.form, require_password=True)
        if errors:
            flash_errors(errors)
            return render_template('analysts/form.html', analyst=None)
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        role = request.form.get('role', 'analyst').strip()
        try:
            if AnalystService.check_duplicate(username, email):
                flash('Username or email already exists', 'error')
                return render_template('analysts/form.html', analyst=None)
            analyst_id = AnalystService.create_analyst_with_password(username, email, password, role)
            ActivityService.log_activity(
                current_user.id, 'analyst_created',
                f'Analyst #{analyst_id}: {username}', request.remote_addr
            )
            flash('Analyst created', 'success')
            return redirect(url_for('analysts.view', id=analyst_id))
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error creating analyst: {str(e)}")
            flash('An error occurred while creating analyst', 'error')
    return render_template('analysts/form.html', analyst=None)


@analysts_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('lead')
def edit(id):
    analyst = AnalystService.get_analyst_by_id(id)
    if analyst is None:
        flash('Analyst not found', 'error')
        return redirect(url_for('analysts.list_view'))
    if request.method == 'POST':
        errors = validate_analyst(request.form, require_password=False)
        if errors:
            flash_errors(errors)
            return render_template('analysts/form.html', analyst=analyst)
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        role = request.form.get('role', 'analyst').strip()
        password = request.form.get('password') or None
        try:
            AnalystService.update_analyst(id, username, email, role, password)
            ActivityService.log_activity(
                current_user.id, 'analyst_updated',
                f'Analyst #{id}: {username}', request.remote_addr
            )
            flash('Analyst updated', 'success')
            return redirect(url_for('analysts.view', id=id))
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error updating analyst: {str(e)}")
            flash('An error occurred while updating analyst', 'error')
    return render_template('analysts/form.html', analyst=analyst)


@analysts_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@role_required('lead')
def delete(id):
    try:
        AnalystService.delete_analyst(id)
        ActivityService.log_activity(
            current_user.id, 'analyst_deleted',
            f'Analyst #{id}', request.remote_addr
        )
        flash('Analyst deleted', 'success')
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error deleting analyst: {str(e)}")
        flash('An error occurred while deleting analyst', 'error')
    return redirect(url_for('analysts.list_view'))
