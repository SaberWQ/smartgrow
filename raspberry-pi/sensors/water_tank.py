"""
SmartGrow - Water Tank Level Sensor Module
Capacitive water level sensor via ADS1115 ADC
Infomatrix Ukraine 2026
"""

import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from typing import Optional, Dict
import numpy as np


class WaterTankSensor:
    """
    Water tank level sensor connected via ADS1115 ADC.
    
    Uses capacitive sensing to measure water level.
    """
    
    def __init__(
        self,
        channel: int = 1,
        i2c_address: int = 0x48,
        empty_value: int = 25000,
        full_value: int = 10000,
        tank_capacity_ml: int = 2000
    ):
        """
        Initialize the water tank sensor.
        
        Args:
            channel: ADC channel (0-3 for ADS1115)
            i2c_address: I2C address of ADS1115
            empty_value: ADC reading when tank is empty
            full_value: ADC reading when tank is full
            tank_capacity_ml: Tank capacity in milliliters
        """
        self.channel = channel
        self.empty_value = empty_value
        self.full_value = full_value
        self.tank_capacity_ml = tank_capacity_ml
        
        # Initialize I2C and ADC
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.ads = ADS.ADS1115(self.i2c, address=i2c_address)
        
        # Channel mapping
        self._channels = {
            0: ADS.P0,
            1: ADS.P1,
            2: ADS.P2,
            3: ADS.P3
        }
        self.chan = AnalogIn(self.ads, self._channels[channel])
        
        # History tracking
        self._reading_history = []
        self._last_reading = None
        self._refill_events = []
        
    def read_raw(self) -> int:
        """Read raw ADC value."""
        return self.chan.value
    
    def read_percentage(self) -> float:
        """
        Read water level as percentage.
        
        Returns:
            Water level percentage (0-100%)
        """
        raw = self.read_raw()
        
        percentage = ((self.empty_value - raw) / 
                      (self.empty_value - self.full_value)) * 100
        
        percentage = max(0, min(100, percentage))
        
        self._last_reading = percentage
        self._reading_history.append({
            'timestamp': time.time(),
            'percentage': percentage,
            'raw': raw
        })
        
        if len(self._reading_history) > 1000:
            self._reading_history = self._reading_history[-1000:]
        
        return round(percentage, 1)
    
    def read_volume_ml(self) -> float:
        """
        Read estimated water volume in milliliters.
        
        Returns:
            Water volume in ml
        """
        percentage = self.read_percentage()
        return round((percentage / 100) * self.tank_capacity_ml, 0)
    
    def read_averaged(self, samples: int = 5, delay_ms: int = 100) -> float:
        """
        Read averaged water level for stable readings.
        
        Args:
            samples: Number of samples
            delay_ms: Delay between samples
        
        Returns:
            Averaged water level percentage
        """
        readings = []
        for _ in range(samples):
            readings.append(self.read_percentage())
            time.sleep(delay_ms / 1000)
        
        return round(np.median(readings), 1)
    
    def get_status(self) -> str:
        """
        Get tank status.
        
        Returns:
            Status: 'empty', 'critical', 'low', 'medium', 'high', 'full'
        """
        level = self._last_reading or self.read_percentage()
        
        if level < 5:
            return 'empty'
        elif level < 15:
            return 'critical'
        elif level < 30:
            return 'low'
        elif level < 60:
            return 'medium'
        elif level < 90:
            return 'high'
        else:
            return 'full'
    
    def estimate_waterings_remaining(self, ml_per_watering: int = 100) -> int:
        """
        Estimate how many watering cycles remain.
        
        Args:
            ml_per_watering: Average water used per watering
        
        Returns:
            Estimated number of waterings remaining
        """
        volume = self.read_volume_ml()
        return int(volume / ml_per_watering)
    
    def detect_refill(self) -> bool:
        """
        Detect if tank was refilled.
        
        Returns:
            True if refill was detected
        """
        if len(self._reading_history) < 2:
            return False
        
        current = self._reading_history[-1]['percentage']
        previous = self._reading_history[-2]['percentage']
        
        # Refill detected if level increased by more than 20%
        if current - previous > 20:
            self._refill_events.append({
                'timestamp': time.time(),
                'from_level': previous,
                'to_level': current
            })
            return True
        
        return False
    
    def get_consumption_rate(self, hours: int = 24) -> float:
        """
        Calculate average water consumption rate.
        
        Args:
            hours: Time window for calculation
        
        Returns:
            Consumption rate in % per hour
        """
        if len(self._reading_history) < 10:
            return 0.0
        
        cutoff = time.time() - (hours * 3600)
        recent = [r for r in self._reading_history if r['timestamp'] > cutoff]
        
        if len(recent) < 5:
            return 0.0
        
        # Filter out refill spikes
        filtered = []
        for i, r in enumerate(recent):
            if i == 0:
                filtered.append(r)
            elif r['percentage'] - recent[i-1]['percentage'] < 15:
                filtered.append(r)
        
        if len(filtered) < 2:
            return 0.0
        
        # Calculate consumption (only decreases)
        total_decrease = 0
        for i in range(1, len(filtered)):
            diff = filtered[i-1]['percentage'] - filtered[i]['percentage']
            if diff > 0:
                total_decrease += diff
        
        time_span_hours = (filtered[-1]['timestamp'] - filtered[0]['timestamp']) / 3600
        
        if time_span_hours > 0:
            return round(total_decrease / time_span_hours, 2)
        
        return 0.0
    
    def estimate_days_until_empty(self) -> Optional[float]:
        """
        Estimate days until tank is empty.
        
        Returns:
            Estimated days or None if cannot calculate
        """
        rate = self.get_consumption_rate()
        
        if rate <= 0:
            return None
        
        current_level = self._last_reading or self.read_percentage()
        hours_remaining = current_level / rate
        
        return round(hours_remaining / 24, 1)
    
    def get_full_reading(self) -> Dict:
        """
        Get complete tank reading with analytics.
        
        Returns:
            Dictionary with all tank data
        """
        percentage = self.read_averaged()
        
        return {
            'percentage': percentage,
            'volume_ml': self.read_volume_ml(),
            'status': self.get_status(),
            'waterings_remaining': self.estimate_waterings_remaining(),
            'consumption_rate': self.get_consumption_rate(),
            'days_until_empty': self.estimate_days_until_empty(),
            'refill_detected': self.detect_refill(),
            'timestamp': time.time(),
            'unit': '%'
        }


# Standalone testing
if __name__ == "__main__":
    print("SmartGrow - Water Tank Sensor Test")
    print("=" * 40)
    
    try:
        sensor = WaterTankSensor(
            channel=1,
            empty_value=25000,
            full_value=10000,
            tank_capacity_ml=2000
        )
        
        print("Sensor initialized successfully!")
        print("\nReading sensor data (Ctrl+C to stop)...\n")
        
        while True:
            reading = sensor.get_full_reading()
            print(f"Level: {reading['percentage']}% | "
                  f"Volume: {reading['volume_ml']}ml | "
                  f"Status: {reading['status']}")
            print(f"Waterings left: {reading['waterings_remaining']} | "
                  f"Days until empty: {reading['days_until_empty']}")
            print("-" * 40)
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\nTest stopped.")
    except Exception as e:
        print(f"Error: {e}")
