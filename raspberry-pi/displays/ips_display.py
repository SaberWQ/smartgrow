"""
SmartGrow - IPS Display Module (ST7789)
240x240 Color IPS display for game interface
Infomatrix Ukraine 2026
"""

import time
import board
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789
from typing import Dict, List, Tuple, Optional


class IPSDisplay:
    """
    ST7789 Color IPS Display controller.
    
    240x240 pixel color display via SPI.
    Used for game interface and plant visualization.
    """
    
    # Color palette (SmartGrow theme)
    COLORS = {
        'black': (0, 0, 0),
        'white': (255, 255, 255),
        'green': (34, 197, 94),
        'dark_green': (22, 163, 74),
        'light_green': (134, 239, 172),
        'yellow': (250, 204, 21),
        'orange': (249, 115, 22),
        'red': (239, 68, 68),
        'blue': (59, 130, 246),
        'purple': (168, 85, 247),
        'gray': (75, 85, 99),
        'dark_gray': (31, 41, 55),
        'bg_dark': (17, 24, 39),
    }
    
    # Plant growth stages
    PLANT_STAGES = ['seed', 'sprout', 'seedling', 'vegetative', 'flowering', 'mature']
    
    def __init__(
        self,
        width: int = 240,
        height: int = 240,
        spi_port: int = 0,
        cs_pin: int = 0,
        dc_pin: int = 25,
        rst_pin: int = 24,
        backlight_pin: int = 23,
        rotation: int = 180
    ):
        """
        Initialize the IPS display.
        
        Args:
            width, height: Display dimensions
            spi_port: SPI port number
            cs_pin: Chip select GPIO pin
            dc_pin: Data/Command GPIO pin
            rst_pin: Reset GPIO pin
            backlight_pin: Backlight control GPIO pin
            rotation: Display rotation
        """
        self.width = width
        self.height = height
        self.rotation = rotation
        
        # Initialize SPI
        spi = board.SPI()
        
        # Configure pins
        cs = digitalio.DigitalInOut(getattr(board, f'D{cs_pin}'))
        dc = digitalio.DigitalInOut(getattr(board, f'D{dc_pin}'))
        rst = digitalio.DigitalInOut(getattr(board, f'D{rst_pin}'))
        
        # Backlight control
        self.backlight = digitalio.DigitalInOut(getattr(board, f'D{backlight_pin}'))
        self.backlight.direction = digitalio.Direction.OUTPUT
        self.backlight.value = True
        
        # Initialize display
        self.display = st7789.ST7789(
            spi, height=height, width=width,
            cs=cs, dc=dc, rst=rst,
            rotation=rotation,
            baudrate=64000000
        )
        
        # Create image buffer
        self.image = Image.new('RGB', (width, height), self.COLORS['bg_dark'])
        self.draw = ImageDraw.Draw(self.image)
        
        # Load fonts
        try:
            self.font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 12)
            self.font_medium = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
            self.font_large = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 24)
            self.font_xlarge = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 36)
        except:
            self.font_small = ImageFont.load_default()
            self.font_medium = ImageFont.load_default()
            self.font_large = ImageFont.load_default()
            self.font_xlarge = ImageFont.load_default()
    
    def clear(self, color: str = 'bg_dark'):
        """Clear display with specified color."""
        self.draw.rectangle(
            (0, 0, self.width, self.height),
            fill=self.COLORS.get(color, self.COLORS['bg_dark'])
        )
    
    def show(self):
        """Push buffer to display."""
        self.display.image(self.image)
    
    def set_backlight(self, on: bool):
        """Control backlight."""
        self.backlight.value = on
    
    def draw_text(
        self,
        text: str,
        x: int,
        y: int,
        color: str = 'white',
        font_size: str = 'medium'
    ):
        """Draw text on display."""
        fonts = {
            'small': self.font_small,
            'medium': self.font_medium,
            'large': self.font_large,
            'xlarge': self.font_xlarge
        }
        font = fonts.get(font_size, self.font_medium)
        self.draw.text((x, y), text, font=font, fill=self.COLORS.get(color, (255, 255, 255)))
    
    def draw_centered_text(self, text: str, y: int, color: str = 'white', font_size: str = 'medium'):
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
        self.draw.text((x, y), text, font=font, fill=self.COLORS.get(color, (255, 255, 255)))
    
    def draw_progress_bar(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        percentage: float,
        bg_color: str = 'dark_gray',
        fill_color: str = 'green',
        border_color: str = 'gray'
    ):
        """Draw a progress bar."""
        # Background
        self.draw.rectangle(
            (x, y, x + width, y + height),
            fill=self.COLORS[bg_color],
            outline=self.COLORS[border_color]
        )
        
        # Fill
        fill_width = int((width - 4) * (percentage / 100))
        if fill_width > 0:
            self.draw.rectangle(
                (x + 2, y + 2, x + 2 + fill_width, y + height - 2),
                fill=self.COLORS[fill_color]
            )
    
    def draw_circular_gauge(
        self,
        cx: int,
        cy: int,
        radius: int,
        percentage: float,
        color: str = 'green',
        thickness: int = 8,
        label: str = '',
        value_text: str = ''
    ):
        """Draw a circular gauge."""
        import math
        
        # Background arc
        self.draw.arc(
            (cx - radius, cy - radius, cx + radius, cy + radius),
            -225, 45,
            fill=self.COLORS['dark_gray'],
            width=thickness
        )
        
        # Value arc
        end_angle = -225 + (270 * percentage / 100)
        self.draw.arc(
            (cx - radius, cy - radius, cx + radius, cy + radius),
            -225, end_angle,
            fill=self.COLORS[color],
            width=thickness
        )
        
        # Center value
        if value_text:
            self.draw_centered_text(value_text, cy - 15, color, 'large')
        
        # Label below
        if label:
            self.draw_centered_text(label, cy + 15, 'white', 'small')
    
    def draw_plant(self, stage: int, x: int, y: int, health: float = 100):
        """
        Draw plant at given growth stage.
        
        Args:
            stage: Growth stage (0-5)
            x, y: Position
            health: Plant health percentage (affects color)
        """
        # Health affects color
        if health > 70:
            stem_color = self.COLORS['dark_green']
            leaf_color = self.COLORS['green']
        elif health > 40:
            stem_color = (139, 119, 42)  # Yellowish
            leaf_color = self.COLORS['yellow']
        else:
            stem_color = (139, 90, 43)  # Brown
            leaf_color = self.COLORS['orange']
        
        pot_color = (139, 90, 43)  # Brown pot
        soil_color = (101, 67, 33)
        
        if stage == 0:  # Seed
            # Pot
            self.draw.rectangle((x + 20, y + 60, x + 80, y + 90), fill=pot_color)
            self.draw.rectangle((x + 25, y + 55, x + 75, y + 65), fill=soil_color)
            # Seed in soil
            self.draw.ellipse((x + 42, y + 45, x + 58, y + 60), fill=(210, 180, 140))
            
        elif stage == 1:  # Sprout
            # Pot
            self.draw.rectangle((x + 20, y + 60, x + 80, y + 90), fill=pot_color)
            self.draw.rectangle((x + 25, y + 55, x + 75, y + 65), fill=soil_color)
            # Small stem
            self.draw.rectangle((x + 48, y + 40, x + 52, y + 55), fill=stem_color)
            # Two small leaves
            self.draw.ellipse((x + 35, y + 30, x + 50, y + 45), fill=leaf_color)
            self.draw.ellipse((x + 50, y + 30, x + 65, y + 45), fill=leaf_color)
            
        elif stage == 2:  # Seedling
            # Pot
            self.draw.rectangle((x + 20, y + 60, x + 80, y + 90), fill=pot_color)
            self.draw.rectangle((x + 25, y + 55, x + 75, y + 65), fill=soil_color)
            # Taller stem
            self.draw.rectangle((x + 47, y + 25, x + 53, y + 55), fill=stem_color)
            # More leaves
            self.draw.ellipse((x + 25, y + 25, x + 48, y + 45), fill=leaf_color)
            self.draw.ellipse((x + 52, y + 25, x + 75, y + 45), fill=leaf_color)
            self.draw.ellipse((x + 30, y + 10, x + 50, y + 30), fill=leaf_color)
            self.draw.ellipse((x + 50, y + 10, x + 70, y + 30), fill=leaf_color)
            
        elif stage == 3:  # Vegetative
            # Pot
            self.draw.rectangle((x + 15, y + 70, x + 85, y + 95), fill=pot_color)
            self.draw.rectangle((x + 20, y + 65, x + 80, y + 75), fill=soil_color)
            # Thick stem
            self.draw.rectangle((x + 45, y + 15, x + 55, y + 65), fill=stem_color)
            # Many leaves
            for offset in [0, 15, 30]:
                self.draw.ellipse((x + 15, y + offset, x + 48, y + offset + 25), fill=leaf_color)
                self.draw.ellipse((x + 52, y + offset, x + 85, y + offset + 25), fill=leaf_color)
            
        elif stage == 4:  # Flowering
            # Pot
            self.draw.rectangle((x + 10, y + 75, x + 90, y + 100), fill=pot_color)
            self.draw.rectangle((x + 15, y + 70, x + 85, y + 80), fill=soil_color)
            # Stem
            self.draw.rectangle((x + 45, y + 10, x + 55, y + 70), fill=stem_color)
            # Leaves
            for offset in [10, 30, 50]:
                self.draw.ellipse((x + 10, y + offset, x + 48, y + offset + 25), fill=leaf_color)
                self.draw.ellipse((x + 52, y + offset, x + 90, y + offset + 25), fill=leaf_color)
            # Flower buds
            self.draw.ellipse((x + 35, y - 5, x + 55, y + 15), fill=self.COLORS['yellow'])
            self.draw.ellipse((x + 55, y, x + 75, y + 20), fill=self.COLORS['yellow'])
            
        else:  # Mature
            # Pot
            self.draw.rectangle((x + 5, y + 80, x + 95, y + 105), fill=pot_color)
            self.draw.rectangle((x + 10, y + 75, x + 90, y + 85), fill=soil_color)
            # Thick stem
            self.draw.rectangle((x + 43, y + 5, x + 57, y + 75), fill=stem_color)
            # Large leaves
            for offset in [5, 25, 45]:
                self.draw.ellipse((x + 5, y + offset, x + 45, y + offset + 30), fill=leaf_color)
                self.draw.ellipse((x + 55, y + offset, x + 95, y + offset + 30), fill=leaf_color)
            # Flowers/Fruit
            self.draw.ellipse((x + 30, y - 10, x + 55, y + 15), fill=self.COLORS['red'])
            self.draw.ellipse((x + 55, y - 5, x + 80, y + 20), fill=self.COLORS['red'])
            self.draw.ellipse((x + 40, y + 5, x + 60, y + 25), fill=self.COLORS['red'])
    
    def show_game_screen(
        self,
        player_level: int,
        xp: int,
        xp_needed: int,
        gold: int,
        streak: int,
        plant_stage: int,
        plant_health: float,
        sensors: Dict
    ):
        """
        Show main game screen.
        
        Args:
            player_level: Current level
            xp: Current XP
            xp_needed: XP needed for next level
            gold: Gold amount
            streak: Day streak
            plant_stage: Plant growth stage (0-5)
            plant_health: Plant health percentage
            sensors: Sensor data dict
        """
        self.clear()
        
        # Header
        self.draw.rectangle((0, 0, self.width, 35), fill=self.COLORS['dark_gray'])
        self.draw_text("SMARTGROW", 10, 5, 'green', 'large')
        self.draw_text(f"Lv.{player_level}", 180, 10, 'yellow', 'medium')
        
        # XP Bar
        self.draw_progress_bar(10, 38, 220, 12, (xp / xp_needed) * 100, fill_color='green')
        self.draw_text(f"{xp}/{xp_needed} XP", 85, 38, 'white', 'small')
        
        # Plant area
        self.draw.rectangle((20, 55, 130, 170), fill=(17, 24, 39), outline=self.COLORS['gray'])
        self.draw_plant(plant_stage, 25, 60, plant_health)
        
        # Plant info
        stage_names = ['Seed', 'Sprout', 'Seedling', 'Vegetative', 'Flowering', 'Mature']
        self.draw_text(stage_names[min(plant_stage, 5)], 45, 172, 'green', 'small')
        
        # Stats panel
        self.draw.rectangle((140, 55, 230, 170), fill=self.COLORS['dark_gray'], outline=self.COLORS['gray'])
        
        # Gold
        self.draw_text(f"Gold: {gold}", 148, 60, 'yellow', 'small')
        
        # Streak
        self.draw_text(f"Streak: {streak}d", 148, 80, 'orange', 'small')
        
        # Health
        self.draw_text("Health:", 148, 105, 'white', 'small')
        health_color = 'green' if plant_health > 70 else ('yellow' if plant_health > 40 else 'red')
        self.draw_progress_bar(148, 120, 75, 10, plant_health, fill_color=health_color)
        
        # Mini sensor values
        self.draw_text(f"M:{sensors.get('moisture', '--')}%", 148, 138, 'blue', 'small')
        self.draw_text(f"T:{sensors.get('temperature', '--')}C", 148, 153, 'red', 'small')
        
        # Bottom status bar
        self.draw.rectangle((0, 180, self.width, self.height), fill=self.COLORS['dark_gray'])
        
        # Sensor mini icons
        moisture = sensors.get('moisture', 50)
        m_color = 'green' if 35 <= moisture <= 65 else 'yellow'
        self.draw.rectangle((15, 195, 55, 225), fill=self.COLORS[m_color], outline=self.COLORS['white'])
        self.draw_text("M", 30, 200, 'white', 'medium')
        
        temp = sensors.get('temperature', 25)
        t_color = 'green' if 20 <= temp <= 28 else 'yellow'
        self.draw.rectangle((65, 195, 105, 225), fill=self.COLORS[t_color], outline=self.COLORS['white'])
        self.draw_text("T", 80, 200, 'white', 'medium')
        
        humidity = sensors.get('humidity', 60)
        h_color = 'green' if 50 <= humidity <= 70 else 'yellow'
        self.draw.rectangle((115, 195, 155, 225), fill=self.COLORS[h_color], outline=self.COLORS['white'])
        self.draw_text("H", 130, 200, 'white', 'medium')
        
        water = sensors.get('water_level', 50)
        w_color = 'green' if water > 30 else ('yellow' if water > 15 else 'red')
        self.draw.rectangle((165, 195, 205, 225), fill=self.COLORS[w_color], outline=self.COLORS['white'])
        self.draw_text("W", 180, 200, 'white', 'medium')
        
        self.show()
    
    def show_achievement(self, title: str, description: str, icon: str = 'star'):
        """Show achievement unlocked screen."""
        self.clear()
        
        # Background glow effect
        for i in range(5):
            r = 80 - i * 10
            alpha = 255 - i * 40
            self.draw.ellipse(
                (self.width//2 - r, self.height//2 - r - 20,
                 self.width//2 + r, self.height//2 + r - 20),
                fill=(34, 197, 94, alpha)
            )
        
        # Achievement banner
        self.draw.rectangle((20, 60, 220, 180), fill=self.COLORS['dark_gray'], outline=self.COLORS['green'])
        
        # Star icon (simplified)
        self.draw.polygon([
            (120, 75), (130, 100), (155, 105),
            (135, 120), (140, 145), (120, 130),
            (100, 145), (105, 120), (85, 105), (110, 100)
        ], fill=self.COLORS['yellow'])
        
        # Text
        self.draw_centered_text("ACHIEVEMENT", 30, 'green', 'medium')
        self.draw_centered_text("UNLOCKED!", 48, 'green', 'medium')
        self.draw_centered_text(title, 148, 'white', 'medium')
        self.draw_centered_text(description, 165, 'gray', 'small')
        
        self.show()
    
    def show_watering_animation(self, progress: float):
        """Show watering in progress animation."""
        self.clear()
        
        # Water drops
        import random
        for _ in range(int(progress / 10)):
            x = random.randint(60, 180)
            y = random.randint(80, 160)
            size = random.randint(5, 15)
            self.draw.ellipse((x, y, x + size, y + size * 2), fill=self.COLORS['blue'])
        
        # Progress bar
        self.draw_centered_text("WATERING", 30, 'blue', 'large')
        self.draw_progress_bar(30, 200, 180, 20, progress, fill_color='blue')
        self.draw_centered_text(f"{int(progress)}%", 203, 'white', 'small')
        
        self.show()
    
    def power_off(self):
        """Turn off display."""
        self.clear('black')
        self.show()
        self.set_backlight(False)


# Standalone testing
if __name__ == "__main__":
    print("SmartGrow - IPS Display Test")
    print("=" * 35)
    
    try:
        display = IPSDisplay(
            width=240,
            height=240,
            dc_pin=25,
            rst_pin=24,
            backlight_pin=23
        )
        
        print("Display initialized!")
        
        # Test game screen
        print("Showing game screen...")
        display.show_game_screen(
            player_level=5,
            xp=350,
            xp_needed=500,
            gold=150,
            streak=7,
            plant_stage=3,
            plant_health=85,
            sensors={
                'moisture': 45,
                'temperature': 24,
                'humidity': 60,
                'water_level': 75
            }
        )
        time.sleep(5)
        
        # Test achievement
        print("Showing achievement...")
        display.show_achievement("Green Thumb", "Water plant 10 times")
        time.sleep(3)
        
        # Test watering animation
        print("Showing watering animation...")
        for p in range(0, 101, 10):
            display.show_watering_animation(p)
            time.sleep(0.3)
        
        print("Test complete!")
        display.power_off()
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure ST7789 is connected via SPI")
