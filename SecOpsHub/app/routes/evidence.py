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
