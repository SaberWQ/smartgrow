"""
SmartGrow - FastAPI Server
Main API server for Raspberry Pi greenhouse controller
"""

import os
import sys
import asyncio
import time
from datetime import datetime
from typing import Dict, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import SmartGrow modules
from sensors.moisture import SoilMoistureSensor, read_moisture
from actuators.pump import WaterPumpController
from actuators.uv_light import UVLightController
from displays.pca9578a import DisplayManager, PCA9578AController
from config.gpio_config import (
    PUMP_RELAY_PIN,
    UV_LIGHT_PIN,
    MOISTURE_SENSOR_PIN,
    PID_TARGET_MOISTURE
)


# Global instances
pump: Optional[WaterPumpController] = None
uv_light: Optional[UVLightController] = None
moisture_sensor: Optional[SoilMoistureSensor] = None
display_manager: Optional[DisplayManager] = None

# Sensor data cache
sensor_data = {
    "moisture": 0.0,
    "temperature": 25.0,
    "humidity": 60.0,
    "water_level": 100.0,
    "last_update": None
}


# Pydantic models
class WaterRequest(BaseModel):
    duration: float = 2.0

class LightSchedule(BaseModel):
    on_hour: int = 7
    off_hour: int = 22

class DisplayText(BaseModel):
    channel: int = 0
    text: str = ""
    lines: Optional[list] = None


# Startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup hardware"""
    global pump, uv_light, moisture_sensor, display_manager
    
    print("[SERVER] Starting SmartGrow...")
    
    # Initialize hardware (simulation mode if not on Pi)
    try:
        pump = WaterPumpController(relay_pin=PUMP_RELAY_PIN)
        uv_light = UVLightController(relay_pin=UV_LIGHT_PIN)
        moisture_sensor = SoilMoistureSensor(gpio_pin=MOISTURE_SENSOR_PIN)
        display_manager = DisplayManager()
        
        # Show startup on display
        display_manager.show_idle()
        
        print("[SERVER] Hardware initialized")
    except Exception as e:
        print(f"[SERVER] Hardware init error: {e}")
        print("[SERVER] Running in simulation mode")
    
    # Start background tasks
    asyncio.create_task(sensor_loop())
    asyncio.create_task(schedule_loop())
    
    yield
    
    # Cleanup
    print("[SERVER] Shutting down...")
    if pump:
        pump.cleanup()
    if uv_light:
        uv_light.cleanup()
    if moisture_sensor:
        moisture_sensor.cleanup()
    print("[SERVER] Cleanup complete")


