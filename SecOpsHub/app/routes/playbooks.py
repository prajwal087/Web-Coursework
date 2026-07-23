import json
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.services import PlaybookService, ActivityService
from app.helpers import validate_playbook, flash_errors

playbooks_bp = Blueprint('playbooks', __name__, url_prefix='/playbooks')


@playbooks_bp.route('/')
@login_required
def list():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '').strip()
    try:
        playbooks, total_pages, current_page, total_items = PlaybookService.get_all_playbooks(
            page=page, search_query=q if q else None
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error listing playbooks: {str(e)}")
        flash('An error occurred while loading playbooks', 'error')
        return redirect(url_for('dashboard.index'))
    return render_template('playbooks/list.html', playbooks=playbooks,
                           page=current_page, total_pages=total_pages,
                           total_items=total_items, search_query=q)


@playbooks_bp.route('/<int:id>')
@login_required
def view(id):
    playbook = PlaybookService.get_playbook_by_id(id)
    if playbook is None:
        flash('Playbook not found', 'error')
        return redirect(url_for('playbooks.list'))
    steps = json.loads(playbook.steps)
    return render_template('playbooks/view.html', playbook=playbook, steps=steps)


@playbooks_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if request.method == 'POST':
        errors = validate_playbook(request.form)
        if errors:
            flash_errors(errors)
            return render_template('playbooks/form.html', playbook=None)
        name = request.form['name'].strip()
        description = request.form.get('description', '').strip()
        steps_raw = request.form.get('steps', '[]')
        try:
            steps = json.loads(steps_raw)
        except json.JSONDecodeError:
            steps = [s.strip() for s in steps_raw.split('\n') if s.strip()]
        try:
            playbook_id = PlaybookService.create_playbook(name, description, steps)
            ActivityService.log_activity(
                current_user.id, 'playbook_created',
                f'Playbook #{playbook_id}: {name}', request.remote_addr
            )
            flash('Playbook created', 'success')
            return redirect(url_for('playbooks.view', id=playbook_id))
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error creating playbook: {str(e)}")
            flash('An error occurred while creating playbook', 'error')
    return render_template('playbooks/form.html', playbook=None)


@playbooks_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    playbook = PlaybookService.get_playbook_by_id(id)
    if playbook is None:
        flash('Playbook not found', 'error')
        return redirect(url_for('playbooks.list'))
    if request.method == 'POST':
        errors = validate_playbook(request.form)
        if errors:
            flash_errors(errors)
            steps = json.loads(playbook.steps)
            return render_template('playbooks/form.html', playbook=playbook, steps=steps)
        name = request.form['name'].strip()
        description = request.form.get('description', '').strip()
        steps_raw = request.form.get('steps', '[]')
        try:
            steps = json.loads(steps_raw)
        except json.JSONDecodeError:
            steps = [s.strip() for s in steps_raw.split('\n') if s.strip()]
        try:
            PlaybookService.update_playbook(id, name, description, steps)
            ActivityService.log_activity(
                current_user.id, 'playbook_updated',
                f'Playbook #{id}: {name}', request.remote_addr
            )
            flash('Playbook updated', 'success')
            return redirect(url_for('playbooks.view', id=id))
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error updating playbook: {str(e)}")
            flash('An error occurred while updating playbook', 'error')
    steps = json.loads(playbook.steps)
    return render_template('playbooks/form.html', playbook=playbook, steps=steps)


@playbooks_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    try:
        PlaybookService.delete_playbook(id)
        ActivityService.log_activity(
            current_user.id, 'playbook_deleted',
            f'Playbook #{id}', request.remote_addr
        )
        flash('Playbook deleted', 'success')
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error deleting playbook: {str(e)}")
        flash('An error occurred while deleting playbook', 'error')
    return redirect(url_for('playbooks.list'))
