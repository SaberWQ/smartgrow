# SmartGrow - Raspberry Pi Controller

AI-powered Smart Greenhouse System for Infomatrix Ukraine 2026.

## Hardware Requirements

### Main Controller
- **Raspberry Pi 4 Model B** (2GB RAM, 128GB Storage)

### Sensors
- **Soil Moisture Sensor** (Capacitive) - via ADS1115 ADC
- **DHT22** - Temperature & Humidity sensor
- **Water Tank Level Sensor** (Capacitive) - via ADS1115 ADC

### Actuators
- **Water Pump** (3-6V DC) - via Relay module
- **UV LED Grow Strip** (12V) - via Relay + 5V to 12V converter

### Displays
- **SSD1306 OLED** (128x64) - Main dashboard (I2C)
- **SSD1306 OLED** (128x32) - Sensor display (I2C)
- **ST7789 IPS** (240x240) - Game interface (SPI)

### Additional Components
- **ADS1115** - 16-bit ADC for analog sensors (I2C)
- **I2C Expansion Module** - For multiple I2C devices
- **Relay Module** (2-channel) - For pump and UV light
- **5V to 12V Step-up Converter** - For UV LED strip

## Wiring Diagram

```
Raspberry Pi 4 GPIO Pinout:

GPIO 2 (SDA)  ─── I2C Data Bus
GPIO 3 (SCL)  ─── I2C Clock Bus
GPIO 4        ─── DHT22 Data
GPIO 17       ─── Pump Relay (IN)
GPIO 27       ─── UV LED Relay (IN)
GPIO 23       ─── IPS Backlight
GPIO 24       ─── IPS RST
GPIO 25       ─── IPS DC

I2C Bus:
├── ADS1115 ADC (0x48)
│   ├── A0: Soil Moisture Sensor
│   └── A1: Water Tank Sensor
├── SSD1306 OLED Main (0x3C)
└── SSD1306 OLED Sensors (0x3D)

SPI Bus:
└── ST7789 IPS Display

Power:
├── 5V ─── Raspberry Pi, Sensors, Relays
├── 3.3V ── Displays
└── 12V ─── UV LED Strip (via converter)
```

## Installation

1. Clone the repository to Raspberry Pi:
```bash
git clone https://github.com/SaberWQ/smartgrow.git
cd smartgrow/raspberry-pi
```

2. Run setup script:
```bash
sudo chmod +x setup.sh
sudo ./setup.sh
```

3. Edit configuration:
```bash
nano config.yaml
```

4. Start the service:
```bash
sudo systemctl start smartgrow
```

## Configuration

Edit `config.yaml` to customize:

- GPIO pin assignments
- ADC calibration values
- Automation thresholds
- Light schedule
- API server settings

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/sensors` | GET | Current sensor readings |
| `/api/sensors/history?hours=24` | GET | Historical data |
| `/api/water` | POST | Trigger watering |
| `/api/water/auto` | POST | Toggle auto-watering |
| `/api/light` | POST | Control UV light |
| `/api/light/auto` | POST | Toggle auto-lighting |
| `/api/light/schedule` | POST | Set light schedule |
| `/api/status` | GET | Full system status |
| `/api/analytics/stats` | GET | Statistics |
| `/api/analytics/predictions` | GET | Watering predictions |
| `/api/recommendations` | GET | AI recommendations |
| `/api/game/stats` | GET | Game statistics |
| `/api/events` | GET | Recent events |

## WebSocket Events

Connect to `ws://[pi-ip]:5000` for real-time updates:

- `sensors` - Real-time sensor data
- `event` - System events (watering, light changes, etc.)
- `status` - Full status updates

## Project Structure

```
raspberry-pi/
├── main.py              # Main controller
├── config.yaml          # Configuration
├── requirements.txt     # Python dependencies
├── setup.sh             # Installation script
├── sensors/
│   ├── soil_moisture.py
│   ├── temperature_humidity.py
│   └── water_tank.py
├── actuators/
│   ├── pump.py
│   └── uv_light.py
├── displays/
│   ├── oled_display.py
│   └── ips_display.py
├── analytics/
│   └── data_analyzer.py
├── api/
│   └── server.py
└── data/
    └── smartgrow.db
```

## Testing Individual Components

```bash
# Activate virtual environment
source venv/bin/activate

# Test soil moisture sensor
python -c "from sensors import SoilMoistureSensor; s = SoilMoistureSensor(); print(s.get_full_reading())"

# Test DHT22 sensor
python -c "from sensors import TemperatureHumiditySensor; s = TemperatureHumiditySensor(); print(s.get_full_reading())"

# Test water pump (WARNING: Will activate pump!)
python -c "from actuators import WaterPumpController; p = WaterPumpController(); p.start(2); p.cleanup()"

# Test OLED display
python -c "from displays import OLEDDisplay; d = OLEDDisplay(); d.show_sensor_dashboard({'moisture': 50, 'temperature': 24, 'humidity': 60, 'water_level': 75})"
```

## Troubleshooting

### I2C devices not detected
```bash
sudo i2cdetect -y 1
```
Should show addresses 0x3C, 0x3D (OLEDs), 0x48 (ADC)

### Permission denied for GPIO
```bash
sudo usermod -a -G gpio,spi,i2c pi
```

### Service not starting
```bash
journalctl -u smartgrow -f
```

## License

MIT License - Infomatrix Ukraine 2026
