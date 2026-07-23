from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.services import CaseService, EvidenceService, ActivityService
from app.helpers import validate_evidence, flash_errors

evidence_bp = Blueprint('evidence', __name__, url_prefix='/evidence')


@evidence_bp.route('/')
@login_required
def list():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '').strip()
    try:
        evidence_list, total_pages, current_page, total_items = EvidenceService.get_all_evidence(
            page=page, search_query=q if q else None
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error listing evidence: {str(e)}")
        flash('An error occurred while loading evidence', 'error')
        return redirect(url_for('dashboard.index'))
    return render_template('evidence/list.html', evidence_list=evidence_list,
                           page=current_page, total_pages=total_pages,
                           total_items=total_items, search_query=q)


@evidence_bp.route('/<int:id>')
@login_required
def view(id):
    evidence = EvidenceService.get_evidence_by_id(id)
    if evidence is None:
        flash('Evidence not found', 'error')
        return redirect(url_for('evidence.list'))
    return render_template('evidence/view.html', evidence=evidence)


@evidence_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    preselected_case_id = request.args.get('case_id')
    if request.method == 'POST':
        errors = validate_evidence(request.form)
        if errors:
            flash_errors(errors)
            cases = EvidenceService.get_all_cases_basic()
            return render_template('evidence/form.html', evidence=None, cases=cases,
                                   preselected_case_id=request.form.get('case_id'))
        title = request.form['title'].strip()
        content = request.form['content'].strip()
        source = request.form.get('source', 'manual').strip()
        case_id = request.form['case_id'].strip()
        try:
            case = CaseService.get_case_by_id(int(case_id))
        except (ValueError, TypeError):
            case = None
        if case is None:
            flash('Case not found', 'error')
            cases = EvidenceService.get_all_cases_basic()
            return render_template('evidence/form.html', evidence=None, cases=cases,
                                   preselected_case_id=case_id)
        try:
            evidence_id = EvidenceService.add_evidence(case_id, title, content, source)
            ActivityService.log_activity(
                current_user.id, 'evidence_added',
                f'Evidence #{evidence_id}: {title}', request.remote_addr
            )
            flash('Evidence added', 'success')
            return redirect(url_for('evidence.view', id=evidence_id))
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error creating evidence: {str(e)}")
            flash('An error occurred while adding evidence', 'error')
    cases = EvidenceService.get_all_cases_basic()
    return render_template('evidence/form.html', evidence=None, cases=cases,
                           preselected_case_id=preselected_case_id)


@evidence_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    evidence = EvidenceService.get_evidence_by_id(id)
    if evidence is None:
        flash('Evidence not found', 'error')
        return redirect(url_for('evidence.list'))
    if request.method == 'POST':
        errors = validate_evidence(request.form)
        if errors:
            flash_errors(errors)
            cases = EvidenceService.get_all_cases_basic()
            return render_template('evidence/form.html', evidence=evidence, cases=cases,
                                   preselected_case_id=evidence.case_id)
        title = request.form['title'].strip()
        content = request.form['content'].strip()
        source = request.form.get('source', 'manual').strip()
        case_id = request.form['case_id'].strip()
        try:
            EvidenceService.update_evidence(id, title, content, source, case_id)
            ActivityService.log_activity(
                current_user.id, 'evidence_updated',
                f'Evidence #{id}: {title}', request.remote_addr
            )
            flash('Evidence updated', 'success')
            return redirect(url_for('evidence.view', id=id))
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error updating evidence: {str(e)}")
            flash('An error occurred while updating evidence', 'error')
    cases = EvidenceService.get_all_cases_basic()
    return render_template('evidence/form.html', evidence=evidence, cases=cases,
                           preselected_case_id=evidence.case_id)


@evidence_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    evidence = EvidenceService.get_evidence_by_id(id)
    if evidence:
        try:
            EvidenceService.delete_evidence(id)
            ActivityService.log_activity(
                current_user.id, 'evidence_deleted',
                f'Evidence #{id}', request.remote_addr
            )
            flash('Evidence deleted', 'success')
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error deleting evidence: {str(e)}")
            flash('An error occurred while deleting evidence', 'error')
    return redirect(url_for('evidence.list'))
