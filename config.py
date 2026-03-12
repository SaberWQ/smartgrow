# /home/smartgrow/config.py

# ── Telegram ─────────────────────────────────────────────────
TELEGRAM_TOKEN   = "ВСТАВТЕ_ТОКЕН_ТУТ"
TELEGRAM_CHAT    = "ВСТАВТЕ_CHAT_ID_ТУТ"

# ── OpenAI (для LangChain агента) ────────────────────────────
OPENAI_API_KEY   = "ВСТАВТЕ_OPENAI_KEY_ТУТ"
OPENAI_MODEL     = "gpt-4o-mini"   # дешевший і швидкий

# ── GPIO ─────────────────────────────────────────────────────
RELAY_PUMP  = 17
RELAY_UV    = 27

# ── Автополив ────────────────────────────────────────────────
SOIL_MIN     = 40
SOIL_MAX     = 75
PUMP_MAX_SEC = 10

# ── Калібровка ADS1115 (виміряй сам!) ────────────────────────
SOIL_DRY = 17000   # сирий ADC у сухому ґрунті
SOIL_WET  = 7000   # сирий ADC у мокрому ґрунті

# ── UV розклад ───────────────────────────────────────────────
UV_ON_HOUR  = 7
UV_OFF_HOUR = 22

# ── OLED (I2C) ───────────────────────────────────────────────
# ВАЖЛИВО: квадратні дужки [], НЕ круглі ()
OLED_ADDRESSES = [0x3C, 0x3D]
OLED_WIDTH     = 128
OLED_HEIGHT    = 64

# ── IPS ST7789 (SPI) ─────────────────────────────────────────
IPS_WIDTH   = 320
IPS_HEIGHT  = 170
IPS_DC_PIN  = 24
IPS_RST_PIN = 25
IPS_CS_PIN  = 8
IPS_BL_PIN  = 18

# ── База даних ───────────────────────────────────────────────
DB_PATH         = "/home/smartgrow/data/smartgrow.db"
DB_LOG_INTERVAL = 60

# ── Веб-сервер ───────────────────────────────────────────────
WEB_HOST = "0.0.0.0"
WEB_PORT = 5000

# ── Алерти ───────────────────────────────────────────────────
ALERT_COOLDOWN_SEC  = 1800
ALERT_SOIL_CRITICAL = 20
ALERT_TEMP_HIGH     = 35
ALERT_TEMP_LOW      = 10
