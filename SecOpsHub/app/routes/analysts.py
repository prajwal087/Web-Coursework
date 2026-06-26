from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models.analyst import Analyst
from app.models.case import Case
from app.database import get_db
from app import role_required
from app.helpers import log_activity, validate_analyst, flash_errors, paginate

analysts_bp = Blueprint('analysts', __name__, url_prefix='/analysts')


@analysts_bp.route('/')
@login_required
def list_view():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '').strip()
    conn = get_db()
    try:
        with conn.cursor() as cur:
            if q:
                where = "WHERE a.username LIKE %s OR a.email LIKE %s"
                like = f'%{q}%'
                params = (like, like)
            else:
                where = ""
                params = None
            rows, total_pages, current_page, total_items = paginate(
                cur,
                f"""
                SELECT a.*, COUNT(c.id) AS case_count
                FROM analysts a LEFT JOIN cases c ON c.analyst_id = a.id {where}
                GROUP BY a.id ORDER BY a.created_at DESC
                """,
                f"SELECT COUNT(*) FROM analysts a {where}",
                page, params
            )
        analysts = []
        for r in rows:
            analyst = Analyst.from_row(r)
            analyst.cases = [None] * (r['case_count'] or 0)
            analysts.append(analyst)
    finally:
        conn.close()
    return render_template('analysts/list.html', analysts=analysts, page=current_page, total_pages=total_pages, total_items=total_items, search_query=q)


@analysts_bp.route('/<int:id>')
@login_required
def view(id):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM analysts WHERE id = %s", (id,))
            analyst = Analyst.from_row(cur.fetchone())
        if analyst is None:
            flash('Analyst not found', 'error')
            return redirect(url_for('analysts.list_view'))
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM cases WHERE analyst_id = %s ORDER BY created_at DESC", (id,))
            analyst.cases = [Case.from_row(r) for r in cur.fetchall()]
    finally:
        conn.close()
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
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM analysts WHERE username = %s OR email = %s",
                    (username, email)
                )
                if cur.fetchone():
                    flash('Username or email already exists', 'error')
                    return render_template('analysts/form.html', analyst=None)
                analyst_obj = Analyst(None, username, email, '', role)
                analyst_obj.set_password(password)
                cur.execute(
                    "INSERT INTO analysts (username, email, password_hash, role, created_at) VALUES (%s, %s, %s, %s, %s)",
                    (username, email, analyst_obj.password_hash, role, datetime.utcnow())
                )
                analyst_id = cur.lastrowid
            conn.commit()
            log_activity('analyst_created', f'Analyst #{analyst_id}: {username}')
            flash('Analyst created', 'success')
            return redirect(url_for('analysts.view', id=analyst_id))
        finally:
            conn.close()
    return render_template('analysts/form.html', analyst=None)

