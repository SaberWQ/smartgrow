#!/usr/bin/env python3
"""
SmartGrow Mini — Точка входу
Запускає всі потоки системи

Запуск:
  cd /home/smartgrow
  source venv/bin/activate
  python main.py
"""

import threading, time, logging, sys
from datetime import datetime

# ── Логування ────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("/home/smartgrow/logs/main.log"),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger("main")

# ── Спільний стан (передається у всі модулі) ─────────────────
state: dict = {
    "soil1":      0,
    "soil2":      0,
    "temp":       0.0,
    "hum_air":    0.0,
    "pump":       False,
    "uv":         False,
    "battery":    100,    # % заряду
    "battery_v":  0.0,    # В напруга (для індикатора SPBKAS)
    "last_water": "—",
}


# ── Потік читання датчиків ───────────────────────────────────
def sensor_loop():
    from core.sensors import read_soil, read_dht, read_battery
    while True:
        try:
            s1, s2 = read_soil()
            state["soil1"], state["soil2"] = s1, s2

            t, h = read_dht()
            if t: state["temp"]    = t
            if h: state["hum_air"] = h

            bat_pct, bat_v = read_battery()
            state["battery"] = bat_pct
            state["battery_v"] = bat_v

        except Exception as e:
            log.error(f"sensor_loop: {e}")
        time.sleep(3)


# ── Головний запуск ──────────────────────────────────────────
def main():
    log.info("=" * 55)
    log.info("  🌱 SmartGrow Mini стартує...")
    log.info(f"  📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    log.info("=" * 55)

    # Імпортуємо тут — після ініціалізації логування
    from core.watering    import watering_loop
    from core.scheduler   import uv_schedule_loop
    from displays.oled_manager import display_loop as oled_loop
    from displays.ips_manager  import display_loop as ips_loop
    from services.database     import db_loop
    from services.telegram_bot import run_bot
    from services.alerts       import alert_loop
    from web.app               import run_web

    tasks = [
        ("Sensors",  sensor_loop,              ()),
        ("Watering", watering_loop,             (state,)),
        ("UV",       uv_schedule_loop,          (state,)),
        ("OLED",     oled_loop,                 (state,)),
        ("IPS",      ips_loop,                  (state,)),
        ("Database", db_loop,                   (state,)),
        ("Alerts",   alert_loop,                (state,)),
        ("Telegram", run_bot,                   (state,)),
        ("Web",      run_web,                   ()),
    ]

    threads = []
    for name, fn, args in tasks:
        t = threading.Thread(target=fn, args=args, daemon=True, name=name)
        t.start()
        threads.append(t)
        log.info(f"  ✓ [{name}]")

    log.info("✅ Всі потоки запущено")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("\n🛑 Зупинка системи...")
        from core.actuators import cleanup
        cleanup()
        log.info("👋 SmartGrow Mini зупинено")
        sys.exit(0)


if __name__ == "__main__":
    main()
