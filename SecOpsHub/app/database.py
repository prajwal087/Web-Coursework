import pymysql
from config import Config


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
            cur.execute("CREATE DATABASE IF NOT EXISTS {} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci".format(Config.MYSQL_DB))
            cur.execute("USE {}".format(Config.MYSQL_DB))
            cur.execute("""
                CREATE TABLE IF NOT EXISTS analysts (
                    id          INT             AUTO_INCREMENT PRIMARY KEY,
                    username    VARCHAR(80)     NOT NULL UNIQUE,
                    email       VARCHAR(120)    NOT NULL UNIQUE,
                    password_hash VARCHAR(255)  NOT NULL,
                    role        VARCHAR(20)     NOT NULL DEFAULT 'analyst',
                    created_at  DATETIME        DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB
            """)
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
                    FOREIGN KEY (analyst_id) REFERENCES analysts(id) ON DELETE CASCADE
                ) ENGINE=InnoDB
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS evidence (
                    id          INT             AUTO_INCREMENT PRIMARY KEY,
                    title       VARCHAR(200)    NOT NULL,
                    content     TEXT            NOT NULL,
                    source      VARCHAR(50)     NOT NULL DEFAULT 'manual',
                    created_at  DATETIME        DEFAULT CURRENT_TIMESTAMP,
                    case_id     INT             NOT NULL,
                    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
                ) ENGINE=InnoDB
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS playbooks (
                    id          INT             AUTO_INCREMENT PRIMARY KEY,
                    name        VARCHAR(200)    NOT NULL,
                    description TEXT,
                    steps       TEXT            NOT NULL DEFAULT ('[]'),
                    created_at  DATETIME        DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB
            """)
        conn.commit()
    finally:
        conn.close()
