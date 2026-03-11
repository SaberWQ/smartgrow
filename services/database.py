"""
services/database.py
SQLite: запис показань, подій, читання для веб-дашборду
"""

import sqlite3, logging, time
from config import DB_PATH, DB_LOG_INTERVAL

log = logging.getLogger("database")


def init_db():
    """Створити таблиці якщо не існують."""
    try:
        con = sqlite3.connect(DB_PATH)
        con.execute("""
            CREATE TABLE IF NOT EXISTS sensor_data (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                soil1     INTEGER  DEFAULT 0,
                soil2     INTEGER  DEFAULT 0,
                temp      REAL     DEFAULT 0,
                hum_air   REAL     DEFAULT 0,
                pump      INTEGER  DEFAULT 0,
                uv        INTEGER  DEFAULT 0,
                battery   INTEGER  DEFAULT 100
            )""")
        con.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp  DATETIME DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT,
                message    TEXT
            )""")
        con.execute(
            "CREATE INDEX IF NOT EXISTS idx_ts ON sensor_data(timestamp)")
        con.commit()
        con.close()
        log.info("SQLite DB ✓")
    except Exception as e:
        log.error(f"init_db: {e}")


def insert_reading(state: dict):
    """Записати поточні показання датчиків."""
    try:
        con = sqlite3.connect(DB_PATH)
        con.execute(
            "INSERT INTO sensor_data(soil1,soil2,temp,hum_air,pump,uv,battery) "
            "VALUES(?,?,?,?,?,?,?)",
            (state["soil1"], state["soil2"], state["temp"], state["hum_air"],
             int(state["pump"]), int(state["uv"]), state.get("battery", 100))
        )
        con.commit()
        con.close()
    except Exception as e:
        log.error(f"insert_reading: {e}")


def insert_event(event_type: str, message: str):
    """Записати подію (полив, UV, алерт)."""
    try:
        con = sqlite3.connect(DB_PATH)
        con.execute(
            "INSERT INTO events(event_type,message) VALUES(?,?)",
            (event_type, message)
        )
        con.commit()
        con.close()
        log.info(f"Event [{event_type}]: {message}")
    except Exception as e:
        log.error(f"insert_event: {e}")


def get_latest() -> dict:
    """Останній рядок sensor_data."""
    try:
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        row = con.execute(
            "SELECT * FROM sensor_data ORDER BY id DESC LIMIT 1"
        ).fetchone()
        con.close()
        return dict(row) if row else {}
    except Exception as e:
        log.error(f"get_latest: {e}")
        return {}


def get_history(minutes: int = 60) -> list[dict]:
    """Дані за останні N хвилин (для графіку)."""
    try:
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        rows = con.execute(
            "SELECT * FROM sensor_data "
            "WHERE timestamp >= datetime('now', ? || ' minutes') "
            "ORDER BY timestamp ASC",
            (f"-{minutes}",)
        ).fetchall()
        con.close()
        return [dict(r) for r in rows]
    except Exception as e:
        log.error(f"get_history: {e}")
        return []


def get_events(limit: int = 20) -> list[dict]:
    """Останні події."""
    try:
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        rows = con.execute(
            "SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        con.close()
        return [dict(r) for r in rows]
    except Exception as e:
        log.error(f"get_events: {e}")
        return []


def db_loop(state: dict):
    """Нескінченний цикл запису в БД."""
    init_db()
    while True:
        insert_reading(state)
        time.sleep(DB_LOG_INTERVAL)
