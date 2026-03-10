#!/usr/bin/env python3
"""
SmartGrow Mini — Головний контролер
DietPi · Raspberry Pi 4B · Python 3
"""

import time, threading, logging, sqlite3, asyncio
from datetime import datetime

# ── GPIO ────────────────────────────────────────────────────────
try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO_OK = True
except Exception as e:
    GPIO_OK = False
    print(f"[WARN] GPIO: {e}")

# ── I2C / ADC ───────────────────────────────────────────────────
try:
    import board, busio
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
    i2c_bus  = busio.I2C(board.SCL, board.SDA)
    ads      = ADS.ADS1115(i2c_bus)
    ads.gain = 1
    soil_ch1 = AnalogIn(ads, ADS.P0)
    soil_ch2 = AnalogIn(ads, ADS.P1)
    ADS_OK   = True
except Exception as e:
    ADS_OK = False
    print(f"[WARN] ADS1115: {e}")

# ── DHT22 ───────────────────────────────────────────────────────
try:
    import adafruit_dht
    dht    = adafruit_dht.DHT22(board.D4)
    DHT_OK = True
except Exception as e:
    DHT_OK = False
    print(f"[WARN] DHT22: {e}")

# ── OLED дисплеї ────────────────────────────────────────────────
try:
    from luma.core.interface.serial import i2c as luma_i2c
    from luma.oled.device import ssd1306
    from luma.core.render import canvas
    from PIL import ImageFont
    oled1 = ssd1306(luma_i2c(port=1, address=0x3C), width=128, height=64)
    oled2 = ssd1306(luma_i2c(port=1, address=0x3D), width=128, height=64)
    FONT  = ImageFont.load_default()
    OLED_OK = True
except Exception as e:
    OLED_OK = False
    print(f"[WARN] OLED: {e}")

# ── Конфігурація ────────────────────────────────────────────────
TELEGRAM_TOKEN = "ВСТАВТЕ_ТОКЕН_ТУТ"
TELEGRAM_CHAT  = "ВСТАВТЕ_CHAT_ID_ТУТ"

RELAY_PUMP   = 17      # GPIO → Реле 1 → Насос 12V
RELAY_UV     = 27      # GPIO → Реле 2 → UV LED 12V
SOIL_MIN     = 40      # % мінімум — запустити полив
SOIL_MAX     = 75      # % максимум — зупинити полив
PUMP_MAX_SEC = 10      # секунд максимум одного поливу
UV_ON_HOUR   = 7       # UV вмикається о 07:00
UV_OFF_HOUR  = 22      # UV вимикається о 22:00
SOIL_DRY     = 17000   # ← ВИМІРЯЙ своє значення (сухий ґрунт)
SOIL_WET     = 7000    # ← ВИМІРЯЙ своє значення (мокрий ґрунт)
DB_PATH      = "/home/smartgrow/data/smartgrow.db"

# ── Логування ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("/home/smartgrow/logs/main.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("SmartGrow")

