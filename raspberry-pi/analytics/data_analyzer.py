"""
SmartGrow - Data Analytics Module
Sensor data analysis, predictions, and anomaly detection
Infomatrix Ukraine 2026
"""

import time
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats
from scipy.signal import savgol_filter


class DataAnalyzer:
    """
    Comprehensive data analytics for SmartGrow sensor data.
    
    Features:
    - Trend analysis
    - Anomaly detection
    - Moisture prediction
    - Optimal condition recommendations
    - Statistical summaries
    """
    
    def __init__(self, database_path: str = './data/smartgrow.db'):
        """
        Initialize the data analyzer.
        
        Args:
            database_path: Path to SQLite database
        """
        self.database_path = database_path
        self._init_database()
        
        # Optimal ranges for plant health
        self.optimal_ranges = {
            'moisture': (45, 65),
            'temperature': (20, 28),
            'humidity': (50, 70),
            'water_level': (30, 100)
        }
        
        # Weights for health score calculation
        self.health_weights = {
            'moisture': 0.35,
            'temperature': 0.25,
            'humidity': 0.20,
            'water_level': 0.20
        }
    
    def _init_database(self):
        """Initialize SQLite database with required tables."""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Sensor readings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                moisture REAL,
                temperature REAL,
                humidity REAL,
                water_level REAL,
                pump_active INTEGER,
                light_active INTEGER
            )
        ''')
        
        # Events log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                event_type TEXT NOT NULL,
                description TEXT,
                value REAL
            )
        ''')
        
        # Daily summaries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE NOT NULL,
                avg_moisture REAL,
                avg_temperature REAL,
                avg_humidity REAL,
                watering_count INTEGER,
                light_hours REAL,
                health_score REAL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_sensor_reading(
        self,
        moisture: float,
        temperature: float,
        humidity: float,
        water_level: float,
        pump_active: bool = False,
        light_active: bool = False
    ):
        """
        Log a sensor reading to database.
        
        Args:
            moisture: Soil moisture percentage
            temperature: Temperature in Celsius
            humidity: Relative humidity percentage
            water_level: Water tank level percentage
            pump_active: Whether pump is running
            light_active: Whether UV light is on
        """
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO sensor_readings 
            (timestamp, moisture, temperature, humidity, water_level, pump_active, light_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (time.time(), moisture, temperature, humidity, water_level, 
              int(pump_active), int(light_active)))
        
        conn.commit()
        conn.close()
    
    def log_event(self, event_type: str, description: str, value: Optional[float] = None):
        """
        Log an event to database.
        
        Args:
            event_type: Type of event (watering, light_on, light_off, alert, etc.)
            description: Event description
            value: Optional numeric value associated with event
        """
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO events (timestamp, event_type, description, value)
            VALUES (?, ?, ?, ?)
        ''', (time.time(), event_type, description, value))
        
        conn.commit()
        conn.close()
    
    def get_recent_readings(self, hours: int = 24) -> pd.DataFrame:
        """
        Get recent sensor readings.
        
        Args:
            hours: Number of hours of data to retrieve
        
        Returns:
            Pandas DataFrame with sensor readings
        """
        conn = sqlite3.connect(self.database_path)
        
        cutoff = time.time() - (hours * 3600)
        
        df = pd.read_sql_query('''
            SELECT * FROM sensor_readings
            WHERE timestamp > ?
            ORDER BY timestamp ASC
        ''', conn, params=(cutoff,))
        
        conn.close()
        
        if not df.empty:
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        
        return df
    
    def calculate_statistics(self, hours: int = 24) -> Dict:
        """
        Calculate comprehensive statistics for sensor data.
        
        Args:
            hours: Time window for analysis
        
        Returns:
            Dictionary with statistical summaries
        """
        df = self.get_recent_readings(hours)
        
        if df.empty:
            return {'error': 'No data available'}
        
        sensors = ['moisture', 'temperature', 'humidity', 'water_level']
        stats_dict = {}
        
        for sensor in sensors:
            if sensor in df.columns and not df[sensor].isna().all():
                data = df[sensor].dropna()
                
                stats_dict[sensor] = {
                    'current': round(data.iloc[-1], 1) if len(data) > 0 else None,
                    'mean': round(data.mean(), 1),
                    'median': round(data.median(), 1),
                    'std': round(data.std(), 2),
                    'min': round(data.min(), 1),
                    'max': round(data.max(), 1),
                    'range': round(data.max() - data.min(), 1),
                    'samples': len(data)
                }
        
        # Add time-based stats
        stats_dict['analysis_period'] = {
            'hours': hours,
            'start_time': df['datetime'].iloc[0].isoformat() if not df.empty else None,
            'end_time': df['datetime'].iloc[-1].isoformat() if not df.empty else None,
            'total_samples': len(df)
        }
        
        return stats_dict
    
    def detect_anomalies(self, hours: int = 24, std_threshold: float = 2.5) -> List[Dict]:
        """
        Detect anomalies in sensor data using Z-score method.
        
        Args:
            hours: Time window for analysis
            std_threshold: Number of standard deviations for anomaly
        
        Returns:
            List of detected anomalies
        """
        df = self.get_recent_readings(hours)
        
        if df.empty or len(df) < 10:
            return []
        
        anomalies = []
        sensors = ['moisture', 'temperature', 'humidity', 'water_level']
        
        for sensor in sensors:
            if sensor not in df.columns or df[sensor].isna().all():
                continue
            
            data = df[sensor].dropna()
            
            if len(data) < 10:
                continue
            
            # Calculate Z-scores
            z_scores = np.abs(stats.zscore(data))
            
            # Find anomalies
            anomaly_indices = np.where(z_scores > std_threshold)[0]
            
            for idx in anomaly_indices:
                anomalies.append({
                    'sensor': sensor,
                    'timestamp': float(df.iloc[idx]['timestamp']),
                    'datetime': df.iloc[idx]['datetime'].isoformat(),
                    'value': float(data.iloc[idx]),
                    'z_score': float(z_scores[idx]),
                    'mean': float(data.mean()),
                    'std': float(data.std())
                })
        
        return sorted(anomalies, key=lambda x: x['z_score'], reverse=True)
    
    def analyze_trends(self, hours: int = 6) -> Dict:
        """
        Analyze trends in sensor data.
        
        Args:
            hours: Time window for trend analysis
        
        Returns:
            Dictionary with trend information for each sensor
        """
        df = self.get_recent_readings(hours)
        
        if df.empty or len(df) < 5:
            return {'error': 'Insufficient data for trend analysis'}
        
        trends = {}
        sensors = ['moisture', 'temperature', 'humidity', 'water_level']
        
        for sensor in sensors:
            if sensor not in df.columns or df[sensor].isna().all():
                continue
            
            data = df[sensor].dropna()
            
            if len(data) < 5:
                continue
            
            # Normalize timestamps for regression
            x = np.arange(len(data))
            y = data.values
            
            # Linear regression
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            
            # Convert slope to units per hour
            time_span_hours = (df['timestamp'].iloc[-1] - df['timestamp'].iloc[0]) / 3600
            if time_span_hours > 0:
                slope_per_hour = slope * len(data) / time_span_hours
            else:
                slope_per_hour = 0
            
            # Determine trend direction
            if abs(slope_per_hour) < 0.5:
                direction = 'stable'
            elif slope_per_hour > 0:
                direction = 'rising'
            else:
                direction = 'falling'
            
            # Predict future values
            hours_to_predict = 3
            samples_per_hour = len(data) / time_span_hours if time_span_hours > 0 else 6
            future_samples = int(samples_per_hour * hours_to_predict)
            
            predicted_value = intercept + slope * (len(data) + future_samples)
            
            trends[sensor] = {
                'direction': direction,
                'slope_per_hour': round(slope_per_hour, 3),
                'r_squared': round(r_value ** 2, 3),
                'current_value': round(y[-1], 1),
                'predicted_3h': round(predicted_value, 1),
                'confidence': 'high' if r_value ** 2 > 0.7 else ('medium' if r_value ** 2 > 0.4 else 'low')
            }
        
        return trends
    
    def predict_watering_need(self) -> Dict:
        """
        Predict when watering will be needed based on moisture trends.
        
        Returns:
            Dictionary with watering prediction
        """
        trends = self.analyze_trends(hours=6)
        
        if 'moisture' not in trends or 'error' in trends:
            return {'predicted': False, 'reason': 'Insufficient data'}
        
        moisture_trend = trends['moisture']
        current = moisture_trend['current_value']
        slope = moisture_trend['slope_per_hour']
        
        # Target moisture threshold
        threshold = 35
        
        if current <= threshold:
            return {
                'needs_watering_now': True,
                'current_moisture': current,
                'threshold': threshold,
                'urgency': 'immediate'
            }
        
        if slope >= 0:
            return {
                'needs_watering_now': False,
                'current_moisture': current,
                'threshold': threshold,
                'hours_until_needed': None,
                'reason': 'Moisture is stable or rising'
            }
        
        # Calculate hours until threshold
        hours_until_threshold = (current - threshold) / abs(slope)
        
        if hours_until_threshold <= 0:
            hours_until_threshold = 0.1
        
        return {
            'needs_watering_now': False,
            'current_moisture': current,
            'threshold': threshold,
            'hours_until_needed': round(hours_until_threshold, 1),
            'predicted_time': (datetime.now() + timedelta(hours=hours_until_threshold)).isoformat(),
            'urgency': 'soon' if hours_until_threshold < 2 else ('scheduled' if hours_until_threshold < 6 else 'not_urgent'),
            'confidence': moisture_trend['confidence']
        }
    
    def calculate_health_score(self, sensors: Dict) -> Dict:
        """
        Calculate overall plant health score based on current conditions.
        
        Args:
            sensors: Dictionary with current sensor values
        
        Returns:
            Dictionary with health score and breakdown
        """
        scores = {}
        total_score = 0
        
        for sensor, (min_opt, max_opt) in self.optimal_ranges.items():
            if sensor not in sensors or sensors[sensor] is None:
                continue
            
            value = sensors[sensor]
            weight = self.health_weights.get(sensor, 0.25)
            
            # Calculate score (100 if optimal, decreases outside range)
            if min_opt <= value <= max_opt:
                score = 100
            else:
                if value < min_opt:
                    deviation = (min_opt - value) / min_opt
                else:
                    deviation = (value - max_opt) / max_opt
                
                score = max(0, 100 - deviation * 100)
            
            scores[sensor] = {
                'value': value,
                'optimal_range': (min_opt, max_opt),
                'score': round(score, 1),
                'status': 'optimal' if score >= 80 else ('acceptable' if score >= 50 else 'poor')
            }
            
            total_score += score * weight
        
        return {
            'overall_score': round(total_score, 1),
            'grade': self._score_to_grade(total_score),
            'breakdown': scores,
            'timestamp': time.time()
        }
    
    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    def get_recommendations(self, sensors: Dict) -> List[Dict]:
        """
        Generate actionable recommendations based on current conditions.
        
        Args:
            sensors: Current sensor values
        
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Moisture recommendations
        moisture = sensors.get('moisture')
        if moisture is not None:
            if moisture < 35:
                recommendations.append({
                    'priority': 'high',
                    'category': 'watering',
                    'title': 'Water Needed',
                    'message': f'Soil moisture is critically low ({moisture}%). Water your plant immediately.',
                    'action': 'water_now'
                })
            elif moisture < 45:
                recommendations.append({
                    'priority': 'medium',
                    'category': 'watering',
                    'title': 'Schedule Watering',
                    'message': f'Soil moisture is below optimal ({moisture}%). Consider watering soon.',
                    'action': 'schedule_water'
                })
            elif moisture > 80:
                recommendations.append({
                    'priority': 'medium',
                    'category': 'watering',
                    'title': 'Reduce Watering',
                    'message': f'Soil is very wet ({moisture}%). Reduce watering frequency to prevent root rot.',
                    'action': 'reduce_water'
                })
        
        # Temperature recommendations
        temp = sensors.get('temperature')
        if temp is not None:
            if temp < 15:
                recommendations.append({
                    'priority': 'high',
                    'category': 'environment',
                    'title': 'Temperature Too Low',
                    'message': f'Temperature is {temp}°C. Move plant to warmer location or increase heating.',
                    'action': 'increase_temp'
                })
            elif temp > 32:
                recommendations.append({
                    'priority': 'high',
                    'category': 'environment',
                    'title': 'Temperature Too High',
                    'message': f'Temperature is {temp}°C. Improve ventilation or provide shade.',
                    'action': 'decrease_temp'
                })
        
        # Water tank recommendations
        water_level = sensors.get('water_level')
        if water_level is not None:
            if water_level < 15:
                recommendations.append({
                    'priority': 'high',
                    'category': 'maintenance',
                    'title': 'Refill Water Tank',
                    'message': f'Water tank is nearly empty ({water_level}%). Refill immediately.',
                    'action': 'refill_tank'
                })
            elif water_level < 30:
                recommendations.append({
                    'priority': 'medium',
                    'category': 'maintenance',
                    'title': 'Low Water Tank',
                    'message': f'Water tank is low ({water_level}%). Consider refilling soon.',
                    'action': 'refill_tank'
                })
        
        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 3))
        
        return recommendations
    
    def generate_daily_summary(self) -> Dict:
        """
        Generate daily summary report.
        
        Returns:
            Dictionary with daily summary
        """
        df = self.get_recent_readings(hours=24)
        
        if df.empty:
            return {'error': 'No data available for summary'}
        
        # Calculate averages
        summary = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'avg_moisture': round(df['moisture'].mean(), 1) if 'moisture' in df else None,
            'avg_temperature': round(df['temperature'].mean(), 1) if 'temperature' in df else None,
            'avg_humidity': round(df['humidity'].mean(), 1) if 'humidity' in df else None,
            'readings_count': len(df)
        }
        
        # Count watering events
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cutoff = time.time() - 86400
        cursor.execute('''
            SELECT COUNT(*) FROM events 
            WHERE event_type = 'watering' AND timestamp > ?
        ''', (cutoff,))
        summary['watering_count'] = cursor.fetchone()[0]
        
        # Calculate light hours
        if 'light_active' in df:
            light_samples = df['light_active'].sum()
            time_between_samples = 86400 / len(df) if len(df) > 0 else 60
            summary['light_hours'] = round(light_samples * time_between_samples / 3600, 1)
        else:
            summary['light_hours'] = None
        
        conn.close()
        
        return summary
    
    def get_hourly_averages(self, hours: int = 24) -> Dict:
        """
        Get hourly averages for charting.
        
        Args:
            hours: Number of hours of data
        
        Returns:
            Dictionary with hourly data
        """
        df = self.get_recent_readings(hours)
        
        if df.empty:
            return {'error': 'No data available'}
        
        # Group by hour
        df['hour'] = df['datetime'].dt.floor('H')
        
        hourly = df.groupby('hour').agg({
            'moisture': 'mean',
            'temperature': 'mean',
            'humidity': 'mean',
            'water_level': 'mean'
        }).reset_index()
        
        return {
            'hours': [h.strftime('%H:%M') for h in hourly['hour']],
            'moisture': [round(v, 1) if pd.notna(v) else None for v in hourly['moisture']],
            'temperature': [round(v, 1) if pd.notna(v) else None for v in hourly['temperature']],
            'humidity': [round(v, 1) if pd.notna(v) else None for v in hourly['humidity']],
            'water_level': [round(v, 1) if pd.notna(v) else None for v in hourly['water_level']]
        }


# Standalone testing
if __name__ == "__main__":
    print("SmartGrow - Data Analytics Module Test")
    print("=" * 45)
    
    analyzer = DataAnalyzer('./data/test_smartgrow.db')
    
    # Generate test data
    print("Generating test data...")
    import random
    
    base_moisture = 50
    base_temp = 24
    base_humidity = 60
    base_water = 70
    
    for i in range(100):
        # Simulate gradual changes
        moisture = base_moisture - i * 0.15 + random.gauss(0, 2)
        temp = base_temp + random.gauss(0, 1)
        humidity = base_humidity + random.gauss(0, 3)
        water = base_water - i * 0.05 + random.gauss(0, 1)
        
        analyzer.log_sensor_reading(
            moisture=max(0, min(100, moisture)),
            temperature=max(10, min(40, temp)),
            humidity=max(20, min(95, humidity)),
            water_level=max(0, min(100, water))
        )
        time.sleep(0.01)
    
    print("\nStatistics:")
    stats = analyzer.calculate_statistics(hours=24)
    for sensor, data in stats.items():
        if isinstance(data, dict) and 'mean' in data:
            print(f"  {sensor}: mean={data['mean']}, range={data['min']}-{data['max']}")
    
    print("\nTrends:")
    trends = analyzer.analyze_trends()
    for sensor, data in trends.items():
        if isinstance(data, dict) and 'direction' in data:
            print(f"  {sensor}: {data['direction']} ({data['slope_per_hour']}/h)")
    
    print("\nWatering Prediction:")
    prediction = analyzer.predict_watering_need()
    print(f"  {prediction}")
    
    print("\nHealth Score:")
    health = analyzer.calculate_health_score({
        'moisture': 45,
        'temperature': 24,
        'humidity': 60,
        'water_level': 65
    })
    print(f"  Overall: {health['overall_score']} ({health['grade']})")
    
    print("\nRecommendations:")
    recs = analyzer.get_recommendations({
        'moisture': 32,
        'temperature': 24,
        'humidity': 60,
        'water_level': 20
    })
    for rec in recs:
        print(f"  [{rec['priority']}] {rec['title']}: {rec['message']}")
    
    print("\nTest complete!")
