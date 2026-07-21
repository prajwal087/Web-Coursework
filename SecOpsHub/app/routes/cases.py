from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.services import CaseService, ActivityService
from app.helpers import validate_case, flash_errors, sanitize_input
import logging

logger = logging.getLogger(__name__)
cases_bp = Blueprint('cases', __name__, url_prefix='/cases')


@cases_bp.route('/')
@login_required
def list():
    try:
        page = request.args.get('page', 1, type=int)
        q = request.args.get('q', '').strip()
        
        rows, total_pages, current_page, total_items = CaseService.get_all_cases(
            page=page,
            search_query=q if q else None
        )
        
        if q:
            ActivityService.log_activity(
                current_user.id,
                'view_cases_list',
                f'Viewed cases list (search: {q})',
                request.remote_addr
            )
        
        return render_template(
            'cases/list.html',
            cases=rows,
            page=current_page,
            total_pages=total_pages,
            total_items=total_items,
            search_query=q
        )
    except Exception as e:
        logger.error(f"Error listing cases: {str(e)}")
        flash('An error occurred while loading cases', 'error')
        return redirect(url_for('dashboard.index'))


@cases_bp.route('/<int:id>')
@login_required
def view(id):
    try:
        case = CaseService.get_case_by_id(id)
        if not case:
            flash('Case not found', 'error')
            return redirect(url_for('cases.list'))

        tasks = CaseService.get_tasks_for_case(id)
        available_playbooks = CaseService.get_available_playbooks(id)

        ActivityService.log_activity(
            current_user.id,
            'view_case_details',
            f'Viewed case #{id}',
            request.remote_addr
        )

        return render_template('cases/view.html', case=case, tasks=tasks, available_playbooks=available_playbooks)
    except Exception as e:
        logger.error(f"Error viewing case {id}: {str(e)}")
        flash('An error occurred while loading the case', 'error')
        return redirect(url_for('cases.list'))


@cases_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if request.method == 'POST':
        try:
            errors = validate_case(request.form)
            if errors:
                flash_errors(errors)
                return render_template('cases/form.html', case=None)
            
            title = sanitize_input(request.form['title'])
            description = sanitize_input(request.form.get('description', ''))
            severity = request.form['severity'].strip().lower()
            
            CaseService.create_case(title, description, severity, current_user.id)
            
            ActivityService.log_activity(
                current_user.id,
                'case_created',
                f'Created case: {title}',
                request.remote_addr
            )
            
            flash('Case created successfully', 'success')
            return redirect(url_for('cases.list'))
        except Exception as e:
            logger.error(f"Error creating case: {str(e)}")
            flash('An error occurred while creating the case', 'error')
            return render_template('cases/form.html', case=None)
    
    return render_template('cases/form.html', case=None)


@cases_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    try:
        case = CaseService.get_case_by_id(id)
        if not case:
            flash('Case not found', 'error')
            return redirect(url_for('cases.list'))
        
        if request.method == 'POST':
            errors = validate_case(request.form)
            if errors:
                flash_errors(errors)
                return render_template('cases/form.html', case=case)
            
            title = sanitize_input(request.form['title'])
            description = sanitize_input(request.form.get('description', ''))
            severity = request.form['severity'].strip().lower()
            status = request.form.get('status', 'open').strip().lower()
            
            CaseService.update_case(id, title, description, severity, status)
            
            ActivityService.log_activity(
                current_user.id,
                'case_updated',
                f'Updated case #{id}: {title}',
                request.remote_addr
            )
            
            flash('Case updated successfully', 'success')
            return redirect(url_for('cases.view', id=id))
        
        return render_template('cases/form.html', case=case)
    except Exception as e:
        logger.error(f"Error editing case {id}: {str(e)}")
        flash('An error occurred while editing the case', 'error')
        return redirect(url_for('cases.list'))


@cases_bp.route('/<int:id>/apply-playbook', methods=['POST'])
@login_required
def apply_playbook(id):
    playbook_id = request.form.get('playbook_id', type=int)
    if not playbook_id:
        flash('No playbook selected', 'error')
        return redirect(url_for('cases.view', id=id))
    try:
        CaseService.apply_playbook_to_case(id, playbook_id)
        ActivityService.log_activity(
            current_user.id, 'playbook_applied',
            f'Applied playbook #{playbook_id} to case #{id}', request.remote_addr
        )
        flash('Playbook applied successfully', 'success')
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        logger.error(f"Error applying playbook: {str(e)}")
        flash('An error occurred while applying the playbook', 'error')
    return redirect(url_for('cases.view', id=id))


@cases_bp.route('/<int:id>/tasks/<int:task_id>/toggle', methods=['POST'])
@login_required
def toggle_task(id, task_id):
    try:
        is_complete = request.form.get('is_complete') == '1'
        CaseService.toggle_task(task_id, is_complete)
        ActivityService.log_activity(
            current_user.id, 'task_toggled',
            f'Task #{task_id} toggled to {"complete" if is_complete else "incomplete"} in case #{id}',
            request.remote_addr
        )
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return {'success': True}
        flash('Task updated', 'success')
    except Exception as e:
        logger.error(f"Error toggling task {task_id}: {str(e)}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return {'success': False, 'error': str(e)}, 500
        flash('An error occurred while updating the task', 'error')
    return redirect(url_for('cases.view', id=id))


@cases_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    try:
        CaseService.delete_case(id)
        
        ActivityService.log_activity(
            current_user.id,
            'case_deleted',
            f'Deleted case #{id}',
            request.remote_addr
        )
        
        flash('Case deleted successfully', 'success')
    except Exception as e:
        logger.error(f"Error deleting case {id}: {str(e)}")
        flash('An error occurred while deleting the case', 'error')
    
    return redirect(url_for('cases.list'))
