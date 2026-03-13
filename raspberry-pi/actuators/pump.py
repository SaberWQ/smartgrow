"""
SmartGrow - Water Pump Controller Module
Controls water pump via relay
Infomatrix Ukraine 2026
"""

import time
import RPi.GPIO as GPIO
from typing import Dict, Optional
from datetime import datetime


class WaterPumpController:
    """
    Water pump controller using GPIO relay.
    
    The pump is connected via relay to handle higher voltage/current.
    Relay activates pump (LOW signal = ON for most relay modules).
    """
    
    def __init__(
        self,
        relay_pin: int = 17,
        active_low: bool = True,
        max_duration_seconds: int = 30,
        cooldown_seconds: int = 300
    ):
        """
        Initialize the water pump controller.
        
        Args:
            relay_pin: GPIO pin connected to relay
            active_low: True if relay activates on LOW signal
            max_duration_seconds: Maximum pump run time (safety)
            cooldown_seconds: Minimum time between activations
        """
        self.relay_pin = relay_pin
        self.active_low = active_low
        self.max_duration = max_duration_seconds
        self.cooldown = cooldown_seconds
        
        # Initialize GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.relay_pin, GPIO.OUT)
        
        # Start with pump OFF
        self._turn_off_relay()
        
        # State tracking
        self._is_running = False
        self._last_activation = None
        self._total_runtime_today = 0
        self._activation_log = []
        self._daily_usage_ml = 0
        
        # Flow rate calibration (ml per second)
        self.flow_rate_ml_per_sec = 20
        
    def _turn_on_relay(self):
        """Activate relay (pump ON)."""
        GPIO.output(self.relay_pin, GPIO.LOW if self.active_low else GPIO.HIGH)
        
    def _turn_off_relay(self):
        """Deactivate relay (pump OFF)."""
        GPIO.output(self.relay_pin, GPIO.HIGH if self.active_low else GPIO.LOW)
    
    def _can_activate(self) -> tuple[bool, str]:
        """
        Check if pump can be activated.
        
        Returns:
            Tuple of (can_activate, reason_if_not)
        """
        if self._is_running:
            return False, "Pump is already running"
        
        if self._last_activation:
            elapsed = time.time() - self._last_activation
            if elapsed < self.cooldown:
                remaining = int(self.cooldown - elapsed)
                return False, f"Cooldown active ({remaining}s remaining)"
        
        return True, ""
    
    def start(self, duration_seconds: Optional[int] = None) -> Dict:
        """
        Start the water pump for specified duration.
        
        Args:
            duration_seconds: How long to run (uses max_duration if not specified)
        
        Returns:
            Result dictionary with status and details
        """
        can_start, reason = self._can_activate()
        if not can_start:
            return {
                'success': False,
                'message': reason,
                'action': 'start',
                'timestamp': time.time()
            }
        
        duration = min(duration_seconds or self.max_duration, self.max_duration)
        
        self._is_running = True
        self._last_activation = time.time()
        
        start_time = time.time()
        self._turn_on_relay()
        
        # Track activation
        activation_record = {
            'start_time': start_time,
            'requested_duration': duration,
            'actual_duration': 0,
            'water_dispensed_ml': 0
        }
        
        try:
            time.sleep(duration)
        except KeyboardInterrupt:
            pass
        finally:
            self._turn_off_relay()
            end_time = time.time()
            
        actual_duration = end_time - start_time
        water_dispensed = actual_duration * self.flow_rate_ml_per_sec
        
        activation_record['actual_duration'] = round(actual_duration, 1)
        activation_record['water_dispensed_ml'] = round(water_dispensed, 0)
        
        self._activation_log.append(activation_record)
        self._total_runtime_today += actual_duration
        self._daily_usage_ml += water_dispensed
        self._is_running = False
        
        return {
            'success': True,
            'message': f'Pump ran for {actual_duration:.1f}s',
            'action': 'start',
            'duration_seconds': actual_duration,
            'water_dispensed_ml': water_dispensed,
            'timestamp': time.time()
        }
    
    def start_async(self, duration_seconds: Optional[int] = None) -> Dict:
        """
        Start pump without blocking (returns immediately).
        
        Note: You must call stop() to turn off the pump!
        
        Args:
            duration_seconds: Maximum duration (safety timeout)
        
        Returns:
            Result dictionary
        """
        can_start, reason = self._can_activate()
        if not can_start:
            return {
                'success': False,
                'message': reason,
                'action': 'start_async',
                'timestamp': time.time()
            }
        
        self._is_running = True
        self._last_activation = time.time()
        self._turn_on_relay()
        
        return {
            'success': True,
            'message': 'Pump started (async)',
            'action': 'start_async',
            'max_duration': duration_seconds or self.max_duration,
            'timestamp': time.time()
        }
    
    def stop(self) -> Dict:
        """
        Stop the water pump.
        
        Returns:
            Result dictionary
        """
        was_running = self._is_running
        
        self._turn_off_relay()
        self._is_running = False
        
        if was_running and self._last_activation:
            duration = time.time() - self._last_activation
            water = duration * self.flow_rate_ml_per_sec
            
            self._total_runtime_today += duration
            self._daily_usage_ml += water
            
            return {
                'success': True,
                'message': f'Pump stopped after {duration:.1f}s',
                'action': 'stop',
                'duration_seconds': duration,
                'water_dispensed_ml': water,
                'timestamp': time.time()
            }
        
        return {
            'success': True,
            'message': 'Pump was already off',
            'action': 'stop',
            'timestamp': time.time()
        }
    
    def pulse(self, pulses: int = 3, on_ms: int = 500, off_ms: int = 500) -> Dict:
        """
        Run pump in pulsed mode for gentle watering.
        
        Args:
            pulses: Number of on/off cycles
            on_ms: Pump ON time in milliseconds
            off_ms: Pump OFF time in milliseconds
        
        Returns:
            Result dictionary
        """
        can_start, reason = self._can_activate()
        if not can_start:
            return {
                'success': False,
                'message': reason,
                'action': 'pulse',
                'timestamp': time.time()
            }
        
        self._is_running = True
        self._last_activation = time.time()
        
        total_on_time = 0
        
        try:
            for i in range(pulses):
                self._turn_on_relay()
                time.sleep(on_ms / 1000)
                total_on_time += on_ms / 1000
                self._turn_off_relay()
                
                if i < pulses - 1:
                    time.sleep(off_ms / 1000)
        finally:
            self._turn_off_relay()
        
        water_dispensed = total_on_time * self.flow_rate_ml_per_sec
        
        self._total_runtime_today += total_on_time
        self._daily_usage_ml += water_dispensed
        self._is_running = False
        
        return {
            'success': True,
            'message': f'Pulsed {pulses} times',
            'action': 'pulse',
            'pulses': pulses,
            'total_on_time': total_on_time,
            'water_dispensed_ml': water_dispensed,
            'timestamp': time.time()
        }
    
    def get_status(self) -> Dict:
        """
        Get current pump status.
        
        Returns:
            Status dictionary
        """
        cooldown_remaining = 0
        if self._last_activation:
            elapsed = time.time() - self._last_activation
            if elapsed < self.cooldown:
                cooldown_remaining = self.cooldown - elapsed
        
        return {
            'is_running': self._is_running,
            'last_activation': self._last_activation,
            'cooldown_remaining': round(cooldown_remaining, 0),
            'total_runtime_today': round(self._total_runtime_today, 1),
            'daily_usage_ml': round(self._daily_usage_ml, 0),
            'activations_today': len(self._activation_log),
            'timestamp': time.time()
        }
    
    def reset_daily_stats(self):
        """Reset daily statistics (call at midnight)."""
        self._total_runtime_today = 0
        self._daily_usage_ml = 0
        self._activation_log = []
    
    def emergency_stop(self):
        """Emergency stop - immediately turn off pump."""
        self._turn_off_relay()
        self._is_running = False
    
    def cleanup(self):
        """Cleanup GPIO resources."""
        self._turn_off_relay()
        GPIO.cleanup(self.relay_pin)


# Standalone testing
if __name__ == "__main__":
    print("SmartGrow - Water Pump Controller Test")
    print("=" * 40)
    print("WARNING: This will activate the real pump!")
    print()
    
    try:
        pump = WaterPumpController(
            relay_pin=17,
            active_low=True,
            max_duration_seconds=10,
            cooldown_seconds=30
        )
        
        print("Pump controller initialized")
        print(f"Status: {pump.get_status()}")
        
        input("\nPress Enter to test pump for 3 seconds...")
        
        result = pump.start(duration_seconds=3)
        print(f"\nResult: {result}")
        
        print(f"\nFinal status: {pump.get_status()}")
        
    except KeyboardInterrupt:
        print("\nTest cancelled.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        pump.cleanup()
        print("Cleanup complete.")
