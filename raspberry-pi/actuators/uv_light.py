"""
SmartGrow - UV Grow Light Controller Module
Controls UV LED strip via relay with 5V to 12V converter
Infomatrix Ukraine 2026
"""

import time
import RPi.GPIO as GPIO
from typing import Dict, Optional
from datetime import datetime, timedelta


class UVLightController:
    """
    UV/Grow Light controller using GPIO relay.
    
    The UV LED strip runs on 12V, connected via:
    - Relay module (controlled by 3.3V GPIO)
    - 5V to 12V step-up converter
    """
    
    def __init__(
        self,
        relay_pin: int = 27,
        active_low: bool = True,
        schedule_start_hour: int = 7,
        schedule_end_hour: int = 22,
        max_continuous_hours: float = 16
    ):
        """
        Initialize the UV light controller.
        
        Args:
            relay_pin: GPIO pin connected to relay
            active_low: True if relay activates on LOW signal
            schedule_start_hour: Hour to turn on light (0-23)
            schedule_end_hour: Hour to turn off light (0-23)
            max_continuous_hours: Safety limit for continuous operation
        """
        self.relay_pin = relay_pin
        self.active_low = active_low
        self.schedule_start = schedule_start_hour
        self.schedule_end = schedule_end_hour
        self.max_continuous_hours = max_continuous_hours
        
        # Initialize GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.relay_pin, GPIO.OUT)
        
        # Start with light OFF
        self._turn_off_relay()
        
        # State tracking
        self._is_on = False
        self._last_on_time = None
        self._last_off_time = None
        self._total_runtime_today = 0
        self._daily_sessions = []
        
        # Auto mode
        self._auto_mode = True
        
    def _turn_on_relay(self):
        """Activate relay (light ON)."""
        GPIO.output(self.relay_pin, GPIO.LOW if self.active_low else GPIO.HIGH)
        
    def _turn_off_relay(self):
        """Deactivate relay (light OFF)."""
        GPIO.output(self.relay_pin, GPIO.HIGH if self.active_low else GPIO.LOW)
    
    def _is_within_schedule(self) -> bool:
        """
        Check if current time is within light schedule.
        
        Returns:
            True if light should be on according to schedule
        """
        now = datetime.now()
        current_hour = now.hour
        
        if self.schedule_start < self.schedule_end:
            # Normal schedule (e.g., 7-22)
            return self.schedule_start <= current_hour < self.schedule_end
        else:
            # Overnight schedule (e.g., 22-7)
            return current_hour >= self.schedule_start or current_hour < self.schedule_end
    
    def turn_on(self, manual: bool = False) -> Dict:
        """
        Turn on the UV grow light.
        
        Args:
            manual: If True, bypasses auto mode check
        
        Returns:
            Result dictionary
        """
        if self._is_on:
            return {
                'success': True,
                'message': 'Light is already on',
                'action': 'turn_on',
                'is_on': True,
                'timestamp': time.time()
            }
        
        # Safety check for continuous runtime
        if self._last_on_time:
            runtime = time.time() - self._last_on_time
            if runtime > self.max_continuous_hours * 3600:
                return {
                    'success': False,
                    'message': 'Max continuous runtime exceeded',
                    'action': 'turn_on',
                    'timestamp': time.time()
                }
        
        self._turn_on_relay()
        self._is_on = True
        self._last_on_time = time.time()
        
        if manual:
            self._auto_mode = False
        
        return {
            'success': True,
            'message': 'Light turned on',
            'action': 'turn_on',
            'is_on': True,
            'mode': 'manual' if manual else 'auto',
            'timestamp': time.time()
        }
    
    def turn_off(self, manual: bool = False) -> Dict:
        """
        Turn off the UV grow light.
        
        Args:
            manual: If True, marks manual operation
        
        Returns:
            Result dictionary
        """
        was_on = self._is_on
        
        self._turn_off_relay()
        self._is_on = False
        self._last_off_time = time.time()
        
        session_duration = 0
        if was_on and self._last_on_time:
            session_duration = time.time() - self._last_on_time
            self._total_runtime_today += session_duration
            self._daily_sessions.append({
                'start': self._last_on_time,
                'end': time.time(),
                'duration': session_duration
            })
        
        if manual:
            self._auto_mode = False
        
        return {
            'success': True,
            'message': 'Light turned off',
            'action': 'turn_off',
            'is_on': False,
            'session_duration': round(session_duration, 1),
            'mode': 'manual' if manual else 'auto',
            'timestamp': time.time()
        }
    
    def toggle(self, manual: bool = True) -> Dict:
        """
        Toggle light state.
        
        Returns:
            Result dictionary
        """
        if self._is_on:
            return self.turn_off(manual=manual)
        else:
            return self.turn_on(manual=manual)
    
    def set_auto_mode(self, enabled: bool) -> Dict:
        """
        Enable or disable automatic schedule mode.
        
        Args:
            enabled: True to enable auto mode
        
        Returns:
            Result dictionary
        """
        self._auto_mode = enabled
        
        if enabled:
            # Apply schedule immediately
            self.check_schedule()
        
        return {
            'success': True,
            'message': f'Auto mode {"enabled" if enabled else "disabled"}',
            'auto_mode': enabled,
            'timestamp': time.time()
        }
    
    def check_schedule(self) -> Dict:
        """
        Check and apply schedule if in auto mode.
        Call this periodically (e.g., every minute).
        
        Returns:
            Result dictionary with any changes made
        """
        if not self._auto_mode:
            return {
                'success': True,
                'message': 'Auto mode disabled',
                'action': None,
                'timestamp': time.time()
            }
        
        should_be_on = self._is_within_schedule()
        
        if should_be_on and not self._is_on:
            result = self.turn_on(manual=False)
            result['action'] = 'schedule_on'
            return result
        elif not should_be_on and self._is_on:
            result = self.turn_off(manual=False)
            result['action'] = 'schedule_off'
            return result
        
        return {
            'success': True,
            'message': 'No schedule change needed',
            'action': None,
            'is_on': self._is_on,
            'within_schedule': should_be_on,
            'timestamp': time.time()
        }
    
    def set_schedule(self, start_hour: int, end_hour: int) -> Dict:
        """
        Update the light schedule.
        
        Args:
            start_hour: Hour to turn on (0-23)
            end_hour: Hour to turn off (0-23)
        
        Returns:
            Result dictionary
        """
        if not (0 <= start_hour <= 23 and 0 <= end_hour <= 23):
            return {
                'success': False,
                'message': 'Hours must be 0-23',
                'timestamp': time.time()
            }
        
        self.schedule_start = start_hour
        self.schedule_end = end_hour
        
        # Re-check schedule if in auto mode
        if self._auto_mode:
            self.check_schedule()
        
        return {
            'success': True,
            'message': f'Schedule updated: {start_hour}:00 - {end_hour}:00',
            'schedule_start': start_hour,
            'schedule_end': end_hour,
            'timestamp': time.time()
        }
    
    def get_schedule_info(self) -> Dict:
        """
        Get detailed schedule information.
        
        Returns:
            Schedule info dictionary
        """
        now = datetime.now()
        within_schedule = self._is_within_schedule()
        
        # Calculate time until next transition
        if within_schedule:
            # Calculate time until schedule end
            end_time = now.replace(hour=self.schedule_end, minute=0, second=0)
            if end_time <= now:
                end_time += timedelta(days=1)
            time_until_change = (end_time - now).total_seconds()
            next_event = 'off'
        else:
            # Calculate time until schedule start
            start_time = now.replace(hour=self.schedule_start, minute=0, second=0)
            if start_time <= now:
                start_time += timedelta(days=1)
            time_until_change = (start_time - now).total_seconds()
            next_event = 'on'
        
        daily_light_hours = self.schedule_end - self.schedule_start
        if daily_light_hours < 0:
            daily_light_hours += 24
        
        return {
            'schedule_start': f'{self.schedule_start:02d}:00',
            'schedule_end': f'{self.schedule_end:02d}:00',
            'daily_light_hours': daily_light_hours,
            'within_schedule': within_schedule,
            'next_event': next_event,
            'time_until_change_seconds': round(time_until_change),
            'time_until_change_formatted': str(timedelta(seconds=int(time_until_change))),
            'auto_mode': self._auto_mode
        }
    
    def get_status(self) -> Dict:
        """
        Get current light status.
        
        Returns:
            Status dictionary
        """
        current_session_duration = 0
        if self._is_on and self._last_on_time:
            current_session_duration = time.time() - self._last_on_time
        
        return {
            'is_on': self._is_on,
            'auto_mode': self._auto_mode,
            'last_on_time': self._last_on_time,
            'last_off_time': self._last_off_time,
            'current_session_duration': round(current_session_duration, 0),
            'total_runtime_today': round(self._total_runtime_today, 0),
            'sessions_today': len(self._daily_sessions),
            'schedule': self.get_schedule_info(),
            'timestamp': time.time()
        }
    
    def get_daily_stats(self) -> Dict:
        """
        Get daily usage statistics.
        
        Returns:
            Daily stats dictionary
        """
        total_hours = self._total_runtime_today / 3600
        
        # Include current session if light is on
        if self._is_on and self._last_on_time:
            total_hours += (time.time() - self._last_on_time) / 3600
        
        return {
            'total_hours': round(total_hours, 2),
            'sessions': len(self._daily_sessions),
            'average_session_minutes': round(
                (self._total_runtime_today / 60 / len(self._daily_sessions))
                if self._daily_sessions else 0, 1
            ),
            'timestamp': time.time()
        }
    
    def reset_daily_stats(self):
        """Reset daily statistics (call at midnight)."""
        self._total_runtime_today = 0
        self._daily_sessions = []
    
    def cleanup(self):
        """Cleanup GPIO resources."""
        self._turn_off_relay()
        GPIO.cleanup(self.relay_pin)


# Standalone testing
if __name__ == "__main__":
    print("SmartGrow - UV Grow Light Controller Test")
    print("=" * 45)
    
    try:
        light = UVLightController(
            relay_pin=27,
            active_low=True,
            schedule_start_hour=7,
            schedule_end_hour=22
        )
        
        print("Light controller initialized")
        print(f"\nStatus: {light.get_status()}")
        print(f"\nSchedule: {light.get_schedule_info()}")
        
        input("\nPress Enter to toggle light...")
        
        result = light.toggle()
        print(f"\nToggle result: {result}")
        print(f"New status: {light.get_status()}")
        
        time.sleep(3)
        
        result = light.toggle()
        print(f"\nToggle result: {result}")
        
    except KeyboardInterrupt:
        print("\nTest cancelled.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        light.cleanup()
        print("Cleanup complete.")
