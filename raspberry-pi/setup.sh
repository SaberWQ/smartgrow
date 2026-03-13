#!/bin/bash
# SmartGrow - Raspberry Pi Setup Script
# Infomatrix Ukraine 2026

echo "=================================="
echo "  SmartGrow Setup for Raspberry Pi"
echo "=================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo ./setup.sh)"
    exit 1
fi

# Update system
echo "[1/7] Updating system packages..."
apt-get update
apt-get upgrade -y

# Install system dependencies
echo "[2/7] Installing system dependencies..."
apt-get install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    libgpiod2 \
    i2c-tools \
    python3-pil \
    python3-numpy \
    fonts-dejavu \
    libopenjp2-7 \
    libtiff5 \
    libfreetype6-dev

# Enable I2C and SPI
echo "[3/7] Enabling I2C and SPI interfaces..."
raspi-config nonint do_i2c 0
raspi-config nonint do_spi 0

# Create virtual environment
echo "[4/7] Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "[5/7] Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create data directory
echo "[6/7] Creating data directories..."
mkdir -p data
mkdir -p data/exports
mkdir -p logs

# Create systemd service
echo "[7/7] Creating systemd service..."
cat > /etc/systemd/system/smartgrow.service << 'EOF'
[Unit]
Description=SmartGrow AI Greenhouse Controller
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/smartgrow
ExecStart=/home/pi/smartgrow/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable smartgrow.service

echo ""
echo "=================================="
echo "  Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Edit config.yaml to match your hardware setup"
echo "2. Test sensors: python -c 'from sensors import *; print(SoilMoistureSensor().read_percentage())'"
echo "3. Start service: sudo systemctl start smartgrow"
echo "4. View logs: journalctl -u smartgrow -f"
echo ""
echo "Web API will be available at: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