# ── GPIO ініціалізація ──────────────────────────────────────────
if GPIO_OK:
    GPIO.setup(RELAY_PUMP, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(RELAY_UV,   GPIO.OUT, initial=GPIO.HIGH)

# ── Стан системи ────────────────────────────────────────────────
state = {
    "soil1": 0, "soil2": 0,
    "temp": 0.0, "hum_air": 0.0,
    "pump": False, "uv": False,
    "battery": 100,
    "last_water": "—",
}

# ── База даних ──────────────────────────────────────────────────
def db_insert():
    try:
        con = sqlite3.connect(DB_PATH)
        con.execute(
            "INSERT INTO sensor_data(soil1,soil2,temp,hum_air,pump,uv,battery) "
            "VALUES(?,?,?,?,?,?,?)",
            (state["soil1"], state["soil2"], state["temp"], state["hum_air"],
             int(state["pump"]), int(state["uv"]), state["battery"])
        )
        con.commit(); con.close()
    except Exception as e:
        log.error(f"DB: {e}")

def db_event(etype, msg):
    try:
        con = sqlite3.connect(DB_PATH)
        con.execute("INSERT INTO events(event_type,message) VALUES(?,?)", (etype, msg))
        con.commit(); con.close()
    except: pass

# ── Актуатори ───────────────────────────────────────────────────
def pump_on():
    if GPIO_OK: GPIO.output(RELAY_PUMP, GPIO.LOW)
    state["pump"] = True
    state["last_water"] = datetime.now().strftime("%H:%M")
    db_event("PUMP_ON", f"Полив. G1:{state['soil1']}% G2:{state['soil2']}%")
    log.info("🚿 Насос ON")

def pump_off():
    if GPIO_OK: GPIO.output(RELAY_PUMP, GPIO.HIGH)
    state["pump"] = False
    log.info("⏹  Насос OFF")

def uv_on():
    if GPIO_OK: GPIO.output(RELAY_UV, GPIO.LOW)
    state["uv"] = True
    db_event("UV_ON", "UV LED увімкнено")
    log.info("💜 UV ON")

def uv_off():
    if GPIO_OK: GPIO.output(RELAY_UV, GPIO.HIGH)
    state["uv"] = False
    log.info("⏹  UV OFF")

# ── Конвертація ADC → % ─────────────────────────────────────────
def raw_to_pct(raw):
    return max(0, min(100, int((SOIL_DRY - raw) / (SOIL_DRY - SOIL_WET) * 100)))

# ── Потік: Датчики ──────────────────────────────────────────────
def sensor_loop():
    while True:
        try:
            if ADS_OK:
                state["soil1"] = raw_to_pct(soil_ch1.value)
                state["soil2"] = raw_to_pct(soil_ch2.value)
            if DHT_OK:
                try:
                    t = dht.temperature
                    h = dht.humidity
                    if t is not None: state["temp"]    = round(t, 1)
                    if h is not None: state["hum_air"] = round(h, 1)
                except: pass
            log.debug(f"G1={state['soil1']}% G2={state['soil2']}% "
                      f"T={state['temp']}°C H={state['hum_air']}%")
        except Exception as e:
            log.error(f"Sensor: {e}")
        time.sleep(3)

# ── Потік: Автополив ────────────────────────────────────────────
def watering_loop():
    while True:
        try:
            avg = (state["soil1"] + state["soil2"]) // 2
            if avg < SOIL_MIN and not state["pump"]:
                log.info(f"Ґрунт {avg}% < {SOIL_MIN}% → полив")
                pump_on()
                time.sleep(PUMP_MAX_SEC)
                pump_off()
            elif avg >= SOIL_MAX and state["pump"]:
                pump_off()
        except Exception as e:
            log.error(f"Watering: {e}")
            pump_off()
        time.sleep(5)

# ── Потік: UV розклад ───────────────────────────────────────────
def uv_loop():
    while True:
        h = datetime.now().hour
        if UV_ON_HOUR <= h < UV_OFF_HOUR:
            if not state["uv"]: uv_on()
        else:
            if state["uv"]: uv_off()
        time.sleep(60)

# ── Потік: OLED дисплеї ─────────────────────────────────────────
def display_loop():
    if not OLED_OK: return
    while True:
        try:
            with canvas(oled1) as draw:
                draw.text((0,  0), "SmartGrow Mini",      font=FONT, fill="white")
                draw.text((0, 16), f"G1: {state['soil1']:>3}%", font=FONT, fill="white")
                draw.text((0, 28), f"G2: {state['soil2']:>3}%", font=FONT, fill="white")
                draw.text((0, 44), f"Pump: {'ON' if state['pump'] else 'OFF'}", font=FONT, fill="white")

            with canvas(oled2) as draw:
                draw.text((0,  0), f"T: {state['temp']:.1f}C",    font=FONT, fill="white")
                draw.text((0, 14), f"H: {state['hum_air']:.0f}%", font=FONT, fill="white")
                draw.text((0, 28), f"UV: {'ON' if state['uv'] else 'OFF'}", font=FONT, fill="white")
                draw.text((0, 44), datetime.now().strftime("%H:%M"), font=FONT, fill="white")
        except Exception as e:
            log.error(f"OLED: {e}")
        time.sleep(2)

# ── Потік: Логування в DB ───────────────────────────────────────
def db_loop():
    while True:
        db_insert()
        time.sleep(60)

# ── Потік: Сповіщення ───────────────────────────────────────────
def alert_loop():
    last = {}
    COOL = 1800  # 30 хв між однаковими алертами
    while True:
        now = time.time()
        checks = [
            ("dry",  state["soil1"] < 20 or state["soil2"] < 20,
             f"⚠️ *Критично сухий ґрунт!*\nG1:{state['soil1']}% G2:{state['soil2']}%"),
            ("hot",  state["temp"] > 35,
             f"🔥 *Висока температура!*\n{state['temp']}°C"),
            ("cold", 0 < state["temp"] < 10,
             f"🥶 *Низька температура!*\n{state['temp']}°C"),
        ]
        for key, cond, msg in checks:
            if cond and now - last.get(key, 0) > COOL:
                asyncio.run(tg_alert(msg))
                last[key] = now
        time.sleep(60)

# ── Telegram ────────────────────────────────────────────────────
async def tg_alert(msg):
    try:
        from telegram import Bot
        b = Bot(token=TELEGRAM_TOKEN)
        await b.send_message(chat_id=TELEGRAM_CHAT, text=msg, parse_mode="Markdown")
    except Exception as e:
        log.error(f"TG alert: {e}")

def run_bot():
    try:
        from telegram import Bot, Update
        from telegram.ext import Application, CommandHandler, ContextTypes

        async def cmd_status(u: Update, c: ContextTypes.DEFAULT_TYPE):
            p = "💧 ON" if state["pump"] else "⏹ OFF"
            v = "💜 ON" if state["uv"]   else "⏹ OFF"
            await u.message.reply_text(
                f"🌱 *SmartGrow Mini*\n"
                f"━━━━━━━━━━━━━━\n"
                f"🌍 Ґрунт 1: *{state['soil1']}%*\n"
                f"🌍 Ґрунт 2: *{state['soil2']}%*\n"
                f"🌡 Темп: *{state['temp']}°C*\n"
                f"💦 Повітря: *{state['hum_air']}%*\n"
                f"━━━━━━━━━━━━━━\n"
                f"🚿 Насос: {p}\n"
                f"💜 UV: {v}\n"
                f"⏰ Полив: {state['last_water']}\n"
                f"📅 {datetime.now().strftime('%d.%m %H:%M')}",
                parse_mode="Markdown"
            )

        async def cmd_water(u: Update, c: ContextTypes.DEFAULT_TYPE):
            if state["pump"]:
                await u.message.reply_text("⚠️ Насос вже працює!"); return
            pump_on()
            await u.message.reply_text("🚿 Полив запущено...")
            await asyncio.sleep(PUMP_MAX_SEC)
            pump_off()
            await u.message.reply_text("✅ Готово!")

        async def cmd_uv_on(u, c):
            uv_on(); await u.message.reply_text("💜 UV увімкнено!")
        async def cmd_uv_off(u, c):
            uv_off(); await u.message.reply_text("⏹ UV вимкнено!")
        async def cmd_help(u: Update, c: ContextTypes.DEFAULT_TYPE):
            await u.message.reply_text(
                "🌱 *SmartGrow Mini — Команди*\n\n"
                "/status — стан системи\n"
                "/water  — полив вручну\n"
                "/uvon   — UV увімкнути\n"
                "/uvoff  — UV вимкнути",
                parse_mode="Markdown"
            )

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        app = Application.builder().token(TELEGRAM_TOKEN).build()
        for cmd, fn in [("status", cmd_status), ("water", cmd_water),
                        ("uvon", cmd_uv_on), ("uvoff", cmd_uv_off), ("help", cmd_help)]:
            app.add_handler(CommandHandler(cmd, fn))
        log.info("🤖 Telegram бот запущено")
        app.run_polling(stop_signals=None)
    except Exception as e:
        log.error(f"Telegram bot: {e}")

# ── Main ────────────────────────────────────────────────────────
def main():
    log.info("🌱 SmartGrow Mini стартує...")
    log.info(f"  GPIO:    {'✓' if GPIO_OK else '✗'}")
    log.info(f"  ADS1115: {'✓' if ADS_OK  else '✗'}")
    log.info(f"  DHT22:   {'✓' if DHT_OK  else '✗'}")
    log.info(f"  OLED:    {'✓' if OLED_OK else '✗'}")

    tasks = [
        ("Sensors",  sensor_loop),
        ("Watering", watering_loop),
        ("UV",       uv_loop),
        ("Display",  display_loop),
        ("DB",       db_loop),
        ("Alerts",   alert_loop),
        ("Telegram", run_bot),
    ]
    for name, fn in tasks:
        threading.Thread(target=fn, daemon=True, name=name).start()
        log.info(f"  ✓ Thread: {name}")

    log.info("✅ Всі системи активні")
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        log.info("🛑 Зупинка...")
        pump_off(); uv_off()
        if GPIO_OK: GPIO.cleanup()
        log.info("👋 Завершено")

if __name__ == "__main__":
    main()
