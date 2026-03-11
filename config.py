import os
from dotenv import load_dotenv

# ═══════════════════════════════════════════════════════
#  SmartGrow Mini — Конфігурація
#  Всі налаштування в одному місці
# ═══════════════════════════════════════════════════════

# ── Telegram ────────────────────────────────────────────
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT  = os.getenv("TELEGRAM_CHAT")

# ── GPIO пін-аут ────────────────────────────────────────
RELAY_PUMP  = 17   # Реле 1 → Насос 12V
RELAY_UV    = 27   # Реле 2 → UV LED 12V

# ── Автополив ───────────────────────────────────────────
SOIL_MIN     = 40   # % → запустити полив якщо нижче
SOIL_MAX     = 75   # % → зупинити полив якщо вище
PUMP_MAX_SEC = 10   # максимум секунд одного циклу поливу

# ── Калібровка датчиків ґрунту ──────────────────────────
# Запусти: python3 -c "import board,busio,adafruit_ads1x15.ads1115 as ADS
# from adafruit_ads1x15.analog_in import AnalogIn
# i=busio.I2C(board.SCL,board.SDA); a=ADS.ADS1115(i); ch=AnalogIn(a,ADS.P0)
# print(ch.value)"  — і виміряй сухий/мокрий ґрунт
SOIL_DRY = 17000   # ← значення в СУХОМУ ґрунті
SOIL_WET  = 7000   # ← значення в МОКРОМУ ґрунті

# ── UV розклад ──────────────────────────────────────────
UV_ON_HOUR  = 7    # вмикати о 07:00
UV_OFF_HOUR = 22   # вимикати о 22:00

# ── I2C OLED дисплеї ────────────────────────────────────
# Всі на одній шині: SDA→GPIO2, SCL→GPIO3
# Адресу міняти перепаюванням резистора A0 на платі
OLED_ADDRESSES = [
    (0, 0x3C),  # OLED #1 — TCA9548A канал 0, адреса 0x3C
    (1, 0x3D),  # OLED #2 — TCA9548A канал 1, адреса 0x3D
    (2, 0x3C),  # OLED #3 — TCA9548A канал 2, адреса 0x3C
]
OLED_WIDTH  = 128
OLED_HEIGHT = 64

# ── IPS ST7789 (SPI) ────────────────────────────────────
IPS_WIDTH  = 320
IPS_HEIGHT = 170
IPS_DC_PIN  = 24   # GPIO24
IPS_RST_PIN = 25   # GPIO25
IPS_CS_PIN  = 8    # GPIO8  CE0
IPS_BL_PIN  = 18   # GPIO18 підсвітка (PWM)

# ── База даних ──────────────────────────────────────────
DB_PATH       = "/home/smartgrow/data/smartgrow.db"
DB_LOG_INTERVAL = 60   # секунд між записами

# ── Веб-сервер ──────────────────────────────────────────
WEB_HOST = "0.0.0.0"
WEB_PORT = 5000

# ── Сповіщення (cooldown між однаковими алертами) ───────
ALERT_COOLDOWN_SEC = 1800   # 30 хвилин

# ── Порогові значення алертів ───────────────────────────
ALERT_SOIL_CRITICAL = 20    # % — критично сухо
ALERT_TEMP_HIGH     = 80    # °C — занадто гаряче
ALERT_TEMP_LOW      = 10    # °C — занадто холодно
