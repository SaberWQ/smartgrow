# /home/smartgrow/core/watering.py

import time, logging
from datetime import datetime
from config import SOIL_MIN, SOIL_MAX, PUMP_MAX_SEC
from core.actuators import pump_on, pump_off

log = logging.getLogger("watering")


def watering_loop(state):
    while True:
        try:
            avg = (state["soil1"] + state["soil2"]) // 2

            if avg < SOIL_MIN and not state["pump"]:
                log.info("Soil %d%% < %d%% -> watering", avg, SOIL_MIN)
                pump_on()
                state["pump"]       = True
                state["last_water"] = datetime.now().strftime("%H:%M")

                for _ in range(PUMP_MAX_SEC):
                    time.sleep(1)
                    if (state["soil1"] + state["soil2"]) // 2 >= SOIL_MAX:
                        break

                pump_off()
                state["pump"] = False
                log.info("Watering done")

            elif avg >= SOIL_MAX and state["pump"]:
                pump_off()
                state["pump"] = False

        except Exception as e:
            log.error("watering_loop: %s", e)
            pump_off()
            state["pump"] = False

        time.sleep(5)
