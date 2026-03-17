"""
SmartGrow GPIO Configuration
Raspberry Pi 4 - BCM Pin Numbering

Hardware mapping based on physical product:
- Pump relay: GPIO 24
- UV LED strip: GPIO 22  
- Soil moisture sensor: GPIO 27
- I2C displays via PCA9578A multiplexer
"""

# Actuators (Output)
PUMP_RELAY_PIN = 24      # Water pump relay control
UV_LIGHT_PIN = 22        # UV LED strip relay

# Sensors (Input)
MOISTURE_SENSOR_PIN = 27  # Soil moisture digital input

# I2C Configuration
I2C_BUS = 1              # I2C bus number (1 for Pi 4)
PCA9578A_ADDRESS = 0x20  # I2C multiplexer address

# Display channels on PCA9578A
DISPLAY_CHANNEL_0 = 0    # Main status display
DISPLAY_CHANNEL_1 = 1    # Sensor data display

# DHT22 Temperature/Humidity sensor
DHT22_PIN = 4            # DHT22 data pin

# ADC for analog moisture reading (if using ADS1115)
ADS1115_ADDRESS = 0x48   # ADC I2C address
MOISTURE_ADC_CHANNEL = 0 # ADC channel for moisture

# Timing constants (seconds)
PUMP_MIN_DURATION = 0.5
PUMP_MAX_DURATION = 10.0
PUMP_COOLDOWN = 60       # Minimum time between watering

UV_SCHEDULE_ON = 7       # Hour to turn on UV (7:00)
UV_SCHEDULE_OFF = 22     # Hour to turn off UV (22:00)

# Sensor reading intervals
SENSOR_READ_INTERVAL = 5  # Read sensors every 5 seconds
DISPLAY_UPDATE_INTERVAL = 2  # Update displays every 2 seconds

# PID Controller defaults
PID_TARGET_MOISTURE = 45  # Target soil moisture %
PID_KP = 2.0
PID_KI = 0.1
PID_KD = 0.5

# Safety limits
MAX_DAILY_WATER_ML = 500  # Maximum water per day
MIN_WATER_TANK_LEVEL = 10  # Minimum tank level % before warning
