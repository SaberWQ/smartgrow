"""
displays/oled_manager.py
Керування кількома OLED SSD1306 на одній I2C шині.

Підключення (всі паралельно):
  VCC → 3.3V
  GND → GND
  SDA → GPIO2  (Pin 3)
  SCL → GPIO3  (Pin 5)

Адреси:
  OLED #1 → 0x3C  (за замовчуванням, нічого не паяти)
  OLED #2 → 0x3D  (перепаяти резистор A0: відключити від GND, підключити до VCC)
  OLED #3 → потребує TCA9548A або --  за замовчуванням недоступний

Перевірити адреси:  i2cdetect -y 1
"""

import logging
import time
from datetime import datetime
from config import OLED_ADDRESSES, OLED_WIDTH, OLED_HEIGHT

log = logging.getLogger("oled")

_displays = []   # список ініціалізованих дисплеїв
OLED_OK   = False


def init():
    """Ініціалізує всі OLED дисплеї з адресами з config.py"""
    global _displays, OLED_OK
    try:
        from luma.core.interface.serial import i2c as luma_i2c
        from luma.oled.device import ssd1306
        from PIL import ImageFont

        for addr in OLED_ADDRESSES:
            try:
                serial  = luma_i2c(port=1, address=addr)
                display = ssd1306(serial, width=OLED_WIDTH, height=OLED_HEIGHT)
                _displays.append(display)
                log.info(f"OLED @ 0x{addr:02X} ✓")
            except Exception as e:
                log.warning(f"OLED @ 0x{addr:02X} не знайдено: {e}")

        OLED_OK = len(_displays) > 0

    except ImportError as e:
        log.warning(f"luma.oled не встановлено: {e}")


def _draw(display, lines: list[str]):
    """Малює список рядків на дисплеї."""
    try:
        from luma.core.render import canvas
        from PIL import ImageFont
        font = ImageFont.load_default()
        with canvas(display) as draw:
            for i, line in enumerate(lines):
                draw.text((0, i * 13), line, font=font, fill="white")
    except Exception as e:
        log.error(f"OLED draw: {e}")


def update_all(state: dict):
    """
    Оновлює всі підключені OLED.
    OLED #0 — вологість ґрунту + насос
    OLED #1 — температура + UV
    OLED #2 — резервний / статус системи
    """
    if not OLED_OK or not _displays:
        return

    pump_str = "PUMP: ON  💧" if state["pump"] else "PUMP: off"
    uv_str   = "UV:   ON  💜" if state["uv"]   else "UV:   off"
    now_str  = datetime.now().strftime("%H:%M")

    screens = [
        # OLED #0 — ґрунт + насос
        [
            "SmartGrow Mini",
            f"G1:  {state['soil1']:>3}%",
            f"G2:  {state['soil2']:>3}%",
            pump_str,
            f"Polyw: {state['last_water']}",
        ],
        # OLED #1 — темп + UV
        [
            f"Temp: {state['temp']:.1f}C",
            f"Hum:  {state['hum_air']:.0f}%",
            uv_str,
            now_str,
        ],
        # OLED #2 — системний статус
        [
            "SmartGrow v1.0",
            f"Soil avg: {(state['soil1']+state['soil2'])//2}%",
            f"Bat:  {state['battery']}%",
            now_str,
        ],
    ]

    for i, display in enumerate(_displays):
        if i < len(screens):
            _draw(display, screens[i])


def display_loop(state: dict):
    """Нескінченний цикл оновлення дисплеїв."""
    init()
    while True:
        update_all(state)
        time.sleep(2)
