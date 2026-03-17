"""
SmartGrow - Sensors Package
Infomatrix Ukraine 2026
"""

try:
    from .soil_moisture import SoilMoistureSensor
except ImportError:
    try:
        from .moisture import SoilMoistureSensor
    except ImportError:
        SoilMoistureSensor = None

try:
    from .temperature_humidity import TemperatureHumiditySensor
except ImportError:
    TemperatureHumiditySensor = None

try:
    from .water_tank import WaterTankSensor
except ImportError:
    WaterTankSensor = None

# Also export moisture module functions
try:
    from .moisture import read_moisture
except ImportError:
    read_moisture = None

__all__ = [
    'SoilMoistureSensor',
    'TemperatureHumiditySensor',
    'WaterTankSensor',
    'read_moisture'
]
