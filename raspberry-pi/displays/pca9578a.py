"""
SmartGrow - PCA9578A I2C Display Multiplexer
Controls multiple displays via I2C multiplexer
"""

import time
from typing import Dict, Optional, List
from dataclasses import dataclass

try:
    import smbus2
    SMBUS_AVAILABLE = True
except ImportError:
    SMBUS_AVAILABLE = False
    print("[PCA9578A] smbus2 not available - simulation mode")


# I2C Configuration
I2C_BUS = 1
PCA9578A_ADDRESS = 0x20  # Default I2C address

# Display channels
DISPLAY_CHANNEL_0 = 0  # Main status display
DISPLAY_CHANNEL_1 = 1  # Sensor data display


@dataclass
class DisplayState:
    """State of a single display"""
    channel: int
    content: str = ""
    line1: str = ""
    line2: str = ""
    line3: str = ""
    line4: str = ""
    backlight: bool = True
    last_update: float = 0


class PCA9578AController:
    """
    PCA9578A I2C Multiplexer for controlling multiple displays.
    
    Supports:
    - 2 displays on channels 0 and 1
    - OLED/LCD character displays
    - Backlight control
    """
    
    def __init__(
        self,
        address: int = PCA9578A_ADDRESS,
        simulation: bool = False
    ):
        self.address = address
        self.simulation = simulation or not SMBUS_AVAILABLE
        self._bus = None
        
        # Track display states
        self.displays: Dict[int, DisplayState] = {
            0: DisplayState(channel=0),
            1: DisplayState(channel=1)
        }
        
        if not self.simulation:
            self._setup_i2c()
        
        print(f"[PCA9578A] Initialized at 0x{address:02X} (sim={self.simulation})")
    
    def _setup_i2c(self):
        """Initialize I2C bus"""
        try:
            self._bus = smbus2.SMBus(I2C_BUS)
            # Test connection
            self._bus.read_byte(self.address)
            print(f"[PCA9578A] I2C bus {I2C_BUS} connected")
        except Exception as e:
            print(f"[PCA9578A] I2C setup error: {e}")
            self.simulation = True
    
    def select_channel(self, channel: int) -> bool:
        """
        Select display channel on multiplexer.
        
        Args:
            channel: Channel number (0 or 1)
        
        Returns:
            True if successful
        """
        if channel not in [0, 1]:
            print(f"[PCA9578A] Invalid channel: {channel}")
            return False
        
        if self.simulation:
            return True
        
        try:
            # Set channel bit (bit 0 = channel 0, bit 1 = channel 1)
            self._bus.write_byte(self.address, 1 << channel)
            return True
        except Exception as e:
            print(f"[PCA9578A] Channel select error: {e}")
            return False
    
    def write_display(self, channel: int, text: str) -> Dict:
        """
        Write text to display.
        
        Args:
            channel: Display channel (0 or 1)
            text: Text to display (will be truncated to fit)
        
        Returns:
            Result dictionary
        """
        if channel not in self.displays:
            return {"success": False, "error": f"Invalid channel: {channel}"}
        
        # Select channel
        if not self.select_channel(channel):
            return {"success": False, "error": "Channel select failed"}
        
        # Update state
        self.displays[channel].content = text
        self.displays[channel].last_update = time.time()
        
        if self.simulation:
            print(f"[DISPLAY {channel}] {text}")
            return {"success": True, "channel": channel, "text": text}
        
        try:
            # Send text bytes to display
            # This is a simplified version - real implementation depends on display type
            text_bytes = text.encode('ascii', errors='replace')[:20]
            for byte in text_bytes:
                self._bus.write_byte(self.address, byte)
            
            return {"success": True, "channel": channel, "text": text}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def write_lines(self, channel: int, lines: List[str]) -> Dict:
        """
        Write multiple lines to display.
        
        Args:
            channel: Display channel
            lines: List of lines (max 4 for typical OLED)
        
        Returns:
            Result dictionary
        """
        if channel not in self.displays:
            return {"success": False, "error": f"Invalid channel: {channel}"}
        
        state = self.displays[channel]
        
        # Update lines
        for i, line in enumerate(lines[:4]):
            if i == 0:
                state.line1 = line[:20]
            elif i == 1:
                state.line2 = line[:20]
            elif i == 2:
                state.line3 = line[:20]
            elif i == 3:
                state.line4 = line[:20]
        
        state.content = "\n".join(lines)
        state.last_update = time.time()
        
        if self.simulation:
            print(f"[DISPLAY {channel}]")
            for line in lines[:4]:
                print(f"  | {line[:20]:<20} |")
            return {"success": True, "channel": channel, "lines": lines[:4]}
        
        # Real implementation would send to display here
        return {"success": True, "channel": channel, "lines": lines[:4]}
    
    def clear_display(self, channel: int) -> Dict:
        """Clear display on specified channel"""
        if channel not in self.displays:
            return {"success": False, "error": f"Invalid channel: {channel}"}
        
        self.displays[channel] = DisplayState(channel=channel)
        
        if self.simulation:
            print(f"[DISPLAY {channel}] <cleared>")
        
        return {"success": True, "channel": channel, "action": "cleared"}
    
    def set_backlight(self, channel: int, enabled: bool) -> Dict:
        """Control display backlight"""
        if channel not in self.displays:
            return {"success": False, "error": f"Invalid channel: {channel}"}
        
        self.displays[channel].backlight = enabled
        
        return {"success": True, "channel": channel, "backlight": enabled}
    
    def get_display_state(self, channel: int) -> Dict:
        """Get current state of a display"""
        if channel not in self.displays:
            return {"error": f"Invalid channel: {channel}"}
        
        state = self.displays[channel]
        return {
            "channel": state.channel,
            "content": state.content,
            "lines": [state.line1, state.line2, state.line3, state.line4],
            "backlight": state.backlight,
            "last_update": state.last_update
        }
    
    def get_all_states(self) -> Dict:
        """Get states of all displays"""
        return {
            "displays": {
                ch: self.get_display_state(ch) for ch in self.displays
            },
            "simulation_mode": self.simulation
        }
    
    def cleanup(self):
        """Cleanup I2C resources"""
        if self._bus:
            self._bus.close()


