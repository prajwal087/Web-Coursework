from app.database import get_db


class AdminService:
    def get_admin_stats(self):
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
                    LIMIT 50
                """)
                activities = cur.fetchall()

            return {
                'total_analysts': total_analysts,
                'total_cases': total_cases,
                'total_evidence': total_evidence,
                'total_playbooks': total_playbooks,
                'analysts': analysts,
                'activities': activities,
            }
        finally:
            conn.close()


admin_service = AdminService()
