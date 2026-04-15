import sqlite3
import os
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "nutrition_bot.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS queries (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      TEXT    NOT NULL,
                username     TEXT,
                query_time   TEXT    NOT NULL,
                image_file   TEXT,
                result       TEXT,
                had_warnings INTEGER DEFAULT 0
            )
        """)
        conn.commit()


def log_query(user_id, username, image_file, result, had_warnings):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO queries (user_id, username, query_time, image_file, result, had_warnings)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (str(user_id), username, datetime.utcnow().isoformat(), image_file, result, int(had_warnings)),
        )
        conn.commit()


def get_user_history(user_id, limit=5):
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT query_time, result, had_warnings
               FROM queries WHERE user_id = ?
               ORDER BY query_time DESC LIMIT ?""",
            (str(user_id), limit),
        ).fetchall()
    return rows