class DisplayManager:
    """
    High-level display manager for SmartGrow.
    Provides easy methods to update displays with sensor data.
    """
    
    def __init__(self, pca: Optional[PCA9578AController] = None):
        self.pca = pca or PCA9578AController()
    
    def update_status_display(
        self,
        moisture: float,
        temperature: float,
        humidity: float,
        pump_active: bool,
        light_active: bool
    ) -> Dict:
        """Update main status display (channel 0)"""
        lines = [
            f"SmartGrow v2.0",
            f"M:{moisture:4.1f}% T:{temperature:4.1f}C",
            f"H:{humidity:4.1f}%",
            f"Pump:{'ON ' if pump_active else 'OFF'} UV:{'ON ' if light_active else 'OFF'}"
        ]
        return self.pca.write_lines(0, lines)
    
    def update_sensor_display(
        self,
        moisture: float,
        temperature: float,
        humidity: float,
        water_level: float
    ) -> Dict:
        """Update sensor data display (channel 1)"""
        lines = [
            f"== SENSORS ==",
            f"Soil: {moisture:5.1f}%",
            f"Temp: {temperature:5.1f}C",
            f"Tank: {water_level:5.1f}%"
        ]
        return self.pca.write_lines(1, lines)
    
    def show_alert(self, channel: int, title: str, message: str) -> Dict:
        """Show alert on display"""
        lines = [
            "!" * 20,
            title.center(20),
            message[:20].center(20),
            "!" * 20
        ]
        return self.pca.write_lines(channel, lines)
    
    def show_watering(self) -> Dict:
        """Show watering animation on display 0"""
        return self.pca.write_lines(0, [
            "~~ WATERING ~~",
            "    ||||",
            "    VVVV",
            "   [PLANT]"
        ])
    
    def show_idle(self) -> Dict:
        """Show idle screen"""
        from datetime import datetime
        now = datetime.now()
        return self.pca.write_lines(0, [
            "SmartGrow",
            now.strftime("%Y-%m-%d"),
            now.strftime("%H:%M:%S"),
            "Ready..."
        ])


# Singleton instances
_pca_instance: Optional[PCA9578AController] = None
_display_manager: Optional[DisplayManager] = None

def get_pca() -> PCA9578AController:
    """Get or create PCA9578A controller singleton"""
    global _pca_instance
    if _pca_instance is None:
        _pca_instance = PCA9578AController()
    return _pca_instance

def get_display_manager() -> DisplayManager:
    """Get or create display manager singleton"""
    global _display_manager
    if _display_manager is None:
        _display_manager = DisplayManager(get_pca())
    return _display_manager

def display0(text: str) -> Dict:
    """Write to display 0"""
    return get_pca().write_display(0, text)

def display1(text: str) -> Dict:
    """Write to display 1"""
    return get_pca().write_display(1, text)


# Standalone testing
if __name__ == "__main__":
    print("SmartGrow - PCA9578A Display Test")
    print("=" * 40)
    
    pca = PCA9578AController(simulation=True)
    dm = DisplayManager(pca)
    
    print("\nUpdating status display...")
    dm.update_status_display(
        moisture=45.2,
        temperature=24.5,
        humidity=65.0,
        pump_active=False,
        light_active=True
    )
    
    print("\nUpdating sensor display...")
    dm.update_sensor_display(
        moisture=45.2,
        temperature=24.5,
        humidity=65.0,
        water_level=78.0
    )
    
    time.sleep(1)
    
    print("\nShowing watering animation...")
    dm.show_watering()
    
    print(f"\nDisplay states: {pca.get_all_states()}")
