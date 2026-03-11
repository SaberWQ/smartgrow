"""
core/scheduler.py
UV LED розклад + інші таймерні задачі
"""

import time, logging
from datetime import datetime
from config import UV_ON_HOUR, UV_OFF_HOUR
from core.actuators import uv_on, uv_off

log = logging.getLogger("scheduler")


def uv_schedule_loop(state: dict):
    """
    Вмикає/вимикає UV LED за годинним розкладом.
    state["uv"] оновлюється тут.
    """
    while True:
        try:
            hour = datetime.now().hour
            should_be_on = UV_ON_HOUR <= hour < UV_OFF_HOUR

            if should_be_on and not state["uv"]:
                uv_on()
                state["uv"] = True

            elif not should_be_on and state["uv"]:
                uv_off()
                state["uv"] = False

        except Exception as e:
            log.error(f"uv_schedule_loop: {e}")

        time.sleep(60)
