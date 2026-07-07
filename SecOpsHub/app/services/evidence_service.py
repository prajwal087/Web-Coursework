from datetime import datetime, timezone
import logging
from app.database import get_db
from app.models.evidence import Evidence
from app.models.case import Case

logger = logging.getLogger(__name__)


class EvidenceService:
    def get_all_evidence(self, page=1, per_page=10, search_query=None):
        conn = get_db()
        try:
            with conn.cursor() as cur:
                if search_query:
                    where = "WHERE title LIKE %s OR source LIKE %s"
                    like = f'%{search_query}%'
                    params = (like, like)
                else:
                    where = ""
                    params = None
                cur.execute(f"SELECT COUNT(*) FROM evidence {where}", params or ())
                total = list(cur.fetchone().values())[0]
                offset = (page - 1) * per_page
                query = f"SELECT * FROM evidence {where} ORDER BY created_at DESC LIMIT %s OFFSET %s"
                if params:
                    cur.execute(query, (*params, per_page, offset))
                else:
                    cur.execute(query, (per_page, offset))
                rows = cur.fetchall()
                total_pages = max(1, (total + per_page - 1) // per_page)
            return [Evidence.from_row(r) for r in rows], total_pages, page, total
        except Exception as e:
            logger.error(f"Error fetching evidence: {str(e)}")
            raise
        finally:
            conn.close()

    def get_evidence_by_id(self, evidence_id):
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM evidence WHERE id = %s", (evidence_id,))
                row = cur.fetchone()
            return Evidence.from_row(row) if row else None
        except Exception as e:
            logger.error(f"Error fetching evidence {evidence_id}: {str(e)}")
            raise
        finally:
            conn.close()

    def add_evidence(self, case_id, title, content, source):
        conn = get_db()
        now = datetime.now(timezone.utc)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO evidence (title, content, source, case_id, created_at) VALUES (%s, %s, %s, %s, %s)",
                    (title, content, source, case_id, now)
                )
                evidence_id = cur.lastrowid
            conn.commit()
            logger.info(f"Evidence added to case {case_id}")
            return evidence_id
        except Exception as e:
            logger.error(f"Error adding evidence: {str(e)}")
            raise
        finally:
            conn.close()

    def update_evidence(self, evidence_id, title, content, source, case_id):
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE evidence SET title=%s, content=%s, source=%s, case_id=%s WHERE id=%s",
                    (title, content, source, case_id, evidence_id)
                )
            conn.commit()
            logger.info(f"Evidence {evidence_id} updated")
        except Exception as e:
            logger.error(f"Error updating evidence: {str(e)}")
            raise
        finally:
            conn.close()

    def delete_evidence(self, evidence_id):
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM evidence WHERE id = %s", (evidence_id,))
            conn.commit()
            logger.info(f"Evidence {evidence_id} deleted")
        except Exception as e:
            logger.error(f"Error deleting evidence: {str(e)}")
            raise
        finally:
            conn.close()

    def get_all_cases_basic(self):
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM cases")
                return [Case.from_row(r) for r in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching cases: {str(e)}")
            raise
        finally:
            conn.close()


evidence_service = EvidenceService()
