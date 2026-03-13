"""
SmartGrow - Temperature & Humidity Sensor Module
DHT22 / AM2302 Digital Sensor
Infomatrix Ukraine 2026
"""

import time
import board
import adafruit_dht
from typing import Tuple, Optional, Dict
import numpy as np


class TemperatureHumiditySensor:
    """
    DHT22/AM2302 Temperature and Humidity Sensor.
    
    Provides:
    - Temperature: -40 to 80°C (±0.5°C accuracy)
    - Humidity: 0-100% RH (±2-5% accuracy)
    """
    
    def __init__(self, pin: int = 4):
        """
        Initialize the DHT22 sensor.
        
        Args:
            pin: GPIO pin number (BCM numbering)
        """
        self.pin = pin
        
        # Map pin number to board pin
        self._pin_map = {
            4: board.D4,
            17: board.D17,
            27: board.D27,
            22: board.D22,
            5: board.D5,
            6: board.D6,
            13: board.D13,
            19: board.D19,
            26: board.D26,
        }
        
        # Initialize DHT22 sensor
        self.dht = adafruit_dht.DHT22(self._pin_map.get(pin, board.D4))
        
        # Reading history for analytics
        self._temp_history = []
        self._humidity_history = []
        self._last_temp = None
        self._last_humidity = None
        
        # Error tracking
        self._consecutive_errors = 0
        self._max_retries = 5
        
    def read_temperature(self) -> Optional[float]:
        """
        Read temperature in Celsius.
        
        Returns:
            Temperature in °C or None if reading failed
        """
        for _ in range(self._max_retries):
            try:
                temp = self.dht.temperature
                if temp is not None:
                    self._last_temp = temp
                    self._temp_history.append({
                        'timestamp': time.time(),
                        'value': temp
                    })
                    # Keep history manageable
                    if len(self._temp_history) > 1000:
                        self._temp_history = self._temp_history[-1000:]
                    self._consecutive_errors = 0
                    return round(temp, 1)
            except RuntimeError as e:
                self._consecutive_errors += 1
                time.sleep(0.5)
        
        return self._last_temp  # Return last known value
    
    def read_humidity(self) -> Optional[float]:
        """
        Read relative humidity percentage.
        
        Returns:
            Humidity in % or None if reading failed
        """
        for _ in range(self._max_retries):
            try:
                humidity = self.dht.humidity
                if humidity is not None:
                    self._last_humidity = humidity
                    self._humidity_history.append({
                        'timestamp': time.time(),
                        'value': humidity
                    })
                    if len(self._humidity_history) > 1000:
                        self._humidity_history = self._humidity_history[-1000:]
                    self._consecutive_errors = 0
                    return round(humidity, 1)
            except RuntimeError as e:
                self._consecutive_errors += 1
                time.sleep(0.5)
        
        return self._last_humidity
    
    def read_both(self) -> Tuple[Optional[float], Optional[float]]:
        """
        Read both temperature and humidity.
        
        Returns:
            Tuple of (temperature, humidity)
        """
        temp = None
        humidity = None
        
        for _ in range(self._max_retries):
            try:
                temp = self.dht.temperature
                humidity = self.dht.humidity
                if temp is not None and humidity is not None:
                    self._last_temp = temp
                    self._last_humidity = humidity
                    
                    timestamp = time.time()
                    self._temp_history.append({'timestamp': timestamp, 'value': temp})
                    self._humidity_history.append({'timestamp': timestamp, 'value': humidity})
                    
                    self._consecutive_errors = 0
                    return round(temp, 1), round(humidity, 1)
            except RuntimeError:
                self._consecutive_errors += 1
                time.sleep(0.5)
        
        return (
            round(self._last_temp, 1) if self._last_temp else None,
            round(self._last_humidity, 1) if self._last_humidity else None
        )
    
    def get_temperature_status(self, temp: Optional[float] = None) -> str:
        """
        Get temperature status based on plant requirements.
        
        Args:
            temp: Temperature value or None to use last reading
        
        Returns:
            Status: 'cold', 'optimal', 'warm', 'hot'
        """
        if temp is None:
            temp = self._last_temp
        if temp is None:
            return 'unknown'
        
        if temp < 15:
            return 'cold'
        elif temp < 20:
            return 'cool'
        elif temp <= 28:
            return 'optimal'
        elif temp <= 32:
            return 'warm'
        else:
            return 'hot'
    
    def get_humidity_status(self, humidity: Optional[float] = None) -> str:
        """
        Get humidity status based on plant requirements.
        
        Args:
            humidity: Humidity value or None to use last reading
        
        Returns:
            Status: 'dry', 'optimal', 'humid'
        """
        if humidity is None:
            humidity = self._last_humidity
        if humidity is None:
            return 'unknown'
        
        if humidity < 40:
            return 'dry'
        elif humidity <= 70:
            return 'optimal'
        else:
            return 'humid'
    
    def get_dew_point(self, temp: Optional[float] = None, 
                      humidity: Optional[float] = None) -> Optional[float]:
        """
        Calculate dew point temperature.
        
        Uses Magnus formula for accurate approximation.
        
        Returns:
            Dew point temperature in °C
        """
        if temp is None:
            temp = self._last_temp
        if humidity is None:
            humidity = self._last_humidity
        
        if temp is None or humidity is None or humidity <= 0:
            return None
        
        # Magnus formula constants
        a = 17.27
        b = 237.7
        
        alpha = ((a * temp) / (b + temp)) + np.log(humidity / 100.0)
        dew_point = (b * alpha) / (a - alpha)
        
        return round(dew_point, 1)
    
    def get_heat_index(self, temp: Optional[float] = None,
                       humidity: Optional[float] = None) -> Optional[float]:
        """
        Calculate heat index (feels like temperature).
        
        Uses simplified Rothfusz regression equation.
        
        Returns:
            Heat index in °C
        """
        if temp is None:
            temp = self._last_temp
        if humidity is None:
            humidity = self._last_humidity
        
        if temp is None or humidity is None:
            return None
        
        # Convert to Fahrenheit for calculation
        T = temp * 9/5 + 32
        RH = humidity
        
        # Simple approximation
        HI = 0.5 * (T + 61.0 + ((T - 68.0) * 1.2) + (RH * 0.094))
        
        if HI >= 80:
            # Full Rothfusz regression
            HI = (-42.379 + 2.04901523 * T + 10.14333127 * RH
                  - 0.22475541 * T * RH - 0.00683783 * T**2
                  - 0.05481717 * RH**2 + 0.00122874 * T**2 * RH
                  + 0.00085282 * T * RH**2 - 0.00000199 * T**2 * RH**2)
        
        # Convert back to Celsius
        heat_index = (HI - 32) * 5/9
        
        return round(heat_index, 1)
    
    def get_trend(self, sensor: str = 'temperature', 
                  window_minutes: int = 30) -> str:
        """
        Analyze temperature or humidity trend.
        
        Args:
            sensor: 'temperature' or 'humidity'
            window_minutes: Time window for analysis
        
        Returns:
            'rising', 'falling', 'stable'
        """
        history = self._temp_history if sensor == 'temperature' else self._humidity_history
        
        if len(history) < 10:
            return 'stable'
        
        cutoff = time.time() - (window_minutes * 60)
        recent = [r for r in history if r['timestamp'] > cutoff]
        
        if len(recent) < 5:
            return 'stable'
        
        x = np.array([r['timestamp'] for r in recent])
        y = np.array([r['value'] for r in recent])
        x_norm = x - x.min()
        
        slope = np.polyfit(x_norm, y, 1)[0]
        slope_per_hour = slope * 3600
        
        if sensor == 'temperature':
            threshold = 0.5  # 0.5°C per hour
        else:
            threshold = 2  # 2% per hour
        
        if slope_per_hour > threshold:
            return 'rising'
        elif slope_per_hour < -threshold:
            return 'falling'
        else:
            return 'stable'
    
    def get_full_reading(self) -> Dict:
        """
        Get complete sensor reading with all computed values.
        
        Returns:
            Dictionary with all sensor data and analytics
        """
        temp, humidity = self.read_both()
        
        return {
            'temperature': {
                'value': temp,
                'unit': '°C',
                'status': self.get_temperature_status(temp),
                'trend': self.get_trend('temperature'),
            },
            'humidity': {
                'value': humidity,
                'unit': '%',
                'status': self.get_humidity_status(humidity),
                'trend': self.get_trend('humidity'),
            },
            'dew_point': self.get_dew_point(temp, humidity),
            'heat_index': self.get_heat_index(temp, humidity),
            'timestamp': time.time(),
            'sensor_health': 'good' if self._consecutive_errors < 3 else 'degraded'
        }
    
    def cleanup(self):
        """Release sensor resources."""
        self.dht.exit()


# Standalone testing
if __name__ == "__main__":
    print("SmartGrow - DHT22 Temperature & Humidity Sensor Test")
    print("=" * 50)
    
    try:
        sensor = TemperatureHumiditySensor(pin=4)
        
        print("Sensor initialized successfully!")
        print("\nReading sensor data (Ctrl+C to stop)...\n")
        
        while True:
            reading = sensor.get_full_reading()
            
            temp_data = reading['temperature']
            humidity_data = reading['humidity']
            
            print(f"Temperature: {temp_data['value']}°C | "
                  f"Status: {temp_data['status']} | "
                  f"Trend: {temp_data['trend']}")
            print(f"Humidity: {humidity_data['value']}% | "
                  f"Status: {humidity_data['status']} | "
                  f"Trend: {humidity_data['trend']}")
            print(f"Dew Point: {reading['dew_point']}°C | "
                  f"Heat Index: {reading['heat_index']}°C")
            print("-" * 50)
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\nTest stopped.")
        sensor.cleanup()
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure DHT22 is connected to GPIO4")
