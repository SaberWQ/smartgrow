# /home/smartgrow/services/alerts.py

import time, logging
from config import (ALERT_COOLDOWN_SEC, ALERT_SOIL_CRITICAL,
                    ALERT_TEMP_HIGH, ALERT_TEMP_LOW)
from services.database import insert_event

log = logging.getLogger("alerts")


def alert_loop(state):
    last = {}

    def ready(key):
        return time.time() - last.get(key, 0) > ALERT_COOLDOWN_SEC

    def fire(key, msg):
        last[key] = time.time()
        insert_event("ALERT", msg)
        log.warning("ALERT: %s", msg)
        # Надсилаємо через telegram async-safe спосіб
        try:
            import asyncio
            from services.telegram_bot import send_message
            asyncio.run(send_message(msg))
        except Exception as e:
            log.error("alert send: %s", e)

    while True:
        try:
            s1, s2 = state["soil1"], state["soil2"]
            temp   = state["temp"]

            if (s1 < ALERT_SOIL_CRITICAL or s2 < ALERT_SOIL_CRITICAL) and ready("dry"):
                fire("dry", "Dry soil! G1:%d%% G2:%d%%" % (s1, s2))
            if temp > ALERT_TEMP_HIGH and temp > 0 and ready("hot"):
                fire("hot", "High temp: %.1fC" % temp)
            if 0 < temp < ALERT_TEMP_LOW and ready("cold"):
                fire("cold", "Low temp: %.1fC" % temp)

        except Exception as e:
            log.error("alert_loop: %s", e)

        time.sleep(60)
