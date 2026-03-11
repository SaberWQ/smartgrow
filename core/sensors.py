"""
core/sensors.py
Читання:
  - ADS1115       → вологість ґрунту (2 датчики)
  - DHT22         → температура + вологість повітря
  - UPS HAT (D)   → напруга та заряд батареї 2S 21700

UPS HAT (D) I2C адреса: 0x36 (MAX17040 або INA219 залежно від ревізії)
Перевірити: i2cdetect -y 1
"""

import logging
from config import SOIL_DRY, SOIL_WET

log = logging.getLogger("sensors")

# ── ADS1115 ─────────────────────────────────────────────
try:
    import board, busio
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn

    _i2c     = busio.I2C(board.SCL, board.SDA)
    _ads     = ADS.ADS1115(_i2c)
    _ads.gain = 1
    _soil1   = AnalogIn(_ads, ADS.P0)   # Датчик ґрунту 1 → A0
    _soil2   = AnalogIn(_ads, ADS.P1)   # Датчик ґрунту 2 → A1
    ADS_OK   = True
    log.info("ADS1115 ✓")
except Exception as e:
    ADS_OK = False
    log.warning(f"ADS1115 не знайдено: {e}")

# ── DHT22 ───────────────────────────────────────────────
try:
    import adafruit_dht
    _dht   = adafruit_dht.DHT22(board.D4)
    DHT_OK = True
    log.info("DHT22 ✓")
except Exception as e:
    DHT_OK = False
    log.warning(f"DHT22 не знайдено: {e}")


def _raw_to_pct(raw: int) -> int:
    """Перетворити сирий ADC → відсоток вологості 0-100%"""
    pct = (SOIL_DRY - raw) / (SOIL_DRY - SOIL_WET) * 100
    return max(0, min(100, int(pct)))


def read_soil() -> tuple[int, int]:
    """Повертає (soil1_pct, soil2_pct). При помилці — (0, 0)."""
    if not ADS_OK:
        return 0, 0
    try:
        return _raw_to_pct(_soil1.value), _raw_to_pct(_soil2.value)
    except Exception as e:
        log.error(f"read_soil: {e}")
        return 0, 0


def read_dht() -> tuple[float, float]:
    """Повертає (temp_C, humidity_pct). При помилці — (0.0, 0.0)."""
    if not DHT_OK:
        return 0.0, 0.0
    try:
        t = _dht.temperature
        h = _dht.humidity
        return (round(t, 1) if t else 0.0,
                round(h, 1) if h else 0.0)
    except Exception as e:
        log.debug(f"read_dht (DHT часто дає збій): {e}")
        return 0.0, 0.0


# ── UPS HAT (D) — заряд батареї ─────────────────────────
# UPS HAT (D) використовує INA219 (0x42) або MAX17040 (0x36)
# Спробуємо обидва варіанти
_ups_mode = None   # "ina219" | "max17040" | None

try:
    import smbus2
    _smbus = smbus2.SMBus(1)

    # Спробуємо INA219 @ 0x42
    _smbus.read_byte_data(0x42, 0x00)
    _ups_mode = "ina219"
    log.info("UPS HAT INA219 @ 0x42 ✓")
except Exception:
    try:
        # Спробуємо MAX17040 @ 0x36
        _smbus.read_byte_data(0x36, 0x02)
        _ups_mode = "max17040"
        log.info("UPS HAT MAX17040 @ 0x36 ✓")
    except Exception as e:
        log.warning(f"UPS HAT не знайдено: {e} — заряд буде 100%")

# Межі напруги для 2S Li-Ion (21700)
_V_FULL = 8.40   # В — 100%
_V_EMPTY = 6.00  # В — 0%


def _voltage_to_pct(volts: float) -> int:
    """Перетворити напругу 2S акумулятора → відсоток заряду."""
    pct = (volts - _V_EMPTY) / (_V_FULL - _V_EMPTY) * 100
    return max(0, min(100, int(pct)))


def read_battery() -> tuple[int, float]:
    """
    Повертає (battery_pct, voltage_V).
    При помилці — (100, 0.0).
    """
    if _ups_mode is None:
        return 100, 0.0

    try:
        if _ups_mode == "ina219":
            # INA219: регістр напруги шини 0x02, LSB = 4мВ
            raw = _smbus.read_word_data(0x42, 0x02)
            # Swap bytes (big-endian)
            raw = ((raw & 0xFF) << 8) | (raw >> 8)
            volts = ((raw >> 3) * 4) / 1000.0
            return _voltage_to_pct(volts), round(volts, 2)

        elif _ups_mode == "max17040":
            # MAX17040: регістр VCELL 0x02 і SOC 0x04
            vcell = _smbus.read_word_data(0x36, 0x02)
            vcell = ((vcell & 0xFF) << 8) | (vcell >> 8)
            volts = (vcell >> 4) * 1.25 / 1000.0

            soc_raw = _smbus.read_word_data(0x36, 0x04)
            soc_raw = ((soc_raw & 0xFF) << 8) | (soc_raw >> 8)
            pct = soc_raw >> 8

            return max(0, min(100, pct)), round(volts, 2)

    except Exception as e:
        log.error(f"read_battery: {e}")
        return 100, 0.0
