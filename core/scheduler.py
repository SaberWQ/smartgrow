# /home/smartgrow/core/scheduler.py

import time, logging
from datetime import datetime
from config import UV_ON_HOUR, UV_OFF_HOUR
from core.actuators import uv_on, uv_off

log = logging.getLogger("scheduler")


def uv_schedule_loop(state):
    while True:
        try:
            hour = datetime.now().hour
            should = UV_ON_HOUR <= hour < UV_OFF_HOUR
            if should and not state["uv"]:
                uv_on()
                state["uv"] = True
            elif not should and state["uv"]:
                uv_off()
                state["uv"] = False
        except Exception as e:
            log.error("uv_schedule_loop: %s", e)
        time.sleep(60)
