import os
from pathlib import Path

import pymysql
from pymysql.constants.CLIENT import MULTI_STATEMENTS


BASE_DIR = Path(__file__).resolve().parent


def load_env(path=BASE_DIR / ".env"):
    if not path.exists():
        return

    with path.open("r", encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()

            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            os.environ.setdefault(key, value)


load_env()


def open_db(dbname=None):
    conn = pymysql.connect(host=os.getenv("DB_HOST", "localhost"),
                           user=os.getenv("DB_USER", "db_user"),
                           passwd=os.getenv("DB_PASSWORD", ""),
                           db=dbname or os.getenv("DB_NAME", "movie_db"),
                           port=int(os.getenv("DB_PORT", "3306")),
                           charset="utf8mb4",
                           client_flag=MULTI_STATEMENTS)
    cur = conn.cursor(pymysql.cursors.DictCursor)

    return conn, cur

def close_db(conn, cur):
    cur.close()
    conn.close()
    
if __name__ == '__main__':
    conn, cur = open_db()
    close_db(conn, cur)
