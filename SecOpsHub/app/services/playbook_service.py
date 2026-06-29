from datetime import datetime
import json
import logging
from app.database import get_db
from app.models.playbook import Playbook

logger = logging.getLogger(__name__)


class PlaybookService:
    def get_all_playbooks(self, page=1, per_page=10, search_query=None):
        conn = get_db()
        try:
            with conn.cursor() as cur:
                if search_query:
                    where = "WHERE name LIKE %s"
                    params = (f'%{search_query}%',)
                else:
                    where = ""
                    params = None
                cur.execute(f"SELECT COUNT(*) FROM playbooks {where}", params or ())
                total = list(cur.fetchone().values())[0]
                offset = (page - 1) * per_page
                query = f"SELECT * FROM playbooks {where} ORDER BY created_at DESC LIMIT %s OFFSET %s"
                if params:
                    cur.execute(query, (*params, per_page, offset))
                else:
                    cur.execute(query, (per_page, offset))
                rows = cur.fetchall()
                total_pages = max(1, (total + per_page - 1) // per_page)
            playbooks = []
            for r in rows:
                pb = Playbook.from_row(r)
                try:
                    pb.step_count = len(json.loads(pb.steps))
                except (json.JSONDecodeError, TypeError):
                    pb.step_count = 0
                playbooks.append(pb)
            return playbooks, total_pages, page, total
        except Exception as e:
            logger.error(f"Error fetching playbooks: {str(e)}")
            raise
        finally:
            conn.close()

    def get_playbook_by_id(self, playbook_id):
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM playbooks WHERE id = %s", (playbook_id,))
                row = cur.fetchone()
            return Playbook.from_row(row) if row else None
        except Exception as e:
            logger.error(f"Error fetching playbook {playbook_id}: {str(e)}")
            raise
        finally:
            conn.close()

    def create_playbook(self, name, description, steps):
        conn = get_db()
        now = datetime.utcnow()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO playbooks (name, description, steps, created_at, updated_at) VALUES (%s, %s, %s, %s, %s)",
                    (name, description, json.dumps(steps), now, now)
                )
                playbook_id = cur.lastrowid
            conn.commit()
            logger.info(f"Playbook created: {name}")
            return playbook_id
        except Exception as e:
            logger.error(f"Error creating playbook: {str(e)}")
            raise
        finally:
            conn.close()

    def update_playbook(self, playbook_id, name, description, steps):
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE playbooks SET name=%s, description=%s, steps=%s WHERE id=%s",
                    (name, description, json.dumps(steps), playbook_id)
                )
            conn.commit()
            logger.info(f"Playbook {playbook_id} updated")
        except Exception as e:
            logger.error(f"Error updating playbook: {str(e)}")
            raise
        finally:
            conn.close()

    def delete_playbook(self, playbook_id):
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM playbooks WHERE id = %s", (playbook_id,))
            conn.commit()
            logger.info(f"Playbook {playbook_id} deleted")
        except Exception as e:
            logger.error(f"Error deleting playbook: {str(e)}")
            raise
        finally:
            conn.close()


playbook_service = PlaybookService()
