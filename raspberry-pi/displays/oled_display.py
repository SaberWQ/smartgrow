"""
SmartGrow - OLED Display Module (SSD1306)
I2C OLED displays for sensor data and status
Infomatrix Ukraine 2026
"""

import time
import board
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
from typing import Dict, List, Optional, Tuple


class OLEDDisplay:
    """
    SSD1306 OLED Display controller.
    
    Supports 128x64 and 128x32 displays via I2C.
    Uses Pillow for rendering graphics and text.
    """
    
    def __init__(
        self,
        width: int = 128,
        height: int = 64,
        i2c_address: int = 0x3C,
        rotation: int = 0
    ):
        """
        Initialize the OLED display.
        
        Args:
            width: Display width in pixels
            height: Display height in pixels
            i2c_address: I2C address (0x3C or 0x3D)
            rotation: Rotation in degrees (0, 90, 180, 270)
        """
        self.width = width
        self.height = height
        self.rotation = rotation
        
        # Initialize I2C
        self.i2c = busio.I2C(board.SCL, board.SDA)
        
        # Initialize display
        self.display = adafruit_ssd1306.SSD1306_I2C(
            width, height, self.i2c, addr=i2c_address
        )
        
        # Clear display
        self.display.fill(0)
        self.display.show()
        
        # Create image buffer
        self.image = Image.new('1', (width, height))
        self.draw = ImageDraw.Draw(self.image)
        
        # Load fonts
        try:
            self.font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 9)
            self.font_medium = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 12)
            self.font_large = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 16)
            self.font_xlarge = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 24)
        except:
            # Fallback to default font
            self.font_small = ImageFont.load_default()
            self.font_medium = ImageFont.load_default()
            self.font_large = ImageFont.load_default()
            self.font_xlarge = ImageFont.load_default()
    
    def clear(self):
        """Clear the display buffer."""
        self.draw.rectangle((0, 0, self.width, self.height), fill=0)
    
    def show(self):
        """Push buffer to display."""
        if self.rotation != 0:
            rotated = self.image.rotate(self.rotation)
            self.display.image(rotated)
        else:
            self.display.image(self.image)
        self.display.show()
    
    def draw_text(
        self,
        text: str,
        x: int,
        y: int,
        font_size: str = 'medium',
        fill: int = 1
    ):
        """
        Draw text on display.
        
        Args:
            text: Text to draw
            x: X position
            y: Y position
            font_size: 'small', 'medium', 'large', 'xlarge'
            fill: 1 for white, 0 for black
        """
        fonts = {
            'small': self.font_small,
            'medium': self.font_medium,
            'large': self.font_large,
            'xlarge': self.font_xlarge
        }
        font = fonts.get(font_size, self.font_medium)
        self.draw.text((x, y), text, font=font, fill=fill)
    
    def draw_centered_text(
        self,
        text: str,
        y: int,
        font_size: str = 'medium',
        fill: int = 1
    ):
        """Draw horizontally centered text."""
        fonts = {
            'small': self.font_small,
            'medium': self.font_medium,
            'large': self.font_large,
            'xlarge': self.font_xlarge
        }
        font = fonts.get(font_size, self.font_medium)
        bbox = self.draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        self.draw.text((x, y), text, font=font, fill=fill)
    
    def draw_progress_bar(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        percentage: float,
        show_text: bool = True
    ):
        """
        Draw a progress bar.
        
        Args:
            x, y: Position
            width, height: Size
            percentage: Fill percentage (0-100)
            show_text: Show percentage text
        """
        # Border
        self.draw.rectangle(
            (x, y, x + width, y + height),
            outline=1, fill=0
        )
        
        # Fill
        fill_width = int((width - 2) * (percentage / 100))
        if fill_width > 0:
            self.draw.rectangle(
                (x + 1, y + 1, x + 1 + fill_width, y + height - 1),
                fill=1
            )
        
        # Text
        if show_text:
            text = f"{int(percentage)}%"
            bbox = self.draw.textbbox((0, 0), text, font=self.font_small)
            text_width = bbox[2] - bbox[0]
            text_x = x + (width - text_width) // 2
            text_y = y + (height - 9) // 2
            self.draw.text((text_x, text_y), text, font=self.font_small, fill=1)
    
    def draw_icon(self, icon_type: str, x: int, y: int, size: int = 16):
        """
        Draw a simple icon.
        
        Args:
            icon_type: 'water', 'sun', 'temp', 'humidity', 'plant'
            x, y: Position
            size: Icon size
        """
        if icon_type == 'water':
            # Water drop
            self.draw.polygon([
                (x + size//2, y),
                (x + size, y + size*2//3),
                (x + size//2, y + size),
                (x, y + size*2//3)
            ], outline=1, fill=0)
        
        elif icon_type == 'sun':
            # Sun circle with rays
            r = size // 3
            cx, cy = x + size//2, y + size//2
            self.draw.ellipse((cx-r, cy-r, cx+r, cy+r), outline=1, fill=0)
            # Rays
            for angle in range(0, 360, 45):
                import math
                rad = math.radians(angle)
                x1 = cx + int(r * 1.5 * math.cos(rad))
                y1 = cy + int(r * 1.5 * math.sin(rad))
                x2 = cx + int(r * 2 * math.cos(rad))
                y2 = cy + int(r * 2 * math.sin(rad))
                self.draw.line((x1, y1, x2, y2), fill=1)
        
        elif icon_type == 'temp':
            # Thermometer
            self.draw.rectangle((x + size//3, y, x + size*2//3, y + size*3//4), outline=1)
            self.draw.ellipse((x + size//4, y + size//2, x + size*3//4, y + size), outline=1, fill=1)
        
        elif icon_type == 'humidity':
            # Cloud
            self.draw.arc((x, y + size//3, x + size//2, y + size), 180, 0, fill=1)
            self.draw.arc((x + size//4, y, x + size*3//4, y + size*2//3), 180, 0, fill=1)
            self.draw.arc((x + size//2, y + size//3, x + size, y + size), 180, 0, fill=1)
        
        elif icon_type == 'plant':
            # Simple plant
            self.draw.line((x + size//2, y + size, x + size//2, y + size//2), fill=1, width=2)
            self.draw.arc((x, y, x + size//2, y + size//2), 90, 270, fill=1)
            self.draw.arc((x + size//2, y, x + size, y + size//2), 270, 90, fill=1)
    
    def draw_sensor_card(
        self,
        label: str,
        value: str,
        unit: str,
        icon: str,
        y_offset: int = 0
    ):
        """
        Draw a sensor data card.
        
        Args:
            label: Sensor label
            value: Sensor value
            unit: Unit of measurement
            icon: Icon type
            y_offset: Vertical offset
        """
        # Icon
        self.draw_icon(icon, 2, y_offset + 2, 12)
        
        # Label
        self.draw_text(label, 18, y_offset, 'small')
        
        # Value
        self.draw_text(f"{value}{unit}", 18, y_offset + 12, 'large')
    
    def show_sensor_dashboard(self, sensors: Dict):
        """
        Display sensor dashboard.
        
        Args:
            sensors: Dict with moisture, temperature, humidity, water_level
        """
        self.clear()
        
        # Header
        self.draw_centered_text("SMARTGROW", 0, 'medium')
        self.draw.line((0, 14, self.width, 14), fill=1)
        
        # Sensor values (2x2 grid)
        # Moisture
        self.draw_text("M:", 2, 18, 'small')
        self.draw_text(f"{sensors.get('moisture', '--')}%", 14, 18, 'medium')
        
        # Temperature
        self.draw_text("T:", 66, 18, 'small')
        self.draw_text(f"{sensors.get('temperature', '--')}C", 78, 18, 'medium')
        
        # Humidity
        self.draw_text("H:", 2, 36, 'small')
        self.draw_text(f"{sensors.get('humidity', '--')}%", 14, 36, 'medium')
        
        # Water tank
        self.draw_text("W:", 66, 36, 'small')
        self.draw_text(f"{sensors.get('water_level', '--')}%", 78, 36, 'medium')
        
        # Status bar
        self.draw.line((0, 52, self.width, 52), fill=1)
        
        pump_status = "ON" if sensors.get('pump_active') else "OFF"
        light_status = "ON" if sensors.get('light_active') else "OFF"
        self.draw_text(f"Pump:{pump_status} Light:{light_status}", 2, 54, 'small')
        
        self.show()
    
    def show_large_value(self, label: str, value: str, unit: str):
        """
        Display a single large value (for dedicated sensor display).
        
        Args:
            label: Label text
            value: Value to display
            unit: Unit
        """
        self.clear()
        
        # Label at top
        self.draw_centered_text(label, 2, 'small')
        
        # Large value in center
        self.draw_centered_text(value, 18, 'xlarge')
        
        # Unit at bottom
        self.draw_centered_text(unit, 50, 'medium')
        
        self.show()
    
    def show_status_message(self, title: str, message: str, icon: Optional[str] = None):
        """
        Show a status message.
        
        Args:
            title: Title text
            message: Message text
            icon: Optional icon
        """
        self.clear()
        
        if icon:
            self.draw_icon(icon, self.width//2 - 8, 4, 16)
            self.draw_centered_text(title, 24, 'medium')
            self.draw_centered_text(message, 40, 'small')
        else:
            self.draw_centered_text(title, 10, 'large')
            self.draw_centered_text(message, 35, 'small')
        
        self.show()
    
    def show_game_stats(self, level: int, xp: int, gold: int, streak: int):
        """
        Show game statistics.
        
        Args:
            level: Player level
            xp: Current XP
            gold: Gold amount
            streak: Current streak
        """
        self.clear()
        
        # Header
        self.draw_centered_text("GAME STATS", 0, 'small')
        self.draw.line((0, 12, self.width, 12), fill=1)
        
        # Stats
        self.draw_text(f"Level: {level}", 4, 16, 'medium')
        self.draw_text(f"XP: {xp}", 4, 30, 'medium')
        self.draw_text(f"Gold: {gold}", 68, 16, 'medium')
        self.draw_text(f"Streak: {streak}d", 68, 30, 'medium')
        
        # XP Progress bar
        xp_for_level = level * 100
        xp_progress = (xp % xp_for_level) / xp_for_level * 100
        self.draw_progress_bar(4, 48, 120, 12, xp_progress)
        
        self.show()
    
    def power_off(self):
        """Turn off display."""
        self.display.fill(0)
        self.display.show()


# Standalone testing
if __name__ == "__main__":
    print("SmartGrow - OLED Display Test")
    print("=" * 35)
    
    try:
        display = OLEDDisplay(width=128, height=64, i2c_address=0x3C)
        
        print("Display initialized!")
        
        # Test sensor dashboard
        print("Showing sensor dashboard...")
        display.show_sensor_dashboard({
            'moisture': 45,
            'temperature': 24,
            'humidity': 60,
            'water_level': 75,
            'pump_active': False,
            'light_active': True
        })
        time.sleep(3)
        
        # Test large value
        print("Showing large value...")
        display.show_large_value("MOISTURE", "45", "%")
        time.sleep(3)
        
        # Test game stats
        print("Showing game stats...")
        display.show_game_stats(level=5, xp=350, gold=150, streak=7)
        time.sleep(3)
        
        # Test status message
        print("Showing status message...")
        display.show_status_message("WATERING", "Starting pump...", "water")
        time.sleep(3)
        
        print("Test complete!")
        display.power_off()
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure SSD1306 is connected via I2C")
