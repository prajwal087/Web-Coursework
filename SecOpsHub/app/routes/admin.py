from flask import Blueprint, render_template
from flask_login import login_required
from app.database import get_db
from app import role_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/')
@login_required
@role_required('lead')
def index():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM analysts")
            total_analysts = cur.fetchone()['cnt']
            cur.execute("SELECT COUNT(*) AS cnt FROM cases")
            total_cases = cur.fetchone()['cnt']
            cur.execute("SELECT COUNT(*) AS cnt FROM evidence")
            total_evidence = cur.fetchone()['cnt']
            cur.execute("SELECT COUNT(*) AS cnt FROM playbooks")
            total_playbooks = cur.fetchone()['cnt']

            cur.execute("""
                SELECT a.id, a.username, a.email, a.role, a.created_at,
                       COUNT(c.id) AS case_count
                FROM analysts a
                LEFT JOIN cases c ON c.analyst_id = a.id
                GROUP BY a.id
                ORDER BY a.created_at DESC
            """)
            analysts = cur.fetchall()

            cur.execute("""
                SELECT al.*, a.username
                FROM activity_log al
                JOIN analysts a ON a.id = al.analyst_id
                ORDER BY al.created_at DESC
                LIMIT 30
            """)
            activities = cur.fetchall()
    finally:
        conn.close()
    return render_template('admin/index.html',
                           total_analysts=total_analysts,
                           total_cases=total_cases,
                           total_evidence=total_evidence,
                           total_playbooks=total_playbooks,
                           analysts=analysts,
                           activities=activities)
