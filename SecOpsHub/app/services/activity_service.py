import logging
from app.database import get_db

logger = logging.getLogger(__name__)


class ActivityService:
    def log_activity(self, analyst_id, action, details='', ip_address=None):
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO activity_log (analyst_id, action, details, ip_address)
                       VALUES (%s, %s, %s, %s)""",
                    (analyst_id, action, details, ip_address)
                )
            conn.commit()
        except Exception as e:
            logger.error(f"Error logging activity: {str(e)}")
        finally:
            conn.close()

    def get_activity_log(self, analyst_id=None, limit=100):
        conn = get_db()
        try:
            with conn.cursor() as cur:
                if analyst_id:
                    cur.execute(
                        """SELECT * FROM activity_log
                           WHERE analyst_id = %s
                           ORDER BY created_at DESC
                           LIMIT %s""",
                        (analyst_id, limit)
                    )
                else:
                    cur.execute(
                        """SELECT * FROM activity_log
                           ORDER BY created_at DESC
                           LIMIT %s""",
                        (limit,)
                    )
                return cur.fetchall()
        except Exception as e:
            logger.error(f"Error fetching activity log: {str(e)}")
            raise
        finally:
            conn.close()


activity_service = ActivityService()
