from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models.case import Case
from app.models.analyst import Analyst
from app.database import get_db

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/')


@dashboard_bp.route('/')
@login_required
def index():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM cases")
            total_cases = cur.fetchone()['cnt']

            cur.execute("""
                SELECT status, COUNT(*) AS cnt FROM cases
                GROUP BY status
            """)
            status_map = {r['status']: r['cnt'] for r in cur.fetchall()}
            open_cases = status_map.get('open', 0)
            in_progress_cases = status_map.get('in_progress', 0)
            closed_cases = status_map.get('closed', 0)

            cur.execute("""
                SELECT severity, COUNT(*) AS cnt FROM cases
                GROUP BY severity
            """)
            sev_map = {r['severity']: r['cnt'] for r in cur.fetchall()}
            critical_cases = sev_map.get('critical', 0)
            high_cases = sev_map.get('high', 0)
            severity_counts = {
                'low': sev_map.get('low', 0),
                'medium': sev_map.get('medium', 0),
                'high': high_cases,
                'critical': critical_cases,
            }

            cur.execute("SELECT COUNT(*) AS cnt FROM evidence")
            total_evidence = cur.fetchone()['cnt']
            cur.execute("SELECT COUNT(*) AS cnt FROM playbooks")
            total_playbooks = cur.fetchone()['cnt']
            cur.execute("SELECT COUNT(*) AS cnt FROM analysts")
            total_analysts = cur.fetchone()['cnt']
