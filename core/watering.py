"""
core/watering.py
Логіка автополиву на основі показань датчиків ґрунту
"""

import time, logging
from config import SOIL_MIN, SOIL_MAX, PUMP_MAX_SEC
from core.actuators import pump_on, pump_off

log = logging.getLogger("watering")


def watering_loop(state: dict):
    """
    Нескінченний цикл автополиву.
    state — спільний словник стану системи (передається з main.py)
    """
    while True:
        try:
            avg = (state["soil1"] + state["soil2"]) // 2

            if avg < SOIL_MIN and not state["pump"]:
                log.info(f"Ґрунт {avg}% < {SOIL_MIN}% → запуск поливу")
                pump_on()
                state["pump"] = True
                state["last_water"] = _now_str()

                # Чекаємо PUMP_MAX_SEC або поки датчик не покаже достатньо
                for _ in range(PUMP_MAX_SEC):
                    time.sleep(1)
                    if (state["soil1"] + state["soil2"]) // 2 >= SOIL_MAX:
                        break

                pump_off()
                state["pump"] = False
                log.info("Полив завершено")

            elif avg >= SOIL_MAX and state["pump"]:
                pump_off()
                state["pump"] = False

        except Exception as e:
            log.error(f"watering_loop: {e}")
            pump_off()
            state["pump"] = False

        time.sleep(5)


def _now_str() -> str:
    from datetime import datetime
    return datetime.now().strftime("%H:%M")
