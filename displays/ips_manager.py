# /home/smartgrow/displays/ips_manager.py
#
# Підключення IPS 1.9" ST7789 (SPI):
#   VCC -> 3.3V   GND -> GND
#   SCL -> GPIO11 SCLK (Pin 23)
#   SDA -> GPIO10 MOSI (Pin 19)
#   RES -> GPIO25      (Pin 22)
#   DC  -> GPIO24      (Pin 18)
#   CS  -> GPIO8  CE0  (Pin 24)
#   BL  -> 3.3V або GPIO18

import logging, time
from datetime import datetime
from config import IPS_WIDTH, IPS_HEIGHT, IPS_DC_PIN, IPS_RST_PIN

log = logging.getLogger("ips")

_ips   = None
IPS_OK = False

C_BG     = (8,  20,  8)
C_GREEN  = (0,  255, 136)
C_BLUE   = (68, 170, 255)
C_PURPLE = (204, 68, 255)
C_AMBER  = (255, 170, 0)
C_RED    = (255, 68,  68)
C_DIM    = (51,  68,  51)


def init():
    global _ips, IPS_OK
    try:
        from luma.core.interface.serial import spi
        from luma.lcd.device import st7789
        serial = spi(port=0, device=0,
                     gpio_DC=IPS_DC_PIN, gpio_RST=IPS_RST_PIN)
        _ips   = st7789(serial, width=IPS_WIDTH, height=IPS_HEIGHT,
                        rotate=0, bgr=False, h_offset=0, v_offset=0)
        IPS_OK = True
        log.info("IPS ST7789 OK")
    except Exception as e:
        log.warning("IPS ST7789 not found: %s", e)


def _bar(draw, x, y, w, h, pct, color):
    draw.rectangle([x, y, x + w, y + h], fill=(20, 40, 20))
    fw = max(0, int(w * pct / 100))
    if fw:
        draw.rectangle([x, y, x + fw, y + h], fill=color)


def update(state):
    if not IPS_OK or _ips is None:
        return
    try:
        from PIL import Image, ImageDraw, ImageFont
        img  = Image.new("RGB", (IPS_WIDTH, IPS_HEIGHT), C_BG)
        draw = ImageDraw.Draw(img)

        try:
            fnt_md = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
            fnt_sm = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
        except Exception:
            fnt_md = fnt_sm = ImageFont.load_default()

        draw.rectangle([0, 0, IPS_WIDTH, 22], fill=(0, 40, 20))
        draw.text((8, 4),   "SmartGrow Mini",                  font=fnt_md, fill=C_GREEN)
        draw.text((240, 6), datetime.now().strftime("%H:%M"),  font=fnt_sm, fill=C_DIM)

        draw.text((8, 30),  "G1:", font=fnt_sm, fill=C_DIM)
        draw.text((32, 28), "%d%%" % state["soil1"],           font=fnt_md, fill=C_GREEN)
        _bar(draw, 75, 32, 230, 8, state["soil1"], C_GREEN)

        draw.text((8, 48),  "G2:", font=fnt_sm, fill=C_DIM)
        draw.text((32, 46), "%d%%" % state["soil2"],           font=fnt_md, fill=C_GREEN)
        _bar(draw, 75, 50, 230, 8, state["soil2"], C_GREEN)

        draw.text((8, 68),  "Temp:", font=fnt_sm, fill=C_DIM)
        draw.text((50, 66), "%.1f C" % state["temp"],         font=fnt_md, fill=C_BLUE)
        draw.text((8, 86),  "Hum:",  font=fnt_sm, fill=C_DIM)
        draw.text((50, 84), "%.0f %%" % state["hum_air"],     font=fnt_md, fill=C_BLUE)

        pc = C_GREEN  if state["pump"] else C_DIM
        uc = C_PURPLE if state["uv"]   else C_DIM
        draw.text((8,  110), "PUMP", font=fnt_sm, fill=pc)
        draw.text((90, 110), "UV",   font=fnt_sm, fill=uc)
        draw.text((8,  122), "ON" if state["pump"] else "off", font=fnt_sm, fill=pc)
        draw.text((90, 122), "ON" if state["uv"]   else "off", font=fnt_sm, fill=uc)

        bat   = state.get("battery",   100)
        bat_v = state.get("battery_v", 0.0)
        bc    = C_GREEN if bat > 50 else C_AMBER if bat > 20 else C_RED
        bat_s = "Bat: %d%%  %.2fV" % (bat, bat_v) if bat_v else "Bat: %d%%" % bat
        draw.text((8, 145), bat_s, font=fnt_sm, fill=bc)
        draw.text((8, 157), "Water: %s" % state["last_water"], font=fnt_sm, fill=C_DIM)

        _ips.display(img)
    except Exception as e:
        log.error("IPS update: %s", e)


def display_loop(state):
    init()
    while True:
        try:
            update(state)
        except Exception as e:
            log.error("display_loop: %s", e)
        time.sleep(2)
