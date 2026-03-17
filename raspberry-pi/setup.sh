#!/bin/bash
# SmartGrow - Raspberry Pi Setup Script
# Infomatrix Ukraine 2026

echo "╔═══════════════════════════════════════╗"
echo "║  SmartGrow Setup for Raspberry Pi 4   ║"
echo "║     AI-Powered Smart Greenhouse       ║"
echo "╚═══════════════════════════════════════╝"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo ./setup.sh)"
    exit 1
fi

ACTUAL_USER=${SUDO_USER:-pi}
HOME_DIR="/home/$ACTUAL_USER"
PROJECT_DIR="$HOME_DIR/smartgrow"

# Update system
echo "[1/8] Updating system packages..."
apt-get update
apt-get upgrade -y

# Install system dependencies
echo "[2/8] Installing system dependencies..."
apt-get install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-smbus \
    libgpiod2 \
    i2c-tools \
    python3-pil \
    python3-numpy \
    fonts-dejavu \
    libopenjp2-7 \
    libtiff5 \
    libfreetype6-dev \
    libatlas-base-dev

# Enable I2C and SPI
echo "[3/8] Enabling I2C and SPI interfaces..."
raspi-config nonint do_i2c 0
raspi-config nonint do_spi 0

# Add user to hardware groups
echo "[4/8] Adding user to gpio and i2c groups..."
usermod -a -G gpio,i2c,spi $ACTUAL_USER

# Create virtual environment
echo "[5/8] Creating Python virtual environment..."
cd $PROJECT_DIR/raspberry-pi
sudo -u $ACTUAL_USER python3 -m venv venv
sudo -u $ACTUAL_USER ./venv/bin/pip install --upgrade pip
sudo -u $ACTUAL_USER ./venv/bin/pip install -r requirements.txt

# Create data directory
echo "[6/8] Creating data directories..."
mkdir -p data
mkdir -p data/exports
mkdir -p logs
chown -R $ACTUAL_USER:$ACTUAL_USER data logs

# Install systemd service
echo "[7/8] Installing systemd service..."
cp smartgrow.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable smartgrow.service

# Test I2C
echo "[8/8] Testing I2C connection..."
echo "I2C devices found:"
i2cdetect -y 1

echo ""
echo "╔═══════════════════════════════════════╗"
echo "║         Setup Complete!               ║"
echo "╠═══════════════════════════════════════╣"
echo "║  GPIO Configuration:                  ║"
echo "║    Pump Relay:  GPIO 24               ║"
echo "║    UV Light:    GPIO 22               ║"
echo "║    Moisture:    GPIO 27               ║"
echo "║    I2C Displays: PCA9578A             ║"
echo "╠═══════════════════════════════════════╣"
echo "║  Commands:                            ║"
echo "║  Start:   systemctl start smartgrow   ║"
echo "║  Stop:    systemctl stop smartgrow    ║"
echo "║  Status:  systemctl status smartgrow  ║"
echo "║  Logs:    journalctl -u smartgrow -f  ║"
echo "╠═══════════════════════════════════════╣"
echo "║  API: http://$(hostname -I | awk '{print $1}'):8000      ║"
echo "║  Docs: http://$(hostname -I | awk '{print $1}'):8000/docs║"
echo "╚═══════════════════════════════════════╝"
echo ""
echo "Reboot recommended: sudo reboot"
