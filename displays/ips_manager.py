"""
displays/ips_manager.py
Керування IPS 1.9" ST7789 через SPI

Підключення:
  VCC  → 3.3V
  GND  → GND
  SCL  → GPIO11 SCLK (Pin 23)
  SDA  → GPIO10 MOSI (Pin 19)
  RES  → GPIO25      (Pin 22)  ← config IPS_RST_PIN
  DC   → GPIO24      (Pin 18)  ← config IPS_DC_PIN
  CS   → GPIO8  CE0  (Pin 24)  ← config IPS_CS_PIN
  BL   → GPIO18 або 3.3V      ← config IPS_BL_PIN
"""

import logging, time
from datetime import datetime
from config import IPS_WIDTH, IPS_HEIGHT, IPS_DC_PIN, IPS_RST_PIN, IPS_CS_PIN

log = logging.getLogger("ips")

_ips    = None
IPS_OK  = False

# Кольори (RGB)
C_BG     = (13,  31,  13)
C_GREEN  = (0,   255, 136)
C_BLUE   = (68,  170, 255)
C_PURPLE = (204, 68,  255)
C_AMBER  = (255, 170, 0)
C_DIM    = (51,  68,  51)
C_WHITE  = (255, 255, 255)
C_RED    = (255, 68,  68)


def init():
    global _ips, IPS_OK
    try:
        from luma.core.interface.serial import spi
        from luma.lcd.device import st7789
        serial = spi(port=0, device=0, gpio_DC=IPS_DC_PIN, gpio_RST=IPS_RST_PIN)
        _ips   = st7789(serial, width=IPS_WIDTH, height=IPS_HEIGHT, rotate=0,
                        bgr=False, h_offset=0, v_offset=0)
        IPS_OK = True
        log.info("IPS ST7789 ✓")
    except Exception as e:
        IPS_OK = False
        log.warning(f"IPS ST7789 не знайдено: {e}")


def _bar(draw, x, y, w, h, pct, color):
    """Малює прогрес-бар."""
    draw.rectangle([x, y, x + w, y + h], outline=C_DIM, fill=(13, 26, 13))
    fill_w = int(w * pct / 100)
    if fill_w > 0:
        draw.rectangle([x, y, x + fill_w, y + h], fill=color)


def update(state: dict):
    """Малює головний екран на IPS дисплеї."""
    if not IPS_OK or _ips is None:
        return
    try:
        from PIL import Image, ImageDraw, ImageFont
        img  = Image.new("RGB", (IPS_WIDTH, IPS_HEIGHT), C_BG)
        draw = ImageDraw.Draw(img)

        try:
            font_lg = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
            font_md = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
            font_sm = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
        except Exception:
            font_lg = font_md = font_sm = ImageFont.load_default()

        # ── Заголовок ──────────────────────────────────
        draw.rectangle([0, 0, IPS_WIDTH, 24], fill=(0, 40, 20))
        draw.text((8, 4), "SmartGrow Mini", font=font_md, fill=C_GREEN)
        draw.text((IPS_WIDTH - 55, 6),
                  datetime.now().strftime("%H:%M"), font=font_sm, fill=C_DIM)

        # ── Ґрунт ──────────────────────────────────────
        draw.text((8, 32), f"G1:", font=font_sm, fill=C_DIM)
        draw.text((36, 30), f"{state['soil1']}%", font=font_md, fill=C_GREEN)
        _bar(draw, 70, 33, 120, 10, state["soil1"], C_GREEN)

        draw.text((8, 52), f"G2:", font=font_sm, fill=C_DIM)
        draw.text((36, 50), f"{state['soil2']}%", font=font_md, fill=C_GREEN)
        _bar(draw, 70, 53, 120, 10, state["soil2"], C_GREEN)

        # ── Температура ────────────────────────────────
        draw.text((8, 74), f"Temp:", font=font_sm, fill=C_DIM)
        draw.text((52, 72), f"{state['temp']:.1f}°C", font=font_md, fill=C_BLUE)

        draw.text((8, 92), f"Hum:", font=font_sm, fill=C_DIM)
        draw.text((52, 90), f"{state['hum_air']:.0f}%", font=font_md, fill=C_BLUE)

        # ── Статуси ────────────────────────────────────
        p_col = C_GREEN  if state["pump"] else C_DIM
        u_col = C_PURPLE if state["uv"]   else C_DIM
        draw.text((8,  116), "НАСОС", font=font_sm, fill=p_col)
        draw.text((80, 116), "UV LED", font=font_sm, fill=u_col)
        draw.text((8,  128), "ON" if state["pump"] else "off",
                  font=font_sm, fill=p_col)
        draw.text((80, 128), "ON" if state["uv"] else "off",
                  font=font_sm, fill=u_col)

        # ── Батарея (UPS HAT / SPBKAS індикатор) ───────────
        bat   = state.get("battery",   100)
        bat_v = state.get("battery_v", 0.0)
        bat_col = C_GREEN if bat > 50 else C_AMBER if bat > 20 else C_RED
        bat_str = f"Bat: {bat}%  {bat_v:.2f}V" if bat_v else f"Bat: {bat}%"
        draw.text((8, 148), bat_str, font=font_sm, fill=bat_col)
        draw.text((220, 148), state["last_water"], font=font_sm, fill=C_DIM)

        _ips.display(img)

    except Exception as e:
        log.error(f"IPS update: {e}")


def display_loop(state: dict):
    init()
    while True:
        update(state)
        time.sleep(2)
