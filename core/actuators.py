# /home/smartgrow/core/actuators.py

import logging
from config import RELAY_PUMP, RELAY_UV

log = logging.getLogger("actuators")
GPIO_OK = False

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(RELAY_PUMP, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(RELAY_UV,   GPIO.OUT, initial=GPIO.HIGH)
    GPIO_OK = True
    log.info("GPIO OK")
except Exception as e:
    log.warning("GPIO not found: %s", e)


def pump_on():
    if GPIO_OK:
        GPIO.output(RELAY_PUMP, GPIO.LOW)
    log.info("PUMP ON")

def pump_off():
    if GPIO_OK:
        GPIO.output(RELAY_PUMP, GPIO.HIGH)
    log.info("PUMP OFF")

def uv_on():
    if GPIO_OK:
        GPIO.output(RELAY_UV, GPIO.LOW)
    log.info("UV ON")

def uv_off():
    if GPIO_OK:
        GPIO.output(RELAY_UV, GPIO.HIGH)
    log.info("UV OFF")

def cleanup():
    pump_off()
    uv_off()
    if GPIO_OK:
        GPIO.cleanup()
    log.info("GPIO cleanup")
