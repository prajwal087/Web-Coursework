import logging
import re

import pymysql
from config import Config

logger = logging.getLogger(__name__)


def get_db():
    return pymysql.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )


def init_db():
    conn = pymysql.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        charset='utf8mb4'
    )
    try:
        with conn.cursor() as cur:
            db_name = Config.MYSQL_DB
            if not re.match(r'^[a-zA-Z0-9_]+$', db_name):
                raise ValueError("Invalid database name")
            cur.execute("CREATE DATABASE IF NOT EXISTS {} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci".format(db_name))
            cur.execute("USE {}".format(db_name))
            
            # Analysts table with indexes
            cur.execute("""
                CREATE TABLE IF NOT EXISTS analysts (
                    id          INT             AUTO_INCREMENT PRIMARY KEY,
                    username    VARCHAR(80)     NOT NULL UNIQUE,
                    email       VARCHAR(120)    NOT NULL UNIQUE,
                    password_hash VARCHAR(255)  NOT NULL,
                    role        VARCHAR(20)     NOT NULL DEFAULT 'analyst',
                    created_at  DATETIME        DEFAULT CURRENT_TIMESTAMP,
                    updated_at  DATETIME        DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_username (username),
                    INDEX idx_email (email),
                    INDEX idx_role (role),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # Cases table with indexes
            cur.execute("""
                CREATE TABLE IF NOT EXISTS cases (
                    id          INT             AUTO_INCREMENT PRIMARY KEY,
                    title       VARCHAR(200)    NOT NULL,
                    description TEXT,
                    severity    VARCHAR(20)     NOT NULL DEFAULT 'low',
                    status      VARCHAR(20)     NOT NULL DEFAULT 'open',
                    created_at  DATETIME        DEFAULT CURRENT_TIMESTAMP,
                    updated_at  DATETIME        DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    analyst_id  INT             NOT NULL,
                    FOREIGN KEY (analyst_id) REFERENCES analysts(id) ON DELETE CASCADE,
                    INDEX idx_analyst_id (analyst_id),
                    INDEX idx_status (status),
                    INDEX idx_severity (severity),
                    INDEX idx_created_at (created_at),
                    INDEX idx_updated_at (updated_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # Evidence table with indexes
            cur.execute("""
                CREATE TABLE IF NOT EXISTS evidence (
                    id          INT             AUTO_INCREMENT PRIMARY KEY,
                    title       VARCHAR(200)    NOT NULL,
                    content     TEXT            NOT NULL,
                    source      VARCHAR(50)     NOT NULL DEFAULT 'manual',
                    created_at  DATETIME        DEFAULT CURRENT_TIMESTAMP,
                    case_id     INT             NOT NULL,
                    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE,
                    INDEX idx_case_id (case_id),
                    INDEX idx_created_at (created_at),
                    INDEX idx_source (source)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # Playbooks table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS playbooks (
                    id          INT             AUTO_INCREMENT PRIMARY KEY,
                    name        VARCHAR(200)    NOT NULL,
                    description TEXT,
                    steps       TEXT            NOT NULL DEFAULT ('[]'),
                    created_at  DATETIME        DEFAULT CURRENT_TIMESTAMP,
                    updated_at  DATETIME        DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # Case tasks table (per-case copies of playbook steps)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS case_tasks (
                    id                INT             AUTO_INCREMENT PRIMARY KEY,
                    case_id           INT             NOT NULL,
                    task_description  TEXT            NOT NULL,
                    is_complete       TINYINT(1)      DEFAULT 0,
                    source_playbook_id INT,
                    created_at        DATETIME        DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE,
                    FOREIGN KEY (source_playbook_id) REFERENCES playbooks(id) ON DELETE SET NULL,
                    INDEX idx_case_id (case_id),
                    INDEX idx_source_playbook_id (source_playbook_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            # Login lockout table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS login_attempts (
                    id          INT             AUTO_INCREMENT PRIMARY KEY,
                    username    VARCHAR(80)     NOT NULL,
                    ip_address  VARCHAR(45),
                    attempted_at DATETIME       DEFAULT CURRENT_TIMESTAMP,
                    success     TINYINT(1)     DEFAULT 0,
                    INDEX idx_username (username),
                    INDEX idx_ip_address (ip_address),
                    INDEX idx_attempted_at (attempted_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # Add composite indexes for common queries
            try:
                with conn.cursor() as cur2:
                    cur2.execute("USE {}".format(db_name))
                    cur2.execute("CREATE INDEX IF NOT EXISTS idx_cases_status_severity ON cases(status, severity)")
                    cur2.execute("CREATE INDEX IF NOT EXISTS idx_cases_analyst_created ON cases(analyst_id, created_at)")
                    cur2.execute("CREATE INDEX IF NOT EXISTS idx_evidence_case_created ON evidence(case_id, created_at)")
            except Exception:
                conn.rollback()
            
            # Activity log table with indexes
            cur.execute("""
                CREATE TABLE IF NOT EXISTS activity_log (
                    id          INT             AUTO_INCREMENT PRIMARY KEY,
                    analyst_id  INT             NOT NULL,
                    action      VARCHAR(100)    NOT NULL,
                    details     TEXT,
                    ip_address  VARCHAR(45),
                    created_at  DATETIME        DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (analyst_id) REFERENCES analysts(id) ON DELETE CASCADE,
                    INDEX idx_analyst_id (analyst_id),
                    INDEX idx_action (action),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # Sessions table for session management
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id  VARCHAR(255)    PRIMARY KEY,
                    analyst_id  INT             NOT NULL,
                    ip_address  VARCHAR(45),
                    user_agent  VARCHAR(255),
                    created_at  DATETIME        DEFAULT CURRENT_TIMESTAMP,
                    expires_at  DATETIME        NOT NULL,
                    last_activity DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (analyst_id) REFERENCES analysts(id) ON DELETE CASCADE,
                    INDEX idx_analyst_id (analyst_id),
                    INDEX idx_expires_at (expires_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
        # Schema migrations for existing databases
        # Each migration is independent — failures are logged but don't block others
        def _migrate(cur, sql, desc):
            try:
                cur.execute(sql)
                conn.commit()
                logger.info(f"Migration OK: {desc}")
            except Exception as e:
                conn.rollback()
                logger.warning(f"Migration skipped (already applied or not applicable): {desc} -> {e}")

        with conn.cursor() as cur:
            cur.execute("USE {}".format(db_name))
            _migrate(cur, "ALTER TABLE activity_log ADD COLUMN ip_address VARCHAR(45) AFTER details",
                     "activity_log.ip_address")
            _migrate(cur, "ALTER TABLE sessions ADD COLUMN ip_address VARCHAR(45) AFTER analyst_id",
                     "sessions.ip_address")
            # Ensure created_at has DEFAULT CURRENT_TIMESTAMP on existing tables
            for tbl in ['cases', 'evidence', 'analysts', 'playbooks']:
                _migrate(cur, f"ALTER TABLE {tbl} MODIFY created_at DATETIME DEFAULT CURRENT_TIMESTAMP",
                         f"{tbl}.created_at MODIFY")
            # Ensure updated_at has DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            _migrate(cur, "ALTER TABLE analysts ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER created_at",
                     "analysts.updated_at ADD")
            _migrate(cur, "ALTER TABLE playbooks ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER created_at",
                     "playbooks.updated_at ADD")
            _migrate(cur, "ALTER TABLE cases MODIFY updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
                     "cases.updated_at MODIFY")
            # Backfill existing NULL updated_at values
            _migrate(cur, "UPDATE cases SET updated_at = COALESCE(created_at, NOW()) WHERE updated_at IS NULL",
                     "cases.updated_at backfill")
            _migrate(cur, "UPDATE analysts SET updated_at = created_at WHERE updated_at IS NULL",
                     "analysts.updated_at backfill")
            _migrate(cur, "UPDATE playbooks SET updated_at = created_at WHERE updated_at IS NULL",
                     "playbooks.updated_at backfill")
    finally:
        conn.close()
