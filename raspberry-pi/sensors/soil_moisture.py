"""
SmartGrow - Soil Moisture Sensor Module
Capacitive soil moisture sensor via ADS1115 ADC (I2C)
Infomatrix Ukraine 2026
"""

import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from typing import Tuple, Optional
import numpy as np


class SoilMoistureSensor:
    """
    Capacitive Soil Moisture Sensor connected via ADS1115 ADC.
    
    The ADS1115 is a 16-bit ADC with I2C interface.
    Capacitive sensors output analog voltage proportional to moisture.
    """
    
    def __init__(
        self,
        channel: int = 0,
        i2c_address: int = 0x48,
        dry_value: int = 26000,
        wet_value: int = 12000
    ):
        """
        Initialize the soil moisture sensor.
        
        Args:
            channel: ADC channel (0-3 for ADS1115)
            i2c_address: I2C address of ADS1115
            dry_value: ADC reading when soil is completely dry
            wet_value: ADC reading when soil is saturated
        """
        self.channel = channel
        self.dry_value = dry_value
        self.wet_value = wet_value
        self.i2c_address = i2c_address
        
        # Initialize I2C and ADC
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.ads = ADS.ADS1115(self.i2c, address=i2c_address)
        
        # Create analog input channel
        self._channels = {
            0: ADS.P0,
            1: ADS.P1,
            2: ADS.P2,
            3: ADS.P3
        }
        self.chan = AnalogIn(self.ads, self._channels[channel])
        
        # Calibration data
        self._calibration_samples = []
        self._last_reading = None
        self._reading_history = []
        
    def read_raw(self) -> int:
        """Read raw ADC value (16-bit)."""
        return self.chan.value
    
    def read_voltage(self) -> float:
        """Read voltage from ADC."""
        return self.chan.voltage
    
    def read_percentage(self) -> float:
        """
        Convert raw ADC value to moisture percentage.
        
        Returns:
            Moisture percentage (0-100%)
        """
        raw = self.read_raw()
        
        # Linear interpolation between dry and wet values
        # Note: capacitive sensors have LOWER values when WET
        percentage = ((self.dry_value - raw) / 
                      (self.dry_value - self.wet_value)) * 100
        
        # Clamp to 0-100 range
        percentage = max(0, min(100, percentage))
        
        self._last_reading = percentage
        self._reading_history.append({
            'timestamp': time.time(),
            'percentage': percentage,
            'raw': raw
        })
        
        # Keep only last 1000 readings in memory
        if len(self._reading_history) > 1000:
            self._reading_history = self._reading_history[-1000:]
        
        return round(percentage, 1)
    
    def read_averaged(self, samples: int = 10, delay_ms: int = 50) -> float:
        """
        Read averaged moisture percentage for more stable readings.
        
        Args:
            samples: Number of samples to average
            delay_ms: Delay between samples in milliseconds
        
        Returns:
            Averaged moisture percentage
        """
        readings = []
        for _ in range(samples):
            readings.append(self.read_percentage())
            time.sleep(delay_ms / 1000)
        
        # Remove outliers using IQR method
        arr = np.array(readings)
        q1 = np.percentile(arr, 25)
        q3 = np.percentile(arr, 75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        filtered = arr[(arr >= lower) & (arr <= upper)]
        
        return round(np.mean(filtered), 1) if len(filtered) > 0 else round(np.mean(arr), 1)
    
    def get_status(self) -> str:
        """
        Get human-readable moisture status.
        
        Returns:
            Status string: 'critical', 'low', 'optimal', 'high'
        """
        moisture = self._last_reading or self.read_percentage()
        
        if moisture < 25:
            return 'critical'
        elif moisture < 35:
            return 'low'
        elif moisture <= 65:
            return 'optimal'
        else:
            return 'high'
    
    def calibrate_dry(self, samples: int = 50) -> int:
        """
        Calibrate dry soil value.
        Place sensor in dry soil/air and call this method.
        
        Returns:
            New dry calibration value
        """
        print("Calibrating DRY value... Keep sensor in dry soil/air")
        readings = []
        for i in range(samples):
            readings.append(self.read_raw())
            time.sleep(0.1)
            print(f"Sample {i+1}/{samples}: {readings[-1]}")
        
        self.dry_value = int(np.mean(readings))
        print(f"New DRY value: {self.dry_value}")
        return self.dry_value
    
    def calibrate_wet(self, samples: int = 50) -> int:
        """
        Calibrate wet soil value.
        Place sensor in saturated soil/water and call this method.
        
        Returns:
            New wet calibration value
        """
        print("Calibrating WET value... Place sensor in wet soil/water")
        readings = []
        for i in range(samples):
            readings.append(self.read_raw())
            time.sleep(0.1)
            print(f"Sample {i+1}/{samples}: {readings[-1]}")
        
        self.wet_value = int(np.mean(readings))
        print(f"New WET value: {self.wet_value}")
        return self.wet_value
    
    def get_trend(self, window_minutes: int = 30) -> str:
        """
        Analyze moisture trend over recent readings.
        
        Args:
            window_minutes: Time window for trend analysis
        
        Returns:
            'rising', 'falling', 'stable'
        """
        if len(self._reading_history) < 10:
            return 'stable'
        
        cutoff = time.time() - (window_minutes * 60)
        recent = [r for r in self._reading_history if r['timestamp'] > cutoff]
        
        if len(recent) < 5:
            return 'stable'
        
        # Calculate linear regression slope
        x = np.array([r['timestamp'] for r in recent])
        y = np.array([r['percentage'] for r in recent])
        
        # Normalize x to prevent numerical issues
        x_norm = x - x.min()
        
        slope = np.polyfit(x_norm, y, 1)[0]
        
        # Convert slope to percentage per hour
        slope_per_hour = slope * 3600
        
        if slope_per_hour > 2:
            return 'rising'
        elif slope_per_hour < -2:
            return 'falling'
        else:
            return 'stable'
    
    def get_full_reading(self) -> dict:
        """
        Get complete sensor reading with all metadata.
        
        Returns:
            Dictionary with all sensor data
        """
        percentage = self.read_averaged()
        
        return {
            'percentage': percentage,
            'raw': self.read_raw(),
            'voltage': round(self.read_voltage(), 3),
            'status': self.get_status(),
            'trend': self.get_trend(),
            'timestamp': time.time(),
            'unit': '%'
        }


# Standalone testing
if __name__ == "__main__":
    print("SmartGrow - Soil Moisture Sensor Test")
    print("=" * 40)
    
    try:
        sensor = SoilMoistureSensor(
            channel=0,
            dry_value=26000,
            wet_value=12000
        )
        
        print("Sensor initialized successfully!")
        print("\nReading sensor data (Ctrl+C to stop)...\n")
        
        while True:
            reading = sensor.get_full_reading()
            print(f"Moisture: {reading['percentage']}% | "
                  f"Status: {reading['status']} | "
                  f"Trend: {reading['trend']} | "
                  f"Raw: {reading['raw']}")
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\nTest stopped.")
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure ADS1115 is connected properly via I2C")
