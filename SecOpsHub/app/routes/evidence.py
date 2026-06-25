from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models.evidence import Evidence
from app.models.case import Case
from app.database import get_db
from app.helpers import log_activity, validate_evidence, flash_errors, paginate

evidence_bp = Blueprint('evidence', __name__, url_prefix='/evidence')


@evidence_bp.route('/')
@login_required
def list():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '').strip()
    conn = get_db()
    try:
        with conn.cursor() as cur:
            if q:
                where = "WHERE title LIKE %s OR source LIKE %s"
                like = f'%{q}%'
                params = (like, like)
            else:
                where = ""
                params = None
            rows, total_pages, current_page, total_items = paginate(
                cur,
                f"SELECT * FROM evidence {where} ORDER BY created_at DESC",
                f"SELECT COUNT(*) FROM evidence {where}",
                page, params
            )
            evidence_list = [Evidence.from_row(r) for r in rows]
    finally:
        conn.close()
    return render_template('evidence/list.html', evidence_list=evidence_list, page=current_page, total_pages=total_pages, total_items=total_items, search_query=q)


@evidence_bp.route('/<int:id>')
@login_required
def view(id):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM evidence WHERE id = %s", (id,))
            evidence = Evidence.from_row(cur.fetchone())
    finally:
        conn.close()
    if evidence is None:
        flash('Evidence not found', 'error')
        return redirect(url_for('evidence.list'))
    return render_template('evidence/view.html', evidence=evidence)


@evidence_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    case_id = request.args.get('case_id')
    conn = get_db()
    try:
        if request.method == 'POST':
            errors = validate_evidence(request.form)
            if errors:
                flash_errors(errors)
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM cases")
                    cases = [Case.from_row(r) for r in cur.fetchall()]
                return render_template('evidence/form.html', evidence=None, cases=cases,
                                       preselected_case_id=request.form.get('case_id'))
            title = request.form['title'].strip()
            content = request.form['content'].strip()
            source = request.form.get('source', 'manual').strip()
            case_id = request.form['case_id'].strip()
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO evidence (title, content, source, case_id) VALUES (%s, %s, %s, %s)",
                    (title, content, source, case_id)
                )
                evidence_id = cur.lastrowid
            conn.commit()
            log_activity('evidence_added', f'Evidence #{evidence_id}: {title}')
            flash('Evidence added', 'success')
            return redirect(url_for('evidence.view', id=evidence_id))
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM cases")
            cases = [Case.from_row(r) for r in cur.fetchall()]
    finally:
        conn.close()
    return render_template('evidence/form.html', evidence=None, cases=cases,
                           preselected_case_id=case_id)