# Create FastAPI app
app = FastAPI(
    title="SmartGrow API",
    description="AI-powered smart greenhouse control system",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Background tasks
async def sensor_loop():
    """Continuously read sensors"""
    global sensor_data
    
    while True:
        try:
            if moisture_sensor:
                reading = moisture_sensor.read()
                sensor_data["moisture"] = reading.percentage
            
            # Simulate temperature/humidity (replace with DHT22 reading)
            import random
            sensor_data["temperature"] = 22.0 + random.uniform(-2, 2)
            sensor_data["humidity"] = 60.0 + random.uniform(-5, 5)
            sensor_data["water_level"] = max(0, sensor_data.get("water_level", 100) - random.uniform(0, 0.1))
            sensor_data["last_update"] = datetime.now().isoformat()
            
            # Update display
            if display_manager:
                display_manager.update_sensor_display(
                    moisture=sensor_data["moisture"],
                    temperature=sensor_data["temperature"],
                    humidity=sensor_data["humidity"],
                    water_level=sensor_data["water_level"]
                )
            
        except Exception as e:
            print(f"[SENSOR LOOP] Error: {e}")
        
        await asyncio.sleep(5)

async def schedule_loop():
    """Check UV light schedule"""
    while True:
        try:
            if uv_light:
                uv_light.check_schedule()
        except Exception as e:
            print(f"[SCHEDULE LOOP] Error: {e}")
        
        await asyncio.sleep(60)


# API Routes

@app.get("/")
async def root():
    """API root"""
    return {
        "name": "SmartGrow API",
        "version": "2.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "pump_ready": pump is not None,
        "uv_ready": uv_light is not None,
        "moisture_ready": moisture_sensor is not None,
        "timestamp": datetime.now().isoformat()
    }


# Sensor endpoints

@app.get("/sensors")
async def get_sensors():
    """Get all sensor readings"""
    return {
        "moisture": round(sensor_data["moisture"], 1),
        "temperature": round(sensor_data["temperature"], 1),
        "humidity": round(sensor_data["humidity"], 1),
        "water_level": round(sensor_data["water_level"], 1),
        "last_update": sensor_data["last_update"],
        "thresholds": {
            "moisture_low": 30,
            "moisture_high": 70,
            "moisture_target": PID_TARGET_MOISTURE
        }
    }


@app.get("/sensors/moisture")
async def get_moisture():
    """Get soil moisture reading"""
    if moisture_sensor:
        return moisture_sensor.get_status()
    return {"moisture_percent": sensor_data["moisture"], "status": "simulated"}


# Pump endpoints

@app.post("/water")
async def water_plant(request: WaterRequest, background_tasks: BackgroundTasks):
    """Water the plant"""
    if not pump:
        raise HTTPException(status_code=503, detail="Pump not available")
    
    # Show watering on display
    if display_manager:
        display_manager.show_watering()
    
    result = pump.start(duration_seconds=request.duration)
    
    return result


@app.post("/water/stop")
async def stop_watering():
    """Emergency stop watering"""
    if not pump:
        raise HTTPException(status_code=503, detail="Pump not available")
    
    return pump.stop()


@app.get("/water/status")
async def get_pump_status():
    """Get pump status"""
    if not pump:
        return {"error": "Pump not available"}
    
    return pump.get_status()


# UV Light endpoints

@app.post("/light/on")
async def light_on():
    """Turn on UV light"""
    if not uv_light:
        raise HTTPException(status_code=503, detail="UV light not available")
    
    return uv_light.turn_on(manual=True)


@app.post("/light/off")
async def light_off():
    """Turn off UV light"""
    if not uv_light:
        raise HTTPException(status_code=503, detail="UV light not available")
    
    return uv_light.turn_off(manual=True)


@app.post("/light/toggle")
async def light_toggle():
    """Toggle UV light"""
    if not uv_light:
        raise HTTPException(status_code=503, detail="UV light not available")
    
    return uv_light.toggle()


@app.get("/light/status")
async def get_light_status():
    """Get UV light status"""
    if not uv_light:
        return {"error": "UV light not available"}
    
    return uv_light.get_status()


@app.post("/light/schedule")
async def set_light_schedule(schedule: LightSchedule):
    """Set UV light schedule"""
    if not uv_light:
        raise HTTPException(status_code=503, detail="UV light not available")
    
    return uv_light.set_schedule(schedule.on_hour, schedule.off_hour)


@app.post("/light/auto")
async def set_light_auto(enabled: bool = True):
    """Enable/disable auto mode"""
    if not uv_light:
        raise HTTPException(status_code=503, detail="UV light not available")
    
    return uv_light.set_auto_mode(enabled)


# Display endpoints

@app.post("/display/write")
async def write_display(request: DisplayText):
    """Write to display"""
    if not display_manager:
        raise HTTPException(status_code=503, detail="Display not available")
    
    if request.lines:
        return display_manager.pca.write_lines(request.channel, request.lines)
    else:
        return display_manager.pca.write_display(request.channel, request.text)


@app.get("/display/status")
async def get_display_status():
    """Get display status"""
    if not display_manager:
        return {"error": "Display not available"}
    
    return display_manager.pca.get_all_states()


# System endpoints

@app.get("/system/status")
async def get_system_status():
    """Get complete system status"""
    return {
        "sensors": sensor_data,
        "pump": pump.get_status() if pump else None,
        "uv_light": uv_light.get_status() if uv_light else None,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/system/reset")
async def reset_daily_stats():
    """Reset daily statistics"""
    results = {}
    
    if pump:
        pump.reset_daily_stats()
        results["pump"] = "reset"
    
    if uv_light:
        uv_light.reset_daily_stats()
        results["uv_light"] = "reset"
    
    return {"success": True, "results": results}


# Run server
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8000))
    
    print(f"""
    ╔═══════════════════════════════════════╗
    ║         SmartGrow Server v2.0         ║
    ║     AI-Powered Smart Greenhouse       ║
    ╠═══════════════════════════════════════╣
    ║  GPIO Configuration:                  ║
    ║    Pump Relay:  GPIO {PUMP_RELAY_PIN:<2}              ║
    ║    UV Light:    GPIO {UV_LIGHT_PIN:<2}              ║
    ║    Moisture:    GPIO {MOISTURE_SENSOR_PIN:<2}              ║
    ╠═══════════════════════════════════════╣
    ║  Starting server on port {port:<5}        ║
    ╚═══════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )
