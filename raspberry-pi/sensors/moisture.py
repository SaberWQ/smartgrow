"""
SmartGrow - Soil Moisture Sensor Module
Reads soil moisture via GPIO 27 (digital) or ADC (analog)
"""

import time
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime

try:
    import RPi.GPIO as GPIO
    RPI_AVAILABLE = True
except ImportError:
    RPI_AVAILABLE = False
    print("[MOISTURE] RPi.GPIO not available - simulation mode")

try:
    import smbus2
    SMBUS_AVAILABLE = True
except ImportError:
    SMBUS_AVAILABLE = False
    print("[MOISTURE] smbus2 not available - ADC disabled")


# GPIO Configuration
MOISTURE_SENSOR_PIN = 27  # Digital moisture sensor on GPIO 27

# ADC Configuration (ADS1115 for analog reading)
ADS1115_ADDRESS = 0x48
I2C_BUS = 1

# Calibration values (adjust based on your sensor)
DRY_VALUE = 1023      # ADC value when soil is completely dry
WET_VALUE = 300       # ADC value when soil is completely wet

# Thresholds
MOISTURE_LOW = 30     # Below this = needs water
MOISTURE_HIGH = 70    # Above this = too wet
MOISTURE_OPTIMAL = 45 # Target moisture level


@dataclass
class MoistureReading:
    """Single moisture reading"""
    raw_value: int
    percentage: float
    is_dry: bool
    is_wet: bool
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MoistureStats:
    """Moisture sensor statistics"""
    readings_count: int = 0
    average_moisture: float = 0.0
    min_moisture: float = 100.0
    max_moisture: float = 0.0
    last_reading: Optional[MoistureReading] = None
    history: List[float] = field(default_factory=list)


