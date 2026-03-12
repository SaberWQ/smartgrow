# /home/smartgrow/services/database.py

import sqlite3, logging, time
from config import DB_PATH, DB_LOG_INTERVAL

log = logging.getLogger("database")


def init_db():
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
        log.info("DB OK: %s", DB_PATH)
    except Exception as e:
        log.error("init_db: %s", e)


def insert_reading(state):
    try:
        con = sqlite3.connect(DB_PATH)
        con.execute(
            "INSERT INTO sensor_data(soil1,soil2,temp,hum_air,pump,uv,battery) "
            "VALUES(?,?,?,?,?,?,?)",
            (state["soil1"], state["soil2"],
             state["temp"],  state["hum_air"],
             int(state["pump"]), int(state["uv"]),
             state.get("battery", 100)))
        con.commit()
        con.close()
    except Exception as e:
        log.error("insert_reading: %s", e)


def insert_event(event_type, message):
    try:
        con = sqlite3.connect(DB_PATH)
        con.execute(
            "INSERT INTO events(event_type,message) VALUES(?,?)",
            (event_type, message))
        con.commit()
        con.close()
        log.info("event [%s]: %s", event_type, message)
    except Exception as e:
        log.error("insert_event: %s", e)


def get_latest():
    try:
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        row = con.execute(
            "SELECT * FROM sensor_data ORDER BY id DESC LIMIT 1"
        ).fetchone()
        con.close()
        return dict(row) if row else {}
    except Exception as e:
        log.error("get_latest: %s", e)
        return {}


def get_history(minutes=60):
    try:
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        rows = con.execute(
            "SELECT * FROM sensor_data "
            "WHERE timestamp >= datetime('now','-%d minutes') "
            "ORDER BY timestamp ASC" % int(minutes)
        ).fetchall()
        con.close()
        return [dict(r) for r in rows]
    except Exception as e:
        log.error("get_history: %s", e)
        return []


def get_events(limit=20):
    try:
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        rows = con.execute(
            "SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        con.close()
        return [dict(r) for r in rows]
    except Exception as e:
        log.error("get_events: %s", e)
        return []


def db_loop(state):
    init_db()
    while True:
        insert_reading(state)
        time.sleep(DB_LOG_INTERVAL)
