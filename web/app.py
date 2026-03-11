"""
web/app.py
Flask + SocketIO веб-дашборд
Доступний на http://<IP_RPi>:5000 або через Nginx на порту 80
"""

import threading, time, logging
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
from services.database import get_latest, get_events, get_history
from config import WEB_HOST, WEB_PORT

log = logging.getLogger("web")

app      = Flask(__name__, template_folder="templates")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="gevent")


@app.route("/")
def index():
    return render_template("dashboard.html")

@app.route("/api/data")
def api_data():
    return jsonify(get_latest())

@app.route("/api/events")
def api_events():
    return jsonify(get_events())

@app.route("/api/history")
def api_history():
    return jsonify(get_history(minutes=60))


def _push_loop():
    """Надсилати дані клієнтам кожні 3 секунди."""
    while True:
        try:
            socketio.emit("update", get_latest())
            socketio.emit("events", get_events(limit=15))
        except Exception as e:
            log.error(f"push_loop: {e}")
        time.sleep(3)


def run_web():
    threading.Thread(target=_push_loop, daemon=True).start()
    log.info(f"🌐 Веб-сервер на {WEB_HOST}:{WEB_PORT}")
    socketio.run(app, host=WEB_HOST, port=WEB_PORT, debug=False)