class SoilMoistureSensor:
    """
    Soil moisture sensor reader.
    
    Supports both:
    - Digital reading via GPIO (wet/dry threshold)
    - Analog reading via ADS1115 ADC (precise percentage)
    """
    
    def __init__(
        self,
        gpio_pin: int = MOISTURE_SENSOR_PIN,
        use_adc: bool = False,
        adc_address: int = ADS1115_ADDRESS,
        adc_channel: int = 0,
        simulation: bool = False
    ):
        self.gpio_pin = gpio_pin
        self.use_adc = use_adc
        self.adc_address = adc_address
        self.adc_channel = adc_channel
        self.simulation = simulation or not RPI_AVAILABLE
        
        self.stats = MoistureStats()
        self._bus = None
        
        if not self.simulation:
            self._setup_gpio()
            if use_adc and SMBUS_AVAILABLE:
                self._setup_adc()
        
        print(f"[MOISTURE] Initialized on GPIO {gpio_pin} (ADC={use_adc}, sim={self.simulation})")
    
    def _setup_gpio(self):
        """Initialize GPIO for digital moisture sensor"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(self.gpio_pin, GPIO.IN)
            print(f"[MOISTURE] GPIO {self.gpio_pin} configured as INPUT")
        except Exception as e:
            print(f"[MOISTURE] GPIO setup error: {e}")
            self.simulation = True
    
    def _setup_adc(self):
        """Initialize I2C ADC for analog moisture reading"""
        try:
            self._bus = smbus2.SMBus(I2C_BUS)
            # Configure ADS1115 for single-ended input on channel 0
            # Config: single-shot, channel 0, +/-4.096V, 128SPS
            config = [0x01, 0xC3, 0x83]
            self._bus.write_i2c_block_data(self.adc_address, config[0], config[1:])
            print(f"[MOISTURE] ADC configured at 0x{self.adc_address:02X}")
        except Exception as e:
            print(f"[MOISTURE] ADC setup error: {e}")
            self.use_adc = False
    
    def _read_adc(self) -> int:
        """Read raw value from ADC"""
        if not self._bus or self.simulation:
            # Simulation: return random value
            import random
            return random.randint(400, 800)
        
        try:
            # Start conversion
            config = [0x01, 0xC3 | (self.adc_channel << 4), 0x83]
            self._bus.write_i2c_block_data(self.adc_address, config[0], config[1:])
            
            # Wait for conversion
            time.sleep(0.01)
            
            # Read result
            data = self._bus.read_i2c_block_data(self.adc_address, 0x00, 2)
            raw = (data[0] << 8) | data[1]
            
            return raw
        except Exception as e:
            print(f"[MOISTURE] ADC read error: {e}")
            return -1
    
    def _read_digital(self) -> int:
        """Read digital moisture sensor (HIGH = dry, LOW = wet)"""
        if self.simulation:
            import random
            return random.choice([0, 1])
        
        try:
            return GPIO.input(self.gpio_pin)
        except Exception as e:
            print(f"[MOISTURE] GPIO read error: {e}")
            return -1
    
    def _raw_to_percentage(self, raw: int) -> float:
        """Convert raw ADC value to moisture percentage"""
        if raw < 0:
            return -1.0
        
        # Invert and scale (lower raw = wetter)
        percentage = ((DRY_VALUE - raw) / (DRY_VALUE - WET_VALUE)) * 100
        return max(0.0, min(100.0, percentage))
    
    def read(self) -> MoistureReading:
        """
        Read current soil moisture.
        
        Returns:
            MoistureReading with raw value and percentage
        """
        if self.use_adc:
            raw = self._read_adc()
            percentage = self._raw_to_percentage(raw)
        else:
            digital = self._read_digital()
            raw = digital
            # Digital sensor: 0 = wet, 1 = dry
            percentage = 20.0 if digital == 1 else 70.0
        
        reading = MoistureReading(
            raw_value=raw,
            percentage=round(percentage, 1),
            is_dry=percentage < MOISTURE_LOW,
            is_wet=percentage > MOISTURE_HIGH
        )
        
        # Update stats
        self.stats.readings_count += 1
        self.stats.last_reading = reading
        
        if percentage >= 0:
            self.stats.min_moisture = min(self.stats.min_moisture, percentage)
            self.stats.max_moisture = max(self.stats.max_moisture, percentage)
            
            # Update rolling average
            self.stats.history.append(percentage)
            if len(self.stats.history) > 100:
                self.stats.history.pop(0)
            self.stats.average_moisture = sum(self.stats.history) / len(self.stats.history)
        
        return reading
    
    def read_averaged(self, samples: int = 5, delay: float = 0.1) -> MoistureReading:
        """
        Read moisture with averaging for stability.
        
        Args:
            samples: Number of readings to average
            delay: Delay between readings in seconds
        
        Returns:
            Averaged MoistureReading
        """
        readings = []
        for _ in range(samples):
            reading = self.read()
            if reading.percentage >= 0:
                readings.append(reading.percentage)
            time.sleep(delay)
        
        if not readings:
            return MoistureReading(raw_value=-1, percentage=-1, is_dry=False, is_wet=False)
        
        avg_percentage = sum(readings) / len(readings)
        
        return MoistureReading(
            raw_value=int(avg_percentage * 10),  # Placeholder raw
            percentage=round(avg_percentage, 1),
            is_dry=avg_percentage < MOISTURE_LOW,
            is_wet=avg_percentage > MOISTURE_HIGH
        )
    
    def get_status(self) -> Dict:
        """Get moisture sensor status"""
        reading = self.read()
        
        # Determine status string
        if reading.percentage < 0:
            status = "error"
        elif reading.is_dry:
            status = "dry"
        elif reading.is_wet:
            status = "wet"
        else:
            status = "optimal"
        
        return {
            "moisture_percent": reading.percentage,
            "raw_value": reading.raw_value,
            "status": status,
            "is_dry": reading.is_dry,
            "is_wet": reading.is_wet,
            "needs_water": reading.is_dry,
            "thresholds": {
                "low": MOISTURE_LOW,
                "high": MOISTURE_HIGH,
                "optimal": MOISTURE_OPTIMAL
            },
            "timestamp": reading.timestamp.isoformat()
        }
    
    def get_stats(self) -> Dict:
        """Get sensor statistics"""
        return {
            "readings_count": self.stats.readings_count,
            "average_moisture": round(self.stats.average_moisture, 1),
            "min_moisture": round(self.stats.min_moisture, 1),
            "max_moisture": round(self.stats.max_moisture, 1),
            "history_length": len(self.stats.history),
            "simulation_mode": self.simulation,
            "using_adc": self.use_adc
        }
    
    def calibrate_dry(self) -> Dict:
        """Calibrate dry point (call when soil is completely dry)"""
        global DRY_VALUE
        if self.use_adc:
            raw = self._read_adc()
            DRY_VALUE = raw
            return {"success": True, "dry_value": raw}
        return {"success": False, "message": "ADC not enabled"}
    
    def calibrate_wet(self) -> Dict:
        """Calibrate wet point (call when soil is completely wet)"""
        global WET_VALUE
        if self.use_adc:
            raw = self._read_adc()
            WET_VALUE = raw
            return {"success": True, "wet_value": raw}
        return {"success": False, "message": "ADC not enabled"}
    
    def cleanup(self):
        """Cleanup resources"""
        if self._bus:
            self._bus.close()
        if not self.simulation:
            try:
                GPIO.cleanup(self.gpio_pin)
            except:
                pass


# Singleton instance
_moisture_instance: Optional[SoilMoistureSensor] = None

def get_moisture_sensor() -> SoilMoistureSensor:
    """Get or create moisture sensor singleton"""
    global _moisture_instance
    if _moisture_instance is None:
        _moisture_instance = SoilMoistureSensor()
    return _moisture_instance

def read_moisture() -> Dict:
    """Read current moisture level"""
    return get_moisture_sensor().get_status()


# Standalone testing
if __name__ == "__main__":
    print("SmartGrow - Soil Moisture Sensor Test")
    print("=" * 40)
    
    sensor = SoilMoistureSensor(gpio_pin=27, use_adc=False, simulation=True)
    
    print("\nTaking 5 readings...")
    for i in range(5):
        reading = sensor.read()
        print(f"  [{i+1}] Moisture: {reading.percentage}% (dry={reading.is_dry})")
        time.sleep(0.5)
    
    print(f"\nStats: {sensor.get_stats()}")
    print(f"Status: {sensor.get_status()}")
