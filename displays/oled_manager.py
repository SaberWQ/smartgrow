# /home/smartgrow/displays/oled_manager.py
#
# Підключення (всі паралельно):
#   VCC -> 3.3V  |  GND -> GND
#   SDA -> GPIO2 (Pin 3)
#   SCL -> GPIO3 (Pin 5)
#
# OLED #1 -> 0x3C (нічого не паяти)
# OLED #2 -> 0x3D (перепаяти A0: GND -> VCC)
# Перевірити: i2cdetect -y 1

import logging, time
from datetime import datetime

log = logging.getLogger("oled")

_displays = []
OLED_OK   = False


def init():
    global _displays, OLED_OK
    _displays = []

    from config import OLED_WIDTH, OLED_HEIGHT

    # Нормалізуємо адреси — завжди список int, незалежно від формату в config
    try:
        from config import OLED_ADDRESSES as _raw
        if isinstance(_raw, int):
            addrs = [_raw]
        elif isinstance(_raw, (list, tuple)):
            addrs = [int(a) for a in _raw]
        else:
            addrs = [0x3C, 0x3D]
    except Exception:
        addrs = [0x3C, 0x3D]

    try:
        from luma.core.interface.serial import i2c as luma_i2c
        from luma.oled.device import ssd1306

        for addr in addrs:
            try:
                serial = luma_i2c(port=1, address=int(addr))
                device = ssd1306(serial, width=OLED_WIDTH, height=OLED_HEIGHT)
                _displays.append(device)
                log.info("OLED 0x%02X OK", addr)
            except Exception as e:
                log.warning("OLED 0x%02X not found: %s", addr, e)

        OLED_OK = len(_displays) > 0

    except ImportError as e:
        log.warning("luma.oled not installed: %s", e)


def _draw(device, lines):
    try:
        from luma.core.render import canvas
        from PIL import ImageFont
        font = ImageFont.load_default()
        with canvas(device) as draw:
            for i, line in enumerate(lines):
                txt = str(line).encode("ascii", errors="replace").decode("ascii")
                draw.text((0, i * 13), txt, font=font, fill="white")
    except Exception as e:
        log.error("OLED draw: %s", e)


def update_all(state):
    if not OLED_OK or not _displays:
        return
    screens = [
        [
            "SmartGrow Mini",
            "G1: %3d%%" % state["soil1"],
            "G2: %3d%%" % state["soil2"],
            "PUMP: ON" if state["pump"] else "PUMP: off",
            "Water: %s"  % state["last_water"],
        ],
        [
            "Temp: %.1fC"  % state["temp"],
            "Hum:  %.0f%%" % state["hum_air"],
            "UV: ON" if state["uv"] else "UV: off",
            "Bat: %d%%" % state.get("battery", 100),
            datetime.now().strftime("%H:%M"),
        ],
    ]
    for i, device in enumerate(_displays):
        if i < len(screens):
            _draw(device, screens[i])


def display_loop(state):
    init()
    while True:
        try:
            update_all(state)
        except Exception as e:
            log.error("display_loop: %s", e)
        time.sleep(2)
