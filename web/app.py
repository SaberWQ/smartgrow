# /home/smartgrow/web/app.py

import threading, time, logging, socket
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
    while True:
        try:
            socketio.emit("update", get_latest())
            socketio.emit("events", get_events(limit=15))
        except Exception as e:
            log.error("push: %s", e)
        time.sleep(3)


def _port_free(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


def run_web():
    for i in range(30):
        if _port_free(WEB_PORT):
            break
        log.warning("Port %d busy, waiting... (%d/30)", WEB_PORT, i + 1)
        time.sleep(1)
    threading.Thread(target=_push_loop, daemon=True).start()
    log.info("Web on %s:%d", WEB_HOST, WEB_PORT)
    socketio.run(app, host=WEB_HOST, port=WEB_PORT,
                 debug=False, use_reloader=False)
