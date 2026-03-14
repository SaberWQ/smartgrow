# SmartGrow - AI Plant Pet Smart Greenhouse

<div align="center">

![SmartGrow Logo](https://img.shields.io/badge/SmartGrow-Plant%20Pet%20AI-green?style=for-the-badge&logo=leaf&logoColor=white)

**Your plant becomes a talking virtual pet that controls a real greenhouse**

[![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi%204-C51A4A?style=flat-square&logo=raspberry-pi)](https://www.raspberrypi.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)](https://python.org)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react)](https://reactjs.org)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20AI-orange?style=flat-square)](https://ollama.ai)

[Demo](https://smartgrow.example.com) | [Documentation](#documentation) | [Hardware Setup](#hardware-setup) | [Installation](#installation)

</div>

---

## Overview

SmartGrow is a hybrid **IoT + AI + Game** platform where your plant becomes a **talking virtual pet**. The plant has emotions, gives you quests, and controls a real greenhouse. All AI runs **100% locally** on Raspberry Pi using Ollama.

### Key Features

- **Plant Pet AI**: Your plant talks, has moods, and gives you missions
- **Voice Interaction**: Talk to your plant using VOSK + Coqui TTS
- **Local AI Brain**: Ollama (mistral/llama3) runs entirely on Raspberry Pi
- **3D Emotional Plant**: React Three Fiber plant with facial expressions
- **Real-time Monitoring**: Soil moisture, temperature, humidity, water level
- **PID Auto-Watering**: Intelligent irrigation with PID controller
- **Plant Vision**: YOLOv8 + OpenCV for disease detection
- **Gamification**: XP, levels, achievements, daily quests from plant
- **Remote Access**: Cloudflare Tunnel for secure internet access

---

## System Architecture

```
                    INTERNET
                       │
                       ▼
              ┌─────────────────┐
              │  SmartGrow Web  │◄────── 3D Plant Pet
              │   Application   │        with emotions
              │  (React + R3F)  │        & voice chat
              └────────┬────────┘
                       │ HTTPS
                       ▼
              ┌─────────────────┐
              │   Cloudflare    │
              │     Tunnel      │
              └────────┬────────┘
                       │
                       ▼
    ┌──────────────────────────────────────────────┐
    │              Raspberry Pi 4                  │
    │  ┌─────────────────────────────────────────┐ │
    │  │           FastAPI Server (8000)         │ │
    │  │  ┌──────────┬───────────┬────────────┐  │ │
    │  │  │   PID    │  Ollama   │   SQLite   │  │ │
    │  │  │Controller│ AI Brain  │  Database  │  │ │
    │  │  └──────────┴───────────┴────────────┘  │ │
    │  │  ┌──────────┬───────────┐               │ │
    │  │  │   VOSK   │  Coqui    │ ◄── Voice    │ │
    │  │  │   STT    │   TTS     │    Pipeline  │ │
    │  │  └──────────┴───────────┘               │ │
    │  └─────────────────────────────────────────┘ │
    │                    │                         │
    │    ┌───────────────┼───────────────┐         │
    │    │               │               │         │
    │    ▼               ▼               ▼         │
    │ ┌──────┐      ┌──────────┐    ┌──────────┐   │
    │ │Sensors│      │ Displays │    │ Actuators│  │
    │ │DHT22 │      │  OLED    │    │  Pump    │   │
    │ │Soil  │      │  IPS     │    │  UV LED  │   │
    │ │Water │      └──────────┘    │  Camera  │   │
    │ └──────┘                      └──────────┘   │
    └──────────────────────────────────────────────┘
```

### Plant Pet Personality

Your plant pet has:
- **Moods**: happy, thirsty, hot, cold, sick, sleepy, excited
- **Facial Expressions**: Eyes, mouth, blush effects in 3D
- **Voice**: Speaks through Coqui TTS
- **Quests**: Gives you missions for XP rewards

---

## Hardware Setup

### Required Components

| Component | Model | Quantity | GPIO/Interface |
|-----------|-------|----------|----------------|
| Raspberry Pi | 4 Model B (2GB+) | 1 | - |
| Soil Moisture Sensor | Capacitive | 1 | ADC (ADS1115) |
| Temperature/Humidity | DHT22 | 1 | GPIO 4 |
| Water Level Sensor | HC-SR04 | 1 | GPIO 23, 24 |
| Water Pump | 3-6V Submersible | 1 | GPIO 17 (Relay) |
| UV LED Strip | 12V Purple | 1 | GPIO 27 (Relay) |
| Relay Module | 2-Channel | 1 | GPIO 17, 27 |
| ADC Converter | ADS1115 | 1 | I2C (0x48) |
| OLED Display | SSD1306 128x64 | 1 | I2C (0x3C) |
| IPS Display | ST7789 240x240 | 1 | SPI |
| Voltage Converter | 5V to 12V | 1 | - |
| I2C Expander | PCF8574 | 1 | I2C |
| Power Supply | 5V 3A | 1 | USB-C |

### Wiring Diagram

```
Raspberry Pi 4 GPIO Pinout
═══════════════════════════════════════════════════════

                    ┌─────────────────────┐
                    │    Raspberry Pi 4   │
                    │                     │
   3.3V Power ──────┤ 1  (3V3)   (5V)  2 ├────── 5V Power
   I2C SDA ─────────┤ 3  (SDA)   (5V)  4 ├────── 5V Power
   I2C SCL ─────────┤ 5  (SCL)  (GND)  6 ├────── Ground
   DHT22 Data ──────┤ 7  (GP4) (TXD0)  8 ├
                    ├ 9  (GND) (RXD0) 10 ├
   Pump Relay ──────┤11 (GP17) (GP18) 12 ├
   UV LED Relay ────┤13 (GP27) (GND)  14 ├────── Ground
                    ├15 (GP22) (GP23) 16 ├────── Water Sensor TRIG
                    ├17  (3V3) (GP24) 18 ├────── Water Sensor ECHO
   SPI MOSI ────────┤19 (MOSI) (GND)  20 ├────── Ground
   SPI MISO ────────┤21 (MISO) (GP25) 22 ├
   SPI SCLK ────────┤23 (SCLK) (CE0)  24 ├────── IPS Display CS
                    ├25  (GND) (CE1)  26 ├
                    ├27 (ID_SD)(ID_SC)28 ├
                    ├29  (GP5) (GND)  30 ├────── Ground
                    ├31  (GP6) (GP12) 32 ├
   IPS DC Pin ──────┤33 (GP13) (GND)  34 ├────── Ground
   IPS Backlight ───┤35 (GP19) (GP16) 36 ├
                    ├37 (GP26) (GP20) 38 ├
                    ├39  (GND) (GP21) 40 ├────── IPS Reset
                    └─────────────────────┘

I2C Bus (Pin 3, 5):
├── ADS1115 ADC (0x48) ← Soil Moisture Sensor
├── SSD1306 OLED (0x3C)
└── PCF8574 Expander (0x20)

SPI Bus (Pin 19, 21, 23, 24):
└── ST7789 IPS Display

Relay Module:
├── Channel 1 (GPIO 17) → Water Pump (3-6V)
└── Channel 2 (GPIO 27) → 5V→12V Converter → UV LED Strip
```

### I2C Connection Diagram

```
┌──────────────────────────────────────────────────────────┐
│                     I2C Bus Wiring                        │
├──────────────────────────────────────────────────────────┤
│                                                          │
│   Raspberry Pi                                           │
│   ┌─────────┐                                            │
│   │ Pin 1   │───────────────────── 3.3V ────┬───────┐    │
│   │ Pin 3   │───────────────────── SDA ─────┼───┬───┤    │
│   │ Pin 5   │───────────────────── SCL ─────┼───┼───┤    │
│   │ Pin 6   │───────────────────── GND ─────┼───┼───┤    │
│   └─────────┘                               │   │   │    │
│                                             │   │   │    │
│   ┌─────────────┐   ┌─────────────┐   ┌─────┴───┴───┴──┐ │
│   │  ADS1115    │   │  SSD1306    │   │   PCF8574      │ │
│   │ ADC (0x48)  │   │ OLED (0x3C) │   │ Expander(0x20) │ │
│   │             │   │             │   │                │ │
│   │ A0 ← Soil   │   │ 128x64 px   │   │ Extra GPIO     │ │
│   │    Moisture │   │             │   │                │ │
│   └─────────────┘   └─────────────┘   └────────────────┘ │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## Installation

### Prerequisites

- Raspberry Pi 4 with Raspberry Pi OS (64-bit recommended)
- Python 3.11+
- Node.js 20+
- Git

### 1. Clone Repository

```bash
git clone https://github.com/SaberWQ/smartgrow.git
cd smartgrow
```

### 2. Raspberry Pi Setup

```bash
# Navigate to Raspberry Pi directory
cd raspberry-pi

# Run setup script (installs dependencies, enables interfaces)
chmod +x setup.sh
sudo ./setup.sh

# Create Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Copy and edit configuration
cp config.yaml.example config.yaml
nano config.yaml
```

### 3. Configure Environment

Create `.env` file:

```bash
# Raspberry Pi .env
GEMINI_API_KEY=your_gemini_api_key
SMARTGROW_ENV=production
```

### 4. Enable I2C and SPI

```bash
sudo raspi-config
# Navigate to: Interface Options → I2C → Enable
# Navigate to: Interface Options → SPI → Enable
sudo reboot
```

### 5. Test Hardware

```bash
# Test I2C devices
i2cdetect -y 1

# Expected output:
#      0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
# 20: 20 -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 30: -- -- -- -- -- -- -- -- -- -- -- -- 3c -- -- --
# 40: -- -- -- -- -- -- -- -- 48 -- -- -- -- -- -- --

# Run hardware test
python3 -c "from sensors import SoilMoistureSensor; s = SoilMoistureSensor(); print(s.read())"
```

### 6. Start Server

```bash
# Development mode
python3 main.py

# Production mode (with systemd)
sudo cp deploy/smartgrow.service /etc/systemd/system/
sudo systemctl enable smartgrow
sudo systemctl start smartgrow
```

---

## Frontend Setup

### 1. Install Dependencies

```bash
# From project root
npm install
# or
pnpm install
```

### 2. Configure Environment

```bash
# Create .env.local
VITE_PI_API_URL=http://your-raspberry-pi:8000
VITE_GEMINI_API_KEY=your_gemini_api_key
```

### 3. Run Development Server

```bash
npm run dev
```

### 4. Build for Production

```bash
npm run build
```

---

## Internet Access (Cloudflare Tunnel)

### Setup Steps

```bash
# On Raspberry Pi
cd raspberry-pi/deploy

# Set environment variables
export TUNNEL_NAME="smartgrow"
export DOMAIN="smartgrow.yourdomain.com"
export LOCAL_PORT=8000

# Run setup script
sudo chmod +x cloudflare_tunnel.sh
sudo ./cloudflare_tunnel.sh
```

### Configure DNS

```bash
# After tunnel is created
cloudflared tunnel route dns smartgrow smartgrow.yourdomain.com
```

### Verify Connection

```bash
# Check tunnel status
sudo systemctl status cloudflared

# Test from internet
curl https://smartgrow.yourdomain.com/sensors
```

---

## API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/sensors` | Get current sensor readings |
| GET | `/status` | Get system status |
| POST | `/water` | Trigger watering |
| POST | `/light` | Control UV light |
| POST | `/auto-mode` | Toggle auto modes |
| GET | `/analytics` | Get analytics data |
| POST | `/ai/analyze` | Trigger AI plant analysis |
| GET | `/pid/status` | Get PID controller status |
| PUT | `/pid/tune` | Tune PID parameters |
| GET | `/game/stats` | Get game statistics |
| WS | `/ws` | Real-time WebSocket stream |

### Example Requests

```bash
# Get sensor data
curl http://localhost:8000/sensors

# Trigger watering
curl -X POST http://localhost:8000/water \
  -H "Content-Type: application/json" \
  -d '{"duration": 3}'

# Set auto-watering
curl -X POST http://localhost:8000/auto-mode \
  -H "Content-Type: application/json" \
  -d '{"auto_water": true, "threshold": 40}'

# Tune PID
curl -X PUT http://localhost:8000/pid/tune \
  -H "Content-Type: application/json" \
  -d '{"kp": 2.5, "ki": 0.1, "kd": 0.5}'
```

---

## PID Tuning Guide

The PID controller maintains optimal soil moisture. Tune parameters for your plant type:

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `target_moisture` | 45% | Target soil moisture |
| `Kp` | 2.0 | Proportional gain - response speed |
| `Ki` | 0.1 | Integral gain - eliminates steady-state error |
| `Kd` | 0.5 | Derivative gain - reduces overshoot |
| `deadband` | 3% | Error tolerance before action |

### Tuning Process

1. **Start Conservative**
   ```yaml
   kp: 1.0
   ki: 0.05
   kd: 0.2
   ```

2. **Increase Kp** until system responds quickly but doesn't overshoot

3. **Add Ki** slowly to eliminate steady-state error

4. **Add Kd** to reduce oscillation

### Plant-Specific Presets

```yaml
# Herbs (Basil, Mint)
target_moisture: 50
kp: 2.0
ki: 0.1
kd: 0.5

# Succulents
target_moisture: 30
kp: 1.5
ki: 0.05
kd: 0.3

# Tropical Plants
target_moisture: 60
kp: 2.5
ki: 0.15
kd: 0.6
```

---

## Game Mechanics

### Progression System

| Level | XP Required | Unlocks |
|-------|-------------|---------|
| 1 | 0 | Basic watering |
| 2 | 100 | UV light control |
| 3 | 300 | Auto-watering |
| 4 | 600 | AI recommendations |
| 5 | 1000 | PID tuning |
| 6 | 1500 | Advanced analytics |
| 7 | 2200 | Custom schedules |
| 8 | 3000 | Multi-plant support |
| 9 | 4000 | Expert mode |
| 10 | 5500 | Master Gardener |

### Achievements

- **First Drop**: Complete first watering
- **Green Thumb**: Keep plant healthy for 7 days
- **Plant Whisperer**: Complete 50 AI consultations
- **Night Owl**: Adjust lighting schedule
- **Data Scientist**: View analytics 10 times
- **Automation Master**: Enable all auto modes
- **Perfect Week**: Complete all daily tasks for 7 days
- **Growth Champion**: Reach mature plant stage

### Daily Quests

1. **Morning Hydration**: Check moisture and water if needed (+25 XP)
2. **Sensor Patrol**: Review all sensor readings (+15 XP)
3. **Light Guardian**: Optimize UV light settings (+30 XP)
4. **AI Consultation**: Ask AI for plant tips (+20 XP)
5. **Photo Journal**: Capture plant photo (+35 XP)

---

## Troubleshooting

### Common Issues

**I2C Devices Not Detected**
```bash
# Enable I2C
sudo raspi-config nonint do_i2c 0
sudo reboot

# Check connections
i2cdetect -y 1
```

**Pump Not Working**
```bash
# Test GPIO
python3 -c "
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)
GPIO.output(17, GPIO.HIGH)
import time; time.sleep(2)
GPIO.output(17, GPIO.LOW)
GPIO.cleanup()
"
```

**Camera Not Found**
```bash
# Enable camera
sudo raspi-config nonint do_camera 0
sudo reboot

# Test camera
rpicam-still -o test.jpg
```

**Cloudflare Tunnel Issues**
```bash
# Check logs
sudo journalctl -u cloudflared -f

# Restart tunnel
sudo systemctl restart cloudflared
```

---

## Project Structure

```
smartgrow/
├── raspberry-pi/           # Raspberry Pi backend
│   ├── sensors/            # Sensor modules
│   │   ├── soil_moisture.py
│   │   ├── temperature_humidity.py
│   │   └── water_tank.py
│   ├── actuators/          # Actuator modules
│   │   ├── pump.py
│   │   └── uv_light.py
│   ├── displays/           # Display modules
│   │   ├── oled_display.py
│   │   └── ips_display.py
│   ├── analytics/          # Data analytics
│   │   └── data_analyzer.py
│   ├── ai/                 # AI plant analysis
│   │   └── plant_analyzer.py
│   ├── pid/                # PID controller
│   │   └── controller.py
│   ├── database/           # SQLite database
│   │   └── models.py
│   ├── api/                # FastAPI server
│   │   └── server.py
│   ├── deploy/             # Deployment scripts
│   │   ├── smartgrow.service
│   │   └── cloudflare_tunnel.sh
│   ├── config.yaml         # Configuration
│   ├── main.py             # Entry point
│   └── requirements.txt    # Python dependencies
│
├── src/                    # Frontend (React)
│   ├── components/         # React components
│   │   ├── Plant3D.tsx     # 3D plant visualization
│   │   ├── SensorCard.tsx
│   │   ├── ControlPanel.tsx
│   │   ├── AIAssistant.tsx
│   │   └── GamePanel.tsx
│   ├── services/           # API services
│   │   ├── raspberryPiApi.ts
│   │   └── gemini.ts
│   ├── App.tsx             # Main app
│   └── types.ts            # TypeScript types
│
├── package.json            # Node.js dependencies
├── vite.config.ts          # Vite configuration
└── README.md               # This file
```

---

## Demo Instructions

### For Hackathon Presentation

1. **Power On** the Raspberry Pi greenhouse
2. **Wait** for system boot (LED indicators)
3. **Open** web dashboard: `https://smartgrow.yourdomain.com`
4. **Demonstrate**:
   - Real-time sensor readings
   - 3D plant responds to data
   - Manual watering (pump activates)
   - UV light control
   - AI plant analysis
   - Game achievements

### Demo Script

```
1. "This is SmartGrow - an AI-powered smart greenhouse"
2. "Real sensors monitor soil, temperature, and humidity"
3. "The 3D plant shows real-time health status"
4. "Watch as I trigger watering..." [click water button]
5. "The PID controller optimizes water usage"
6. "AI analyzes plant health using computer vision"
7. "Gamification makes plant care engaging"
8. "All accessible remotely via Cloudflare Tunnel"
```

---

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- **Infomatrix Ukraine 2026** - Hackathon organizers
- **Google Gemini** - AI plant analysis
- **Raspberry Pi Foundation** - Hardware platform
- **Cloudflare** - Secure tunnel infrastructure

---

<div align="center">

**Built with love for sustainable agriculture**

Made for Infomatrix Ukraine 2026

</div>
