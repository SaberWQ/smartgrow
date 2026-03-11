"""
services/alerts.py
Моніторинг критичних значень і надсилання сповіщень
"""

import asyncio, time, logging
from config import (ALERT_COOLDOWN_SEC, ALERT_SOIL_CRITICAL,
                    ALERT_TEMP_HIGH, ALERT_TEMP_LOW)
from services.database import insert_event

log = logging.getLogger("alerts")


def alert_loop(state: dict):
    """Нескінченний цикл перевірки алертів."""
    last_sent: dict[str, float] = {}

    def _should(key: str) -> bool:
        return time.time() - last_sent.get(key, 0) > ALERT_COOLDOWN_SEC

    def _fire(key: str, msg: str):
        last_sent[key] = time.time()
        insert_event("ALERT", msg)
        asyncio.run(_send(msg))
        log.warning(f"ALERT: {msg}")

    async def _send(msg: str):
        from services.telegram_bot import send_message
        await send_message(f"⚠️ *SmartGrow Alert*\n{msg}")

    while True:
        try:
            s1, s2 = state["soil1"], state["soil2"]
            temp   = state["temp"]

            if (s1 < ALERT_SOIL_CRITICAL or s2 < ALERT_SOIL_CRITICAL) and _should("dry"):
                _fire("dry", f"Критично сухий ґрунт!\nG1:{s1}% G2:{s2}%")

            if temp > ALERT_TEMP_HIGH and temp > 0 and _should("hot"):
                _fire("hot", f"Висока температура: {temp}°C")

            if 0 < temp < ALERT_TEMP_LOW and _should("cold"):
                _fire("cold", f"Низька температура: {temp}°C")

        except Exception as e:
            log.error(f"alert_loop: {e}")

        time.sleep(60)
