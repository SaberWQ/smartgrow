"""
SmartGrow SQLite Database Models
================================

Database schema and operations for storing sensor data,
events, plant health, and game statistics.
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path
from contextlib import contextmanager
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Default database path
DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "smartgrow.db"


@dataclass
class SensorReading:
    """Sensor data reading."""
    id: Optional[int] = None
    moisture: float = 0.0
    temperature: float = 0.0
    humidity: float = 0.0
    water_level: float = 0.0
    timestamp: Optional[str] = None


@dataclass
class WateringEvent:
    """Watering event record."""
    id: Optional[int] = None
    duration: float = 0.0
    moisture_before: float = 0.0
    moisture_after: float = 0.0
    trigger: str = "manual"  # manual, auto, pid
    timestamp: Optional[str] = None


@dataclass
class LightEvent:
    """UV light event record."""
    id: Optional[int] = None
    action: str = "on"  # on, off
    brightness: int = 100
    trigger: str = "manual"
    timestamp: Optional[str] = None


@dataclass
class PlantHealthRecord:
    """Plant health analysis record."""
    id: Optional[int] = None
    health_score: int = 0
    leaf_color: str = ""
    leaf_condition: str = ""
    disease_detected: bool = False
    disease_name: Optional[str] = None
    growth_stage: str = ""
    water_stress: str = ""
    recommendations: str = ""  # JSON string
    timestamp: Optional[str] = None


@dataclass
class GameStats:
    """Game statistics record."""
    id: Optional[int] = None
    player_name: str = ""
    xp: int = 0
    level: int = 1
    gold: int = 0
    streak: int = 0
    achievements: str = ""  # JSON string
    timestamp: Optional[str] = None


class Database:
    """
    SQLite database manager for SmartGrow.
    
    Handles all database operations including:
    - Sensor data logging
    - Watering events
    - Light events
    - Plant health records
    - Game statistics
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database connection."""
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
        logger.info(f"Database initialized at {self.db_path}")
    
    @contextmanager
    def _get_connection(self):
        """Get database connection context manager."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_database(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Sensor data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sensor_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    moisture REAL NOT NULL,
                    temperature REAL NOT NULL,
                    humidity REAL NOT NULL,
                    water_level REAL NOT NULL,
                    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
                )
            """)
            
            # Watering events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS watering_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    duration REAL NOT NULL,
                    moisture_before REAL,
                    moisture_after REAL,
                    trigger TEXT NOT NULL DEFAULT 'manual',
                    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
                )
            """)
            
            # Light events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS light_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    brightness INTEGER DEFAULT 100,
                    trigger TEXT NOT NULL DEFAULT 'manual',
                    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
                )
            """)
            
            # Plant health table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS plant_health (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    health_score INTEGER NOT NULL,
                    leaf_color TEXT,
                    leaf_condition TEXT,
                    disease_detected INTEGER DEFAULT 0,
                    disease_name TEXT,
                    growth_stage TEXT,
                    water_stress TEXT,
                    recommendations TEXT,
                    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
                )
            """)
            
            # Game stats table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS game_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_name TEXT NOT NULL,
                    xp INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    gold INTEGER DEFAULT 0,
                    streak INTEGER DEFAULT 0,
                    achievements TEXT,
                    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
                )
            """)
            
            # Create indexes for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sensor_timestamp 
                ON sensor_data(timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_watering_timestamp 
                ON watering_events(timestamp)
            """)
            
            logger.info("Database schema initialized")
    
    # ==================== Sensor Data ====================
    
    def log_sensor_data(
        self,
        moisture: float,
        temperature: float,
        humidity: float,
        water_level: float
    ) -> int:
        """Log sensor reading to database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sensor_data (moisture, temperature, humidity, water_level)
                VALUES (?, ?, ?, ?)
            """, (moisture, temperature, humidity, water_level))
            return cursor.lastrowid
    
    def get_latest_sensor_data(self) -> Optional[SensorReading]:
        """Get most recent sensor reading."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                return SensorReading(
                    id=row['id'],
                    moisture=row['moisture'],
                    temperature=row['temperature'],
                    humidity=row['humidity'],
                    water_level=row['water_level'],
                    timestamp=row['timestamp']
                )
            return None
    
    def get_sensor_history(
        self,
        hours: int = 24,
        limit: int = 1000
    ) -> List[SensorReading]:
        """Get sensor data history."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
            cursor.execute("""
                SELECT * FROM sensor_data 
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (cutoff, limit))
            
            return [
                SensorReading(
                    id=row['id'],
                    moisture=row['moisture'],
                    temperature=row['temperature'],
                    humidity=row['humidity'],
                    water_level=row['water_level'],
                    timestamp=row['timestamp']
                )
                for row in cursor.fetchall()
            ]
    
    def get_sensor_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get sensor statistics for time period."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
            cursor.execute("""
                SELECT 
                    AVG(moisture) as avg_moisture,
                    MIN(moisture) as min_moisture,
                    MAX(moisture) as max_moisture,
                    AVG(temperature) as avg_temperature,
                    MIN(temperature) as min_temperature,
                    MAX(temperature) as max_temperature,
                    AVG(humidity) as avg_humidity,
                    AVG(water_level) as avg_water_level,
                    COUNT(*) as samples
                FROM sensor_data
                WHERE timestamp >= ?
            """, (cutoff,))
            
            row = cursor.fetchone()
            if row and row['samples'] > 0:
                return {
                    'moisture': {
                        'avg': round(row['avg_moisture'], 1),
                        'min': round(row['min_moisture'], 1),
                        'max': round(row['max_moisture'], 1)
                    },
                    'temperature': {
                        'avg': round(row['avg_temperature'], 1),
                        'min': round(row['min_temperature'], 1),
                        'max': round(row['max_temperature'], 1)
                    },
                    'humidity': {
                        'avg': round(row['avg_humidity'], 1)
                    },
                    'water_level': {
                        'avg': round(row['avg_water_level'], 1)
                    },
                    'samples': row['samples'],
                    'period_hours': hours
                }
            return {'samples': 0}
    
    # ==================== Watering Events ====================
    
    def log_watering_event(
        self,
        duration: float,
        moisture_before: float,
        moisture_after: float = None,
        trigger: str = "manual"
    ) -> int:
        """Log watering event."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO watering_events 
                (duration, moisture_before, moisture_after, trigger)
                VALUES (?, ?, ?, ?)
            """, (duration, moisture_before, moisture_after, trigger))
            return cursor.lastrowid
    
    def get_watering_history(self, days: int = 7) -> List[WateringEvent]:
        """Get watering event history."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            cursor.execute("""
                SELECT * FROM watering_events 
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            """, (cutoff,))
            
            return [
                WateringEvent(
                    id=row['id'],
                    duration=row['duration'],
                    moisture_before=row['moisture_before'],
                    moisture_after=row['moisture_after'],
                    trigger=row['trigger'],
                    timestamp=row['timestamp']
                )
                for row in cursor.fetchall()
            ]
    
    def get_total_water_used(self, days: int = 7) -> float:
        """Get total watering duration in seconds."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            cursor.execute("""
                SELECT SUM(duration) as total
                FROM watering_events
                WHERE timestamp >= ?
            """, (cutoff,))
            row = cursor.fetchone()
            return row['total'] or 0.0
    
    # ==================== Light Events ====================
    
    def log_light_event(
        self,
        action: str,
        brightness: int = 100,
        trigger: str = "manual"
    ) -> int:
        """Log light event."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO light_events (action, brightness, trigger)
                VALUES (?, ?, ?)
            """, (action, brightness, trigger))
            return cursor.lastrowid
    
    def get_light_history(self, days: int = 7) -> List[LightEvent]:
        """Get light event history."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            cursor.execute("""
                SELECT * FROM light_events 
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            """, (cutoff,))
            
            return [
                LightEvent(
                    id=row['id'],
                    action=row['action'],
                    brightness=row['brightness'],
                    trigger=row['trigger'],
                    timestamp=row['timestamp']
                )
                for row in cursor.fetchall()
            ]
    
    # ==================== Plant Health ====================
    
    def log_plant_health(self, analysis: Dict[str, Any]) -> int:
        """Log plant health analysis."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO plant_health 
                (health_score, leaf_color, leaf_condition, disease_detected,
                 disease_name, growth_stage, water_stress, recommendations)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                analysis.get('health_score', 0),
                analysis.get('leaf_color', ''),
                analysis.get('leaf_condition', ''),
                1 if analysis.get('disease_detected') else 0,
                analysis.get('disease_name'),
                analysis.get('growth_stage', ''),
                analysis.get('water_stress', ''),
                json.dumps(analysis.get('recommendations', []))
            ))
            return cursor.lastrowid
    
    def get_plant_health_history(self, limit: int = 30) -> List[PlantHealthRecord]:
        """Get plant health history."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM plant_health 
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            return [
                PlantHealthRecord(
                    id=row['id'],
                    health_score=row['health_score'],
                    leaf_color=row['leaf_color'],
                    leaf_condition=row['leaf_condition'],
                    disease_detected=bool(row['disease_detected']),
                    disease_name=row['disease_name'],
                    growth_stage=row['growth_stage'],
                    water_stress=row['water_stress'],
                    recommendations=row['recommendations'],
                    timestamp=row['timestamp']
                )
                for row in cursor.fetchall()
            ]
    
    # ==================== Game Stats ====================
    
    def save_game_stats(self, stats: Dict[str, Any]) -> int:
        """Save game statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO game_stats 
                (player_name, xp, level, gold, streak, achievements)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                stats.get('player_name', 'Player'),
                stats.get('xp', 0),
                stats.get('level', 1),
                stats.get('gold', 0),
                stats.get('streak', 0),
                json.dumps(stats.get('achievements', []))
            ))
            return cursor.lastrowid
    
    def get_latest_game_stats(self) -> Optional[GameStats]:
        """Get latest game statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM game_stats ORDER BY timestamp DESC LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                return GameStats(
                    id=row['id'],
                    player_name=row['player_name'],
                    xp=row['xp'],
                    level=row['level'],
                    gold=row['gold'],
                    streak=row['streak'],
                    achievements=row['achievements'],
                    timestamp=row['timestamp']
                )
            return None
    
    # ==================== Cleanup ====================
    
    def cleanup_old_data(self, days: int = 30):
        """Remove data older than specified days."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            
            cursor.execute("DELETE FROM sensor_data WHERE timestamp < ?", (cutoff,))
            deleted_sensors = cursor.rowcount
            
            cursor.execute("DELETE FROM watering_events WHERE timestamp < ?", (cutoff,))
            deleted_watering = cursor.rowcount
            
            cursor.execute("DELETE FROM light_events WHERE timestamp < ?", (cutoff,))
            deleted_light = cursor.rowcount
            
            logger.info(f"Cleanup: removed {deleted_sensors} sensor, "
                       f"{deleted_watering} watering, {deleted_light} light records")
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get database table statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            stats = {}
            
            for table in ['sensor_data', 'watering_events', 'light_events', 
                         'plant_health', 'game_stats']:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cursor.fetchone()[0]
            
            return stats


# Singleton instance
_database: Optional[Database] = None


def get_database(db_path: str = None) -> Database:
    """Get or create global database instance."""
    global _database
    
    if _database is None:
        _database = Database(db_path)
    
    return _database
