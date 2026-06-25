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

            cur.execute("""
                SELECT c.*, a.id AS analyst_id2, a.username, a.email, a.role, a.created_at AS analyst_created_at
                FROM cases c JOIN analysts a ON c.analyst_id = a.id
                ORDER BY c.created_at DESC LIMIT 5
            """)
            recent_rows = cur.fetchall()
            recent_cases = []
            for r in recent_rows:
                case = Case.from_row(r)
                analyst = Analyst(
                    id=r['analyst_id2'], username=r['username'], email=r['email'],
                    password_hash='', role=r['role'], created_at=r['analyst_created_at']
                )
                case.analyst = analyst
                recent_cases.append(case)
    finally:
        conn.close()

    return render_template('dashboard/index.html',
                           total_cases=total_cases,
                           open_cases=open_cases,
                           in_progress_cases=in_progress_cases,
                           closed_cases=closed_cases,
                           critical_cases=critical_cases,
                           high_cases=high_cases,
                           total_evidence=total_evidence,
                           total_playbooks=total_playbooks,
                           total_analysts=total_analysts,
                           recent_cases=recent_cases,
                           severity_counts=severity_counts)

