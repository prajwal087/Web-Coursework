from datetime import datetime, timezone
import json
import logging
from app.database import get_db
from app.models.case import Case
from app.models.case import CaseTask
from app.models.evidence import Evidence
from app.models.playbook import Playbook

logger = logging.getLogger(__name__)


class CaseService:
    def get_all_cases(self, page=1, per_page=10, search_query=None):
        conn = get_db()
        try:
            with conn.cursor() as cur:
                if search_query:
                    where = "WHERE c.title LIKE %s OR c.description LIKE %s"
                    like = f'%{search_query}%'
                    params = (like, like)
                else:
                    where = ""
                    params = None
                cur.execute(f"SELECT COUNT(*) as total FROM cases c {where}", params or ())
                total = cur.fetchone()['total']
                offset = (page - 1) * per_page
                query = f"""
                    SELECT c.*, a.username, a.email, a.role
                    FROM cases c
                    JOIN analysts a ON c.analyst_id = a.id
                    {where}
                    ORDER BY c.updated_at DESC
                    LIMIT %s OFFSET %s
                """
                if params:
                    cur.execute(query, (*params, per_page, offset))
                else:
                    cur.execute(query, (per_page, offset))
                rows = cur.fetchall()
                total_pages = max(1, (total + per_page - 1) // per_page)
            return rows, total_pages, page, total
        except Exception as e:
            logger.error(f"Error fetching cases: {str(e)}")
            raise
        finally:
            conn.close()

    def get_case_by_id(self, case_id):
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT c.*, a.username, a.email, a.role, a.id as analyst_id2
                    FROM cases c JOIN analysts a ON c.analyst_id = a.id
                    WHERE c.id = %s
                """, (case_id,))
                case_row = cur.fetchone()
                if not case_row:
                    return None
                cur.execute(
                    "SELECT * FROM evidence WHERE case_id = %s ORDER BY created_at DESC",
                    (case_id,)
                )
                evidence_rows = cur.fetchall()
            case = Case.from_row(case_row)
            case.evidence_items = [Evidence.from_row(r) for r in evidence_rows]
            return case
        except Exception as e:
            logger.error(f"Error fetching case {case_id}: {str(e)}")
            raise
        finally:
            conn.close()

    def create_case(self, title, description, severity, analyst_id):
        conn = get_db()
        now = datetime.now(timezone.utc)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO cases (title, description, severity, analyst_id, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s)",
                    (title, description, severity, analyst_id, now, now)
                )
            conn.commit()
            logger.info(f"Case created: {title} by analyst {analyst_id}")
        except Exception as e:
            logger.error(f"Error creating case: {str(e)}")
            raise
        finally:
            conn.close()

    def update_case(self, case_id, title, description, severity, status):
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE cases SET title = %s, description = %s, severity = %s, status = %s WHERE id = %s",
                    (title, description, severity, status, case_id)
                )
            conn.commit()
            logger.info(f"Case {case_id} updated")
        except Exception as e:
            logger.error(f"Error updating case {case_id}: {str(e)}")
            raise
        finally:
            conn.close()

    def delete_case(self, case_id):
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM evidence WHERE case_id = %s", (case_id,))
                cur.execute("DELETE FROM case_tasks WHERE case_id = %s", (case_id,))
                cur.execute("DELETE FROM cases WHERE id = %s", (case_id,))
            conn.commit()
            logger.info(f"Case {case_id} deleted")
        except Exception as e:
            logger.error(f"Error deleting case {case_id}: {str(e)}", exc_info=True)
            raise
        finally:
            conn.close()

    def get_tasks_for_case(self, case_id):
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT ct.*, p.name AS playbook_name
                    FROM case_tasks ct
                    LEFT JOIN playbooks p ON ct.source_playbook_id = p.id
                    WHERE ct.case_id = %s
                    ORDER BY ct.source_playbook_id, ct.id
                """, (case_id,))
                rows = cur.fetchall()
            return [CaseTask.from_row(r) for r in rows]
        except Exception as e:
            logger.error(f"Error fetching tasks for case {case_id}: {str(e)}")
            raise
        finally:
            conn.close()

    def apply_playbook_to_case(self, case_id, playbook_id):
        conn = get_db()
        now = datetime.now(timezone.utc)
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT steps, name FROM playbooks WHERE id = %s", (playbook_id,))
                pb = cur.fetchone()
                if not pb:
                    raise ValueError("Playbook not found")
                steps = json.loads(pb['steps']) if pb['steps'] else []
                if not steps:
                    raise ValueError("Playbook has no steps")
                cur.execute(
                    "SELECT COUNT(*) AS cnt FROM case_tasks WHERE case_id = %s AND source_playbook_id = %s",
                    (case_id, playbook_id)
                )
                row = cur.fetchone()
                if row and row['cnt'] > 0:
                    raise ValueError(f"Playbook '{pb['name']}' is already applied to this case")
                for step in steps:
                    cur.execute(
                        "INSERT INTO case_tasks (case_id, task_description, source_playbook_id, created_at) VALUES (%s, %s, %s, %s)",
                        (case_id, step, playbook_id, now)
                    )
            conn.commit()
            logger.info(f"Playbook {playbook_id} applied to case {case_id}")
        except Exception as e:
            conn.rollback()
            logger.error(f"Error applying playbook to case: {str(e)}")
            raise
        finally:
            conn.close()

    def toggle_task(self, task_id, is_complete):
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE case_tasks SET is_complete = %s WHERE id = %s",
                    (1 if is_complete else 0, task_id)
                )
            conn.commit()
            logger.info(f"Task {task_id} toggled to {'complete' if is_complete else 'incomplete'}")
        except Exception as e:
            logger.error(f"Error toggling task {task_id}: {str(e)}")
            raise
        finally:
            conn.close()

    def get_available_playbooks(self, case_id):
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM playbooks
                    WHERE id NOT IN (
                        SELECT DISTINCT source_playbook_id FROM case_tasks
                        WHERE case_id = %s AND source_playbook_id IS NOT NULL
                    )
                    ORDER BY name
                """, (case_id,))
                rows = cur.fetchall()
            return [Playbook.from_row(r) for r in rows]
        except Exception as e:
            logger.error(f"Error fetching available playbooks: {str(e)}")
            raise
        finally:
            conn.close()


case_service = CaseService()
