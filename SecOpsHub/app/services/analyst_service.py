from datetime import datetime
import logging
from app.database import get_db
from app.models.analyst import Analyst
from app.models.case import Case

logger = logging.getLogger(__name__)


class AnalystService:
    def get_analyst_by_username(self, username):
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM analysts WHERE username = %s", (username,))
                row = cur.fetchone()
            return Analyst.from_row(row) if row else None
        except Exception as e:
            logger.error(f"Error fetching analyst {username}: {str(e)}")
            raise
        finally:
            conn.close()

    def get_analyst_by_id(self, analyst_id):
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM analysts WHERE id = %s", (analyst_id,))
                row = cur.fetchone()
            return Analyst.from_row(row) if row else None
        except Exception as e:
            logger.error(f"Error fetching analyst {analyst_id}: {str(e)}")
            raise
        finally:
            conn.close()

    def get_all_analysts(self):
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM analysts ORDER BY username ASC")
                return [Analyst.from_row(r) for r in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching analysts: {str(e)}")
            raise
        finally:
            conn.close()

    def get_all_analysts_paginated(self, page=1, per_page=10, search_query=None):
        conn = get_db()
        try:
            with conn.cursor() as cur:
                if search_query:
                    where = "WHERE a.username LIKE %s OR a.email LIKE %s"
                    like = f'%{search_query}%'
                    params = (like, like)
                else:
                    where = ""
                    params = None
                cur.execute(f"SELECT COUNT(*) FROM analysts a {where}", params or ())
                total = list(cur.fetchone().values())[0]
                offset = (page - 1) * per_page
                query = f"""
                    SELECT a.*, COUNT(c.id) AS case_count
                    FROM analysts a LEFT JOIN cases c ON c.analyst_id = a.id {where}
                    GROUP BY a.id ORDER BY a.id ASC LIMIT %s OFFSET %s
                """
                if params:
                    cur.execute(query, (*params, per_page, offset))
                else:
                    cur.execute(query, (per_page, offset))
                rows = cur.fetchall()
                total_pages = max(1, (total + per_page - 1) // per_page)
            analysts = []
            for r in rows:
                analyst = Analyst.from_row(r)
                analyst.cases = [None] * (r['case_count'] or 0)
                analysts.append(analyst)
            return analysts, total_pages, page, total
        except Exception as e:
            logger.error(f"Error fetching analysts: {str(e)}")
            raise
        finally:
            conn.close()

    def get_analyst_with_cases(self, analyst_id):
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM analysts WHERE id = %s", (analyst_id,))
                analyst_row = cur.fetchone()
                if not analyst_row:
                    return None
                analyst = Analyst.from_row(analyst_row)
                cur.execute(
                    "SELECT * FROM cases WHERE analyst_id = %s ORDER BY created_at DESC",
                    (analyst_id,)
                )
                analyst.cases = [Case.from_row(r) for r in cur.fetchall()]
            return analyst
        except Exception as e:
            logger.error(f"Error fetching analyst {analyst_id}: {str(e)}")
            raise
        finally:
            conn.close()

    def check_duplicate(self, username, email):
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM analysts WHERE username = %s OR email = %s",
                    (username, email)
                )
                return cur.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking duplicate analyst: {str(e)}")
            raise
        finally:
            conn.close()

    def create_analyst_with_password(self, username, email, password, role='analyst'):
        analyst_obj = Analyst(None, username, email, '', role)
        analyst_obj.set_password(password)
        conn = get_db()
        now = datetime.utcnow()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO analysts (username, email, password_hash, role, created_at, updated_at)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (username, email, analyst_obj.password_hash, role, now, now)
                )
                analyst_id = cur.lastrowid
            conn.commit()
            logger.info(f"Analyst created: {username} with role {role}")
            return analyst_id
        except Exception as e:
            logger.error(f"Error creating analyst: {str(e)}")
            raise
        finally:
            conn.close()

    def update_analyst_password(self, analyst_id, password_hash):
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE analysts SET password_hash = %s WHERE id = %s",
                    (password_hash, analyst_id)
                )
            conn.commit()
            logger.info(f"Password updated for analyst {analyst_id}")
        except Exception as e:
            logger.error(f"Error updating password: {str(e)}")
            raise
        finally:
            conn.close()

    def update_analyst(self, analyst_id, username, email, role, password=None):
        conn = get_db()
        try:
            with conn.cursor() as cur:
                if password:
                    analyst_obj = Analyst(None, username, email, '', role)
                    analyst_obj.set_password(password)
                    cur.execute(
                        """UPDATE analysts SET username=%s, email=%s, password_hash=%s, role=%s
                           WHERE id=%s""",
                        (username, email, analyst_obj.password_hash, role, analyst_id)
                    )
                else:
                    cur.execute(
                        "UPDATE analysts SET username=%s, email=%s, role=%s WHERE id=%s",
                        (username, email, role, analyst_id)
                    )
            conn.commit()
            logger.info(f"Analyst {analyst_id} updated")
        except Exception as e:
            logger.error(f"Error updating analyst: {str(e)}")
            raise
        finally:
            conn.close()

    def delete_analyst(self, analyst_id):
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM analysts WHERE id = %s", (analyst_id,))
            conn.commit()
            logger.info(f"Analyst {analyst_id} deleted")
        except Exception as e:
            logger.error(f"Error deleting analyst: {str(e)}")
            raise
        finally:
            conn.close()

    def get_cases_by_analyst(self, analyst_id):
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM cases WHERE analyst_id = %s ORDER BY created_at DESC",
                    (analyst_id,)
                )
                return [Case.from_row(r) for r in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching cases for analyst {analyst_id}: {str(e)}")
            raise
        finally:
            conn.close()


analyst_service = AnalystService()
