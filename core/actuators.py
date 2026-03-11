"""
core/actuators.py
Керування реле: насос 12V і UV LED 12V
HIGH = реле вимкнено (нормально розімкнутий контакт)
LOW  = реле увімкнено
"""

import logging
from config import RELAY_PUMP, RELAY_UV

log = logging.getLogger("actuators")

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(RELAY_PUMP, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(RELAY_UV,   GPIO.OUT, initial=GPIO.HIGH)
    GPIO_OK = True
    log.info("GPIO ✓")
except Exception as e:
    GPIO_OK = False
    log.warning(f"GPIO не знайдено: {e}")


def pump_on():
    if GPIO_OK:
        GPIO.output(RELAY_PUMP, GPIO.LOW)
    log.info("🚿 Насос ON")

def pump_off():
    if GPIO_OK:
        GPIO.output(RELAY_PUMP, GPIO.HIGH)
    log.info("⏹  Насос OFF")

def uv_on():
    if GPIO_OK:
        GPIO.output(RELAY_UV, GPIO.LOW)
    log.info("💜 UV ON")

def uv_off():
    if GPIO_OK:
        GPIO.output(RELAY_UV, GPIO.HIGH)
    log.info("⏹  UV OFF")

def cleanup():
    """Викликати при завершенні програми"""
    pump_off()
    uv_off()
    if GPIO_OK:
        GPIO.cleanup()
    log.info("GPIO cleanup ✓")
