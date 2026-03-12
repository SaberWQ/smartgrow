#!/usr/bin/env python3
# /home/smartgrow/main.py

import threading, time, logging, sys
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("/home/smartgrow/logs/main.log"),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger("main")

state = {
    "soil1":      0,
    "soil2":      0,
    "temp":       0.0,
    "hum_air":    0.0,
    "pump":       False,
    "uv":         False,
    "battery":    100,
    "battery_v":  0.0,
    "last_water": "--",
}


def sensor_loop():
    from core.sensors import read_soil, read_dht, read_battery
    while True:
        try:
            state["soil1"], state["soil2"] = read_soil()
            t, h = read_dht()
            if t: state["temp"]    = t
            if h: state["hum_air"] = h
            state["battery"], state["battery_v"] = read_battery()
        except Exception as e:
            log.error("sensor_loop: %s", e)
        time.sleep(3)


def main():
    log.info("=" * 50)
    log.info("SmartGrow Mini starting  %s",
             datetime.now().strftime("%d.%m.%Y %H:%M"))
    log.info("=" * 50)

    from core.watering         import watering_loop
    from core.scheduler        import uv_schedule_loop
    from displays.oled_manager import display_loop as oled_loop
    from displays.ips_manager  import display_loop as ips_loop
    from services.database     import db_loop
    from services.telegram_bot import run_bot
    from services.alerts       import alert_loop
    from web.app               import run_web

    tasks = [
        ("Sensors",  sensor_loop,      ()),
        ("Watering", watering_loop,    (state,)),
        ("UV",       uv_schedule_loop, (state,)),
        ("OLED",     oled_loop,        (state,)),
        ("IPS",      ips_loop,         (state,)),
        ("Database", db_loop,          (state,)),
        ("Alerts",   alert_loop,       (state,)),
        ("Telegram", run_bot,          (state,)),
        ("Web",      run_web,          ()),
    ]

    for name, fn, args in tasks:
        threading.Thread(target=fn, args=args,
                         daemon=True, name=name).start()
        log.info("  started: %s", name)

    log.info("All threads running | Web: http://0.0.0.0:%d",
             __import__("config").WEB_PORT)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Stopping...")
        from core.actuators import cleanup
        cleanup()
        sys.exit(0)


if __name__ == "__main__":
    main()
