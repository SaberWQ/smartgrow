#!/usr/bin/env python3
"""
SmartGrow - Main Controller
Central controller for smart greenhouse system
Infomatrix Ukraine 2026

Hardware:
- Raspberry Pi 4 Model B (2GB RAM, 128GB Storage)
- ADS1115 ADC (I2C) - Soil moisture & water tank sensors
- DHT22 - Temperature & humidity sensor
- Relay module - Pump & UV light control
- SSD1306 OLED displays (I2C)
- ST7789 IPS display (SPI)
- Water pump (3-6V via relay)
- UV LED strip (12V via 5V-12V converter + relay)
"""

import os
import sys
import time
import signal
import threading
import schedule
import yaml
from datetime import datetime, timedelta
from typing import Dict, Optional

# Import SmartGrow modules
from sensors import SoilMoistureSensor, TemperatureHumiditySensor, WaterTankSensor
from actuators import WaterPumpController, UVLightController
from displays import OLEDDisplay, IPSDisplay
from analytics import DataAnalyzer
from api import SmartGrowAPI
from pid import PIDController, PIDConfig
from ai import PlantAnalyzer, AnalysisBackend
from database import get_database


class GreenhouseController:
    """
    Main controller for SmartGrow greenhouse system.
    
    Coordinates all sensors, actuators, displays, and the web API.
    Implements automation logic and game mechanics.
    """
    
    def __init__(self, config_path: str = './config.yaml'):
        """
        Initialize the greenhouse controller.
        
        Args:
            config_path: Path to configuration file
        """
        print("=" * 50)
        print("   SMARTGROW - AI Greenhouse Controller")
        print("   Infomatrix Ukraine 2026")
        print("=" * 50)
        print()
        
        # Load configuration
        print("[INIT] Loading configuration...")
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize components
        self._init_sensors()
        self._init_actuators()
        self._init_displays()
        self._init_analytics()
        self._init_pid()
        self._init_ai()
        self._init_database()
        
        # State
        self._running = False
        self._auto_watering = True
        self._last_sensor_reading = {}
        self._events_log = []
        
        # Game state
        self._game_state = {
            'level': 1,
            'xp': 0,
            'gold': 0,
            'streak': 0,
            'last_action_date': None,
            'plant_stage': 0,  # 0-5 (seed to mature)
            'plant_health': 100,
            'achievements': [],
            'daily_tasks_completed': []
        }
        
        # Threads
        self._sensor_thread = None
        self._display_thread = None
        self._automation_thread = None
        
        print("[INIT] Controller initialized successfully!")
        print()
    
    def _init_sensors(self):
        """Initialize all sensors."""
        print("[INIT] Initializing sensors...")
        
        try:
            # Soil moisture sensor (ADC channel 0)
            self.soil_moisture = SoilMoistureSensor(
                channel=self.config['adc']['soil_moisture_channel'],
                i2c_address=self.config['adc']['address'],
                dry_value=self.config['adc']['soil_dry_value'],
                wet_value=self.config['adc']['soil_wet_value']
            )
            print("  - Soil moisture sensor: OK")
        except Exception as e:
            print(f"  - Soil moisture sensor: FAILED ({e})")
            self.soil_moisture = None
        
        try:
            # Temperature & humidity sensor (DHT22)
            self.temp_humidity = TemperatureHumiditySensor(
                pin=self.config['gpio']['dht_sensor_pin']
            )
            print("  - Temperature/humidity sensor: OK")
        except Exception as e:
            print(f"  - Temperature/humidity sensor: FAILED ({e})")
            self.temp_humidity = None
        
        try:
            # Water tank level sensor (ADC channel 1)
            self.water_tank = WaterTankSensor(
                channel=self.config['adc']['water_tank_channel'],
                i2c_address=self.config['adc']['address'],
                empty_value=self.config['adc']['tank_empty_value'],
                full_value=self.config['adc']['tank_full_value']
            )
            print("  - Water tank sensor: OK")
        except Exception as e:
            print(f"  - Water tank sensor: FAILED ({e})")
            self.water_tank = None
    
    def _init_actuators(self):
        """Initialize all actuators."""
        print("[INIT] Initializing actuators...")
        
        try:
            # Water pump
            self.pump = WaterPumpController(
                relay_pin=self.config['gpio']['pump_relay_pin'],
                active_low=True,
                max_duration_seconds=self.config['automation']['watering']['duration_seconds'],
                cooldown_seconds=self.config['automation']['watering']['cooldown_minutes'] * 60
            )
            print("  - Water pump: OK")
        except Exception as e:
            print(f"  - Water pump: FAILED ({e})")
            self.pump = None
        
        try:
            # UV grow light
            self.uv_light = UVLightController(
                relay_pin=self.config['gpio']['uv_led_relay_pin'],
                active_low=True,
                schedule_start_hour=self.config['automation']['lighting']['on_hour'],
                schedule_end_hour=self.config['automation']['lighting']['off_hour']
            )
            print("  - UV grow light: OK")
        except Exception as e:
            print(f"  - UV grow light: FAILED ({e})")
            self.uv_light = None
    
    def _init_displays(self):
        """Initialize all displays."""
        print("[INIT] Initializing displays...")
        
        try:
            # Main OLED display (sensor dashboard)
            self.oled_main = OLEDDisplay(
                width=self.config['displays']['oled_main']['width'],
                height=self.config['displays']['oled_main']['height'],
                i2c_address=self.config['displays']['oled_main']['i2c_address']
            )
            print("  - Main OLED display: OK")
        except Exception as e:
            print(f"  - Main OLED display: FAILED ({e})")
            self.oled_main = None
        
        try:
            # Secondary OLED display
            self.oled_sensors = OLEDDisplay(
                width=self.config['displays']['oled_sensors']['width'],
                height=self.config['displays']['oled_sensors']['height'],
                i2c_address=self.config['displays']['oled_sensors']['i2c_address']
            )
            print("  - Sensor OLED display: OK")
        except Exception as e:
            print(f"  - Sensor OLED display: FAILED ({e})")
            self.oled_sensors = None
        
        try:
            # IPS game display
            self.ips_display = IPSDisplay(
                width=self.config['displays']['ips_game']['width'],
                height=self.config['displays']['ips_game']['height'],
                dc_pin=self.config['displays']['ips_game']['dc_pin'],
                rst_pin=self.config['displays']['ips_game']['rst_pin'],
                backlight_pin=self.config['displays']['ips_game']['backlight_pin']
            )
            print("  - IPS game display: OK")
        except Exception as e:
            print(f"  - IPS game display: FAILED ({e})")
            self.ips_display = None
    
    def _init_analytics(self):
        """Initialize analytics module."""
        print("[INIT] Initializing analytics...")
        
        # Create data directory if needed
        os.makedirs('./data', exist_ok=True)
        
        self.analyzer = DataAnalyzer(
            database_path=self.config['storage']['database_path']
        )
        print("  - Data analyzer: OK")
    
    def _init_pid(self):
        """Initialize PID controller for irrigation."""
        print("[INIT] Initializing PID controller...")
        
        try:
            pid_config = PIDConfig(
                target_moisture=self.config['pid']['target_moisture'],
                kp=self.config['pid']['kp'],
                ki=self.config['pid']['ki'],
                kd=self.config['pid']['kd'],
                min_output=self.config['pid']['min_output'],
                max_output=self.config['pid']['max_output'],
                deadband=self.config['pid']['deadband'],
                min_cycle_time=self.config['pid']['min_cycle_time']
            )
            self.pid_controller = PIDController(config=pid_config)
            print("  - PID controller: OK")
        except Exception as e:
            print(f"  - PID controller: FAILED ({e})")
            self.pid_controller = None
    
    def _init_ai(self):
        """Initialize AI plant analyzer."""
        print("[INIT] Initializing AI analyzer...")
        
        try:
            api_key = os.getenv('GEMINI_API_KEY', self.config.get('ai', {}).get('gemini_api_key'))
            self.plant_ai = PlantAnalyzer(
                backend=AnalysisBackend.GEMINI,
                api_key=api_key
            )
            print("  - AI plant analyzer: OK")
        except Exception as e:
            print(f"  - AI plant analyzer: FAILED ({e})")
            self.plant_ai = None
    
    def _init_database(self):
        """Initialize SQLite database."""
        print("[INIT] Initializing database...")
        
        try:
            self.database = get_database(self.config['storage']['database_path'])
            print("  - SQLite database: OK")
        except Exception as e:
            print(f"  - SQLite database: FAILED ({e})")
            self.database = None
    
    def get_all_sensor_data(self) -> Dict:
        """
        Read all sensors and return combined data.
        
        Returns:
            Dictionary with all sensor readings
        """
        data = {
            'moisture': None,
            'temperature': None,
            'humidity': None,
            'water_level': None,
            'pump_active': False,
            'light_active': False,
            'timestamp': time.time()
        }
        
        # Soil moisture
        if self.soil_moisture:
            try:
                reading = self.soil_moisture.get_full_reading()
                data['moisture'] = reading['percentage']
                data['moisture_status'] = reading['status']
                data['moisture_trend'] = reading['trend']
            except Exception as e:
                print(f"[ERROR] Soil moisture read failed: {e}")
        
        # Temperature & humidity
        if self.temp_humidity:
            try:
                reading = self.temp_humidity.get_full_reading()
                data['temperature'] = reading['temperature']['value']
                data['humidity'] = reading['humidity']['value']
                data['temperature_status'] = reading['temperature']['status']
                data['humidity_status'] = reading['humidity']['status']
            except Exception as e:
                print(f"[ERROR] Temp/humidity read failed: {e}")
        
        # Water tank
        if self.water_tank:
            try:
                reading = self.water_tank.get_full_reading()
                data['water_level'] = reading['percentage']
                data['water_status'] = reading['status']
                data['waterings_remaining'] = reading['waterings_remaining']
            except Exception as e:
                print(f"[ERROR] Water tank read failed: {e}")
        
        # Actuator states
        if self.pump:
            data['pump_active'] = self.pump.get_status()['is_running']
        
        if self.uv_light:
            status = self.uv_light.get_status()
            data['light_active'] = status['is_on']
            data['light_auto_mode'] = status['auto_mode']
        
        self._last_sensor_reading = data
        return data
    
    def water_plant(self, duration_seconds: Optional[int] = None) -> Dict:
        """
        Water the plant.
        
        Args:
            duration_seconds: Watering duration (uses default if not specified)
        
        Returns:
            Result dictionary
        """
        if not self.pump:
            return {'success': False, 'error': 'Pump not available'}
        
        # Check water tank level
        if self.water_tank:
            level = self.water_tank.read_percentage()
            if level < 10:
                return {'success': False, 'error': 'Water tank too low'}
        
        # Execute watering
        result = self.pump.start(duration_seconds)
        
        if result['success']:
            # Log event
            self._log_event('watering', f"Watered for {result.get('duration_seconds', 0)}s")
            
            # Award XP
            self._award_xp(10, "Watering")
            
            # Update displays
            self._show_watering_animation()
        
        return result
    
    def check_auto_watering(self):
        """Check and execute auto-watering if needed."""
        if not self._auto_watering:
            return
        
        if not self.soil_moisture or not self.pump:
            return
        
        moisture = self.soil_moisture.read_percentage()
        threshold = self.config['automation']['watering']['min_moisture_trigger']
        
        if moisture < threshold:
            print(f"[AUTO] Moisture {moisture}% below threshold {threshold}% - watering...")
            self.water_plant()
    
    def set_auto_watering(self, enabled: bool):
        """Enable or disable auto-watering."""
        self._auto_watering = enabled
        self._log_event('config', f"Auto-watering {'enabled' if enabled else 'disabled'}")
    
    def get_plant_health(self) -> Dict:
        """Calculate current plant health score."""
        sensors = self._last_sensor_reading or self.get_all_sensor_data()
        return self.analyzer.calculate_health_score(sensors)
    
    def get_game_stats(self) -> Dict:
        """Get current game statistics."""
        return {
            **self._game_state,
            'xp_for_next_level': self._game_state['level'] * 100,
            'plant_stage_name': [
                'Seed', 'Sprout', 'Seedling', 'Vegetative', 'Flowering', 'Mature'
            ][min(self._game_state['plant_stage'], 5)]
        }
    
    def _award_xp(self, amount: int, reason: str):
        """Award XP to player."""
        self._game_state['xp'] += amount
        
        # Check for level up
        xp_needed = self._game_state['level'] * 100
        while self._game_state['xp'] >= xp_needed:
            self._game_state['xp'] -= xp_needed
            self._game_state['level'] += 1
            self._game_state['gold'] += 50
            print(f"[GAME] Level up! Now level {self._game_state['level']}")
            
            # Check plant growth
            if self._game_state['level'] % 3 == 0:
                self._grow_plant()
            
            xp_needed = self._game_state['level'] * 100
        
        self._log_event('xp', f"+{amount} XP ({reason})")
    
    def _grow_plant(self):
        """Advance plant growth stage."""
        if self._game_state['plant_stage'] < 5:
            self._game_state['plant_stage'] += 1
            stage_names = ['Seed', 'Sprout', 'Seedling', 'Vegetative', 'Flowering', 'Mature']
            stage_name = stage_names[self._game_state['plant_stage']]
            print(f"[GAME] Plant grew to {stage_name}!")
            self._log_event('growth', f"Plant advanced to {stage_name}")
    
    def _update_streak(self):
        """Update daily streak."""
        today = datetime.now().date().isoformat()
        
        if self._game_state['last_action_date'] != today:
            # Check if streak continues
            yesterday = (datetime.now().date() - timedelta(days=1)).isoformat()
            
            if self._game_state['last_action_date'] == yesterday:
                self._game_state['streak'] += 1
            else:
                self._game_state['streak'] = 1
            
            self._game_state['last_action_date'] = today
            self._game_state['daily_tasks_completed'] = []
            
            # Award streak bonus
            if self._game_state['streak'] >= 7:
                self._award_xp(50, "7-day streak!")
    
    def _log_event(self, event_type: str, description: str):
        """Log an event."""
        event = {
            'type': event_type,
            'description': description,
            'timestamp': time.time()
        }
        self._events_log.append(event)
        
        # Keep only last 100 events in memory
        if len(self._events_log) > 100:
            self._events_log = self._events_log[-100:]
        
        # Also log to database
        self.analyzer.log_event(event_type, description)
    
    def get_recent_events(self, limit: int = 50) -> list:
        """Get recent events."""
        return self._events_log[-limit:]
    
    def _show_watering_animation(self):
        """Show watering animation on displays."""
        if self.ips_display:
            for p in range(0, 101, 10):
                self.ips_display.show_watering_animation(p)
                time.sleep(0.1)
    
    def _sensor_loop(self):
        """Background loop for sensor reading."""
        interval = self.config['automation']['sensor_poll_interval']
        log_interval = self.config['automation']['data_log_interval']
        last_log = 0
        
        while self._running:
            try:
                # Read sensors
                data = self.get_all_sensor_data()
                
                # Log to database periodically
                if time.time() - last_log >= log_interval:
                    self.analyzer.log_sensor_reading(
                        moisture=data.get('moisture'),
                        temperature=data.get('temperature'),
                        humidity=data.get('humidity'),
                        water_level=data.get('water_level'),
                        pump_active=data.get('pump_active', False),
                        light_active=data.get('light_active', False)
                    )
                    last_log = time.time()
                
                # Update displays
                self._update_displays(data)
                
            except Exception as e:
                print(f"[ERROR] Sensor loop error: {e}")
            
            time.sleep(interval)
    
    def _update_displays(self, data: Dict):
        """Update all displays with current data."""
        # Main OLED - sensor dashboard
        if self.oled_main:
            try:
                self.oled_main.show_sensor_dashboard(data)
            except Exception as e:
                print(f"[ERROR] OLED main update failed: {e}")
        
        # IPS - game screen
        if self.ips_display:
            try:
                game = self._game_state
                self.ips_display.show_game_screen(
                    player_level=game['level'],
                    xp=game['xp'],
                    xp_needed=game['level'] * 100,
                    gold=game['gold'],
                    streak=game['streak'],
                    plant_stage=game['plant_stage'],
                    plant_health=game['plant_health'],
                    sensors=data
                )
            except Exception as e:
                print(f"[ERROR] IPS display update failed: {e}")
    
    def _automation_loop(self):
        """Background loop for automation tasks."""
        while self._running:
            try:
                # Check auto-watering
                self.check_auto_watering()
                
                # Check light schedule
                if self.uv_light:
                    self.uv_light.check_schedule()
                
                # Update streak
                self._update_streak()
                
                # Update plant health
                health = self.get_plant_health()
                self._game_state['plant_health'] = health.get('overall_score', 100)
                
            except Exception as e:
                print(f"[ERROR] Automation loop error: {e}")
            
            time.sleep(60)  # Check every minute
    
    def start(self):
        """Start the greenhouse controller."""
        print("[START] Starting SmartGrow controller...")
        
        self._running = True
        
        # Start background threads
        self._sensor_thread = threading.Thread(
            target=self._sensor_loop,
            daemon=True,
            name="SensorThread"
        )
        self._sensor_thread.start()
        print("  - Sensor thread: Started")
        
        self._automation_thread = threading.Thread(
            target=self._automation_loop,
            daemon=True,
            name="AutomationThread"
        )
        self._automation_thread.start()
        print("  - Automation thread: Started")
        
        print()
        print("[READY] SmartGrow is running!")
        print("        Press Ctrl+C to stop")
        print()
    
    def stop(self):
        """Stop the greenhouse controller."""
        print()
        print("[STOP] Stopping SmartGrow controller...")
        
        self._running = False
        
        # Turn off actuators
        if self.pump:
            self.pump.emergency_stop()
            self.pump.cleanup()
        
        if self.uv_light:
            self.uv_light.cleanup()
        
        # Turn off displays
        if self.oled_main:
            self.oled_main.power_off()
        
        if self.oled_sensors:
            self.oled_sensors.power_off()
        
        if self.ips_display:
            self.ips_display.power_off()
        
        # Cleanup sensors
        if self.temp_humidity:
            self.temp_humidity.cleanup()
        
        print("[STOP] SmartGrow stopped cleanly")


def main():
    """Main entry point."""
    # Initialize controller
    controller = GreenhouseController('./config.yaml')
    
    # Handle shutdown signals
    def signal_handler(sig, frame):
        controller.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start controller
    controller.start()
    
    # Start API server (blocks)
    api = SmartGrowAPI(
        controller,
        config_path='./config.yaml',
        host=controller.config['api']['host'],
        port=controller.config['api']['port']
    )
    
    try:
        api.start(debug=False)
    except KeyboardInterrupt:
        controller.stop()


if __name__ == "__main__":
    main()
