from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models.analyst import Analyst
from app.models.case import Case
from app.database import get_db

analysts_bp = Blueprint('analysts', __name__, url_prefix='/analysts')


@analysts_bp.route('/')
@login_required
def list_view():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM analysts ORDER BY created_at DESC")
            rows = cur.fetchall()
        analysts = []
        for r in rows:
            analyst = Analyst.from_row(r)
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS cnt FROM cases WHERE analyst_id = %s", (r['id'],))
                analyst.cases = [None] * cur.fetchone()['cnt']
            analysts.append(analyst)
    finally:
        conn.close()
    return render_template('analysts/list.html', analysts=analysts)
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
