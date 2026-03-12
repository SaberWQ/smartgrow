# /home/smartgrow/core/sensors.py

import logging
from config import SOIL_DRY, SOIL_WET

log = logging.getLogger("sensors")

ADS_OK = False
_soil1 = None
_soil2 = None

try:
    import board, busio
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
    _i2c      = busio.I2C(board.SCL, board.SDA)
    _ads      = ADS.ADS1115(_i2c)
    _ads.gain = 1
    _soil1    = AnalogIn(_ads, ADS.P0)
    _soil2    = AnalogIn(_ads, ADS.P1)
    ADS_OK    = True
    log.info("ADS1115 OK")
except Exception as e:
    log.warning("ADS1115 not found: %s", e)

DHT_OK = False
_dht   = None

try:
    import board
    import adafruit_dht
    _dht   = adafruit_dht.DHT22(board.D4)
    DHT_OK = True
    log.info("DHT22 OK")
except Exception as e:
    log.warning("DHT22 not found: %s", e)

_ups_mode = None
_smbus    = None

try:
    import smbus2
    _smbus = smbus2.SMBus(1)
    _smbus.read_byte_data(0x42, 0x00)
    _ups_mode = "ina219"
    log.info("UPS HAT INA219 @ 0x42 OK")
except Exception:
    try:
        _smbus.read_byte_data(0x36, 0x02)
        _ups_mode = "max17040"
        log.info("UPS HAT MAX17040 @ 0x36 OK")
    except Exception as e:
        log.warning("UPS HAT not found: %s", e)

_V_FULL  = 8.40
_V_EMPTY = 6.00


def _raw_to_pct(raw):
    pct = (SOIL_DRY - raw) / (SOIL_DRY - SOIL_WET) * 100
    return max(0, min(100, int(pct)))


def read_soil():
    if not ADS_OK:
        return 0, 0
    try:
        return _raw_to_pct(_soil1.value), _raw_to_pct(_soil2.value)
    except Exception as e:
        log.error("read_soil: %s", e)
        return 0, 0


def read_dht():
    if not DHT_OK:
        return 0.0, 0.0
    try:
        t = _dht.temperature
        h = _dht.humidity
        return (round(t, 1) if t else 0.0,
                round(h, 1) if h else 0.0)
    except Exception:
        return 0.0, 0.0


def read_battery():
    if _ups_mode is None:
        return 100, 0.0
    try:
        if _ups_mode == "ina219":
            raw   = _smbus.read_word_data(0x42, 0x02)
            raw   = ((raw & 0xFF) << 8) | (raw >> 8)
            volts = ((raw >> 3) * 4) / 1000.0
            pct   = max(0, min(100, int(
                (volts - _V_EMPTY) / (_V_FULL - _V_EMPTY) * 100)))
            return pct, round(volts, 2)
        elif _ups_mode == "max17040":
            vcell = _smbus.read_word_data(0x36, 0x02)
            vcell = ((vcell & 0xFF) << 8) | (vcell >> 8)
            volts = (vcell >> 4) * 1.25 / 1000.0
            soc   = _smbus.read_word_data(0x36, 0x04)
            soc   = ((soc & 0xFF) << 8) | (soc >> 8)
            pct   = max(0, min(100, soc >> 8))
            return pct, round(volts, 2)
    except Exception as e:
        log.error("read_battery: %s", e)
    return 100, 0.0
