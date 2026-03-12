#!/bin/bash
# /home/smartgrow/deploy/install.sh
# Повне встановлення на DietPi / Raspberry Pi OS
# Запуск: sudo bash deploy/install.sh

set -e
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }

PROJECT=/home/smartgrow

log "Активація I2C і SPI..."
CONFIG=/boot/config.txt
grep -q "dtparam=i2c_arm=on" $CONFIG || echo "dtparam=i2c_arm=on"          >> $CONFIG
grep -q "dtparam=spi=on"     $CONFIG || echo "dtparam=spi=on"              >> $CONFIG
grep -q "i2c_baudrate"       $CONFIG || echo "dtparam=i2c_baudrate=400000" >> $CONFIG
modprobe i2c-dev    2>/dev/null || warn "i2c-dev: перезавантаж RPi"
modprobe spi-bcm2835 2>/dev/null || true

log "Директорії..."
mkdir -p $PROJECT/{logs,data}

log "Python venv..."
python3 -m venv $PROJECT/venv --system-site-packages
source $PROJECT/venv/bin/activate

log "pip пакети..."
pip install --upgrade pip -q
pip install -r $PROJECT/requirements.txt -q

log "SQLite DB..."
python3 -c "
import sys; sys.path.insert(0,'$PROJECT')
from services.database import init_db
init_db()
"

log "Systemd сервіс..."
cp $PROJECT/deploy/smartgrow.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable smartgrow

if command -v nginx &>/dev/null; then
    log "Nginx..."
    cp $PROJECT/deploy/nginx.conf /etc/nginx/sites-available/smartgrow
    ln -sf /etc/nginx/sites-available/smartgrow /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    nginx -t && systemctl restart nginx
else
    warn "Nginx не знайдено — дашборд на порту 5000"
fi

IP=$(hostname -I | awk '{print $1}')
echo ""
echo -e "${GREEN}=== Готово! ===${NC}"
echo "1. Вставити токени в config.py:"
echo "   nano $PROJECT/config.py"
echo ""
echo "2. Запустити:"
echo "   systemctl start smartgrow"
echo ""
echo "3. Дашборд: http://$IP"
echo "4. Логи:    journalctl -u smartgrow -f"
