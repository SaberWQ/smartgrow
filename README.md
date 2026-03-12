# SmartGrow Mini 🌱

Автономна мікротеплиця на Raspberry Pi 4B + DietPi з AI Telegram-ботом.  
Проєкт для Infomatrix Ukraine 2026.

---

## Структура проєкту

```
/home/smartgrow/
├── main.py                    ← точка входу
├── config.py                  ← всі налаштування
├── requirements.txt
├── .gitignore
│
├── core/
│   ├── sensors.py             ← ADS1115, DHT22, UPS HAT
│   ├── actuators.py           ← реле: насос + UV
│   ├── watering.py            ← автополив
│   └── scheduler.py           ← UV за розкладом
│
├── displays/
│   ├── oled_manager.py        ← OLED SSD1306 × 2 (I2C)
│   └── ips_manager.py         ← IPS ST7789 1.9" (SPI)
│
├── services/
│   ├── database.py            ← SQLite
│   ├── telegram_bot.py        ← бот + LangChain AI агент
│   └── alerts.py              ← критичні сповіщення
│
├── web/
│   ├── app.py                 ← Flask + SocketIO
│   └── templates/dashboard.html
│
├── deploy/
│   ├── install.sh             ← скрипт встановлення
│   ├── smartgrow.service      ← systemd unit
│   └── nginx.conf             ← nginx конфіг
│
├── data/
│   └── smartgrow.db           ← SQLite база (не в git)
└── logs/
    └── main.log               ← логи (не в git)
```

---

## Залежності (hardware)

| Компонент | Підключення |
|---|---|
| ADS1115 | I2C: SDA→GPIO2, SCL→GPIO3, ADDR→GND (0x48) |
| OLED #1 SSD1306 | I2C: 0x3C (нічого не паяти) |
| OLED #2 SSD1306 | I2C: 0x3D (перепаяти A0: GND→VCC) |
| IPS ST7789 1.9" | SPI: SCL→GPIO11, SDA→GPIO10, DC→GPIO24, RST→GPIO25, CS→GPIO8 |
| Реле 1 (Насос) | GPIO17 |
| Реле 2 (UV LED) | GPIO27 |
| UPS HAT (D) | I2C: 0x36 або 0x42 (автовизначення) |
| Датчики ґрунту | ADS1115: A0, A1 |

Перевірити I2C пристрої:
```bash
i2cdetect -y 1
```

---

## Деплой на Raspberry Pi

### Крок 1 — Завантажити код

```bash
# Варіант A: через git
cd /home
git clone https://github.com/SaberWQ/smartgrow smartgrow

# Варіант B: через SCP (з ПК)
scp smartgrow_final.zip root@<IP_RPi>:/home/
ssh root@<IP_RPi>
cd /home && unzip smartgrow_final.zip && mv sg2 smartgrow
```

### Крок 2 — Налаштувати конфіг

```bash
nano /home/smartgrow/config.py
```

Обов'язково змінити:
```python
TELEGRAM_TOKEN = "1234567890:AAFxxxx..."   # від @BotFather
TELEGRAM_CHAT  = "123456789"               # твій chat_id
OPENAI_API_KEY = "sk-proj-..."             # від platform.openai.com (необов'язково)
```

Як отримати TELEGRAM_CHAT:
```
1. Напиши боту @userinfobot
2. Він поверне твій chat_id
```

### Крок 3 — Встановити

```bash
cd /home/smartgrow
sudo bash deploy/install.sh
```

Скрипт автоматично:
- Активує I2C і SPI в `/boot/config.txt`
- Створює Python venv і встановлює всі пакети
- Ініціалізує SQLite базу
- Реєструє systemd сервіс (автозапуск)
- Налаштовує Nginx (якщо встановлений)

### Крок 4 — Калібровка датчиків ґрунту

```bash
cd /home/smartgrow
source venv/bin/activate
python3 - << 'EOF'
import board, busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import time

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
ch1 = AnalogIn(ads, ADS.P0)
ch2 = AnalogIn(ads, ADS.P1)

print("Датчики В ПОВІТРІ (сухо)...")
time.sleep(5)
dry1, dry2 = ch1.value, ch2.value
print(f"Сухо: ch1={dry1}  ch2={dry2}")

print("Датчики У ВОДІ (мокро)...")
time.sleep(5)
wet1, wet2 = ch1.value, ch2.value
print(f"Мокро: ch1={wet1}  ch2={wet2}")

print(f"\nВстав у config.py:")
print(f"SOIL_DRY = {max(dry1, dry2)}")
print(f"SOIL_WET  = {min(wet1, wet2)}")
EOF
```

Вставити отримані значення в `config.py` і перезапустити.

### Крок 5 — Запустити

```bash
systemctl start smartgrow
systemctl status smartgrow
```

---

## Команди керування

```bash
# Статус
systemctl status smartgrow

# Логи в реальному часі
journalctl -u smartgrow -f

# Або з файлу
tail -f /home/smartgrow/logs/main.log

# Перезапустити (після зміни коду)
systemctl restart smartgrow

# Зупинити
systemctl stop smartgrow

# Вбити старий процес на порту 5000
fuser -k 5000/tcp
```

---

## Веб-дашборд

Відкрити в браузері:
```
http://<IP_RPi>        # через Nginx (порт 80)
http://<IP_RPi>:5000   # напряму Flask
```

Дізнатись IP:
```bash
hostname -I
```

---

## Telegram бот

### Команди

| Команда | Дія |
|---|---|
| `/start` | Привітання і список команд |
| `/status` | Поточний стан системи |
| `/water` | Запустити полив вручну |
| `/uvon` | Увімкнути UV LED |
| `/uvoff` | Вимкнути UV LED |
| `/history` | Дані датчиків за годину |
| `/events` | Останні події системи |

### AI агент (якщо вставлено OPENAI_API_KEY)

Можна писати звичайною мовою:

```
"як справи у теплиці?"
"полий рослину"
"вимкни лампу"
"покажи дані за годину"
"температура занадто висока?"
```

Агент сам вибере потрібний інструмент і відповість.

---

## Оновлення коду

```bash
cd /home/smartgrow
git pull
systemctl restart smartgrow
```

---

## Типові помилки

| Помилка | Причина | Рішення |
|---|---|---|
| `Address already in use: 5000` | Старий процес | `fuser -k 5000/tcp` |
| `I2C device address invalid` | `OLED_ADDRESSES` — круглі дужки | Змінити `()` на `[]` в config.py |
| `No module named 'spidev'` | Не встановлено | `pip install spidev` |
| `No I2C device at 0x48` | ADS1115 не підключений | Перевірити провід, `i2cdetect -y 1` |
| `Remote I/O Error` | I2C не активовано | `raspi-config` → Interfaces → I2C |
| DHT22 постійно дає помилки | Нормально | Ігнорувати, код обробляє |
