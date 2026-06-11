from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.case import Case
from app.models.analyst import Analyst
from app.models.evidence import Evidence
from app.database import get_db

cases_bp = Blueprint('cases', __name__, url_prefix='/cases')


@cases_bp.route('/')
@login_required
def list():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.*, a.id AS analyst_id2, a.username, a.email, a.password_hash, a.role, a.created_at AS analyst_created_at
                FROM cases c JOIN analysts a ON c.analyst_id = a.id
                ORDER BY c.updated_at DESC
            """)
            rows = cur.fetchall()
        cases = []
        for r in rows:
            case = Case.from_row(r)
            analyst = Analyst(
                id=r['analyst_id2'], username=r['username'], email=r['email'],
                password_hash=r['password_hash'], role=r['role'], created_at=r['analyst_created_at']
            )
            case.analyst = analyst
            cases.append(case)
    finally:
        conn.close()
    return render_template('cases/list.html', cases=cases)
