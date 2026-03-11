# SmartGrow Mini — Структура проєкту

## Дерево файлів

```
/home/smartgrow/
│
├── main.py              ← ТОЧКА ВХОДУ. Запускає всі потоки.
├── config.py            ← Всі налаштування (токен, піни, пороги)
│
├── core/                ← Апаратний рівень
│   ├── sensors.py       ← Читання ADS1115 + DHT22
│   ├── actuators.py     ← Керування реле (насос, UV)
│   ├── watering.py      ← Логіка автополиву
│   └── scheduler.py     ← UV розклад за годинником
│
├── displays/            ← Дисплеї
│   ├── oled_manager.py  ← OLED SSD1306 × 2 (I2C: 0x3C, 0x3D)
│   └── ips_manager.py   ← IPS ST7789 1.9" (SPI)
│
├── services/            ← Сервіси
│   ├── database.py      ← SQLite: запис/читання даних
│   ├── telegram_bot.py  ← Telegram бот + команди
│   └── alerts.py        ← Критичні сповіщення
│
├── web/                 ← Веб-дашборд
│   ├── app.py           ← Flask + SocketIO сервер
│   └── templates/
│       └── dashboard.html ← Живий дашборд з графіком
│
├── data/
│   └── smartgrow.db     ← SQLite база даних
│
└── logs/
    └── main.log         ← Логи системи
```

## Чому так, а не один файл

| Було | Стало |
|------|-------|
| main.py (все разом) | main.py → тільки запуск потоків |
| Падає один модуль → падає все | Кожен модуль ізольований |
| Важко дебажити | Логи по модулях: [sensors], [watering] |
| Важко змінювати | Зміна датчика → тільки sensors.py |
| Токен і піни розкидані по коду | Всі налаштування в config.py |

## Підключення OLED (кілька штук на одну шину)

```
Всі OLED паралельно:
  VCC → 3.3V
  GND → GND
  SDA → GPIO2 (Pin 3)
  SCL → GPIO3 (Pin 5)

Адреси:
  OLED #1 → 0x3C  (за замовчуванням)
  OLED #2 → 0x3D  (перепаяти A0: відключити від GND → підключити до VCC)
```

Перевірити: `i2cdetect -y 1`

## Запуск

```bash
cd /home/smartgrow
source venv/bin/activate
python main.py
```

## Команди Telegram

```
/status  — поточний стан
/water   — полив вручну
/uvon    — UV увімкнути
/uvoff   — UV вимкнути
/help    — довідка
```
