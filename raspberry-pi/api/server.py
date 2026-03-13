"""
SmartGrow - Flask API Server
REST API and WebSocket server for web application communication
Infomatrix Ukraine 2026
"""

import time
import json
import threading
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from typing import Dict, Optional
import yaml


class SmartGrowAPI:
    """
    Flask-based API server for SmartGrow.
    
    Provides:
    - REST endpoints for sensor data and controls
    - WebSocket for real-time updates
    - Event broadcasting
    """
    
    def __init__(
        self,
        greenhouse_controller,
        config_path: str = './config.yaml',
        host: str = '0.0.0.0',
        port: int = 5000
    ):
        """
        Initialize the API server.
        
        Args:
            greenhouse_controller: Reference to GreenhouseController instance
            config_path: Path to configuration file
            host: Server host address
            port: Server port
        """
        self.controller = greenhouse_controller
        self.host = host
        self.port = port
        
        # Load config
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize Flask app
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'smartgrow-secret-key-2026'
        
        # Enable CORS for web app
        CORS(self.app, origins=['*'])
        
        # Initialize SocketIO
        self.socketio = SocketIO(
            self.app,
            cors_allowed_origins='*',
            async_mode='threading'
        )
        
        # Register routes
        self._register_routes()
        self._register_socketio_events()
        
        # Background task for sensor broadcasting
        self._broadcast_thread = None
        self._running = False
    
    def _register_routes(self):
        """Register REST API routes."""
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Health check endpoint."""
            return jsonify({
                'status': 'healthy',
                'service': 'SmartGrow API',
                'version': '1.0.0',
                'timestamp': time.time()
            })
        
        @self.app.route('/api/sensors', methods=['GET'])
        def get_sensors():
            """Get current sensor readings."""
            try:
                data = self.controller.get_all_sensor_data()
                return jsonify({
                    'success': True,
                    'data': data,
                    'timestamp': time.time()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/sensors/history', methods=['GET'])
        def get_sensor_history():
            """Get sensor history data."""
            hours = request.args.get('hours', 24, type=int)
            
            try:
                hourly = self.controller.analyzer.get_hourly_averages(hours)
                return jsonify({
                    'success': True,
                    'data': hourly,
                    'hours': hours
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/water', methods=['POST'])
        def water_plant():
            """Trigger watering."""
            try:
                data = request.get_json() or {}
                duration = data.get('duration', 5)
                
                result = self.controller.water_plant(duration_seconds=duration)
                
                # Broadcast event
                self.socketio.emit('event', {
                    'type': 'watering',
                    'data': result,
                    'timestamp': time.time()
                })
                
                return jsonify({
                    'success': result.get('success', False),
                    'data': result
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/water/auto', methods=['POST'])
        def toggle_auto_water():
            """Toggle auto-watering mode."""
            try:
                data = request.get_json() or {}
                enabled = data.get('enabled', True)
                
                self.controller.set_auto_watering(enabled)
                
                return jsonify({
                    'success': True,
                    'auto_watering': enabled
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/light', methods=['POST'])
        def toggle_light():
            """Toggle UV grow light."""
            try:
                data = request.get_json() or {}
                state = data.get('state')  # 'on', 'off', or 'toggle'
                
                if state == 'on':
                    result = self.controller.uv_light.turn_on(manual=True)
                elif state == 'off':
                    result = self.controller.uv_light.turn_off(manual=True)
                else:
                    result = self.controller.uv_light.toggle(manual=True)
                
                # Broadcast event
                self.socketio.emit('event', {
                    'type': 'light',
                    'data': result,
                    'timestamp': time.time()
                })
                
                return jsonify({
                    'success': result.get('success', False),
                    'data': result
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/light/auto', methods=['POST'])
        def toggle_auto_light():
            """Toggle auto-lighting mode."""
            try:
                data = request.get_json() or {}
                enabled = data.get('enabled', True)
                
                self.controller.uv_light.set_auto_mode(enabled)
                
                return jsonify({
                    'success': True,
                    'auto_light': enabled
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/light/schedule', methods=['POST'])
        def set_light_schedule():
            """Set light schedule."""
            try:
                data = request.get_json() or {}
                start_hour = data.get('start_hour', 7)
                end_hour = data.get('end_hour', 22)
                
                result = self.controller.uv_light.set_schedule(start_hour, end_hour)
                
                return jsonify({
                    'success': result.get('success', False),
                    'data': result
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/status', methods=['GET'])
        def get_status():
            """Get full system status."""
            try:
                status = {
                    'sensors': self.controller.get_all_sensor_data(),
                    'pump': self.controller.pump.get_status(),
                    'light': self.controller.uv_light.get_status(),
                    'health': self.controller.get_plant_health(),
                    'timestamp': time.time()
                }
                
                return jsonify({
                    'success': True,
                    'data': status
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/analytics/stats', methods=['GET'])
        def get_analytics():
            """Get analytics and statistics."""
            hours = request.args.get('hours', 24, type=int)
            
            try:
                stats = self.controller.analyzer.calculate_statistics(hours)
                trends = self.controller.analyzer.analyze_trends(hours=6)
                
                return jsonify({
                    'success': True,
                    'statistics': stats,
                    'trends': trends
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/analytics/predictions', methods=['GET'])
        def get_predictions():
            """Get watering predictions."""
            try:
                prediction = self.controller.analyzer.predict_watering_need()
                
                return jsonify({
                    'success': True,
                    'data': prediction
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/analytics/anomalies', methods=['GET'])
        def get_anomalies():
            """Get detected anomalies."""
            hours = request.args.get('hours', 24, type=int)
            
            try:
                anomalies = self.controller.analyzer.detect_anomalies(hours)
                
                return jsonify({
                    'success': True,
                    'data': anomalies
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/recommendations', methods=['GET'])
        def get_recommendations():
            """Get AI recommendations."""
            try:
                sensors = self.controller.get_all_sensor_data()
                recommendations = self.controller.analyzer.get_recommendations(sensors)
                
                return jsonify({
                    'success': True,
                    'data': recommendations
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/game/stats', methods=['GET'])
        def get_game_stats():
            """Get game statistics."""
            try:
                stats = self.controller.get_game_stats()
                
                return jsonify({
                    'success': True,
                    'data': stats
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/events', methods=['GET'])
        def get_events():
            """Get recent events."""
            limit = request.args.get('limit', 50, type=int)
            
            try:
                events = self.controller.get_recent_events(limit)
                
                return jsonify({
                    'success': True,
                    'data': events
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
    
    def _register_socketio_events(self):
        """Register WebSocket event handlers."""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection."""
            print(f"Client connected: {request.sid}")
            
            # Send current state
            try:
                status = {
                    'sensors': self.controller.get_all_sensor_data(),
                    'pump': self.controller.pump.get_status(),
                    'light': self.controller.uv_light.get_status(),
                }
                emit('status', status)
            except Exception as e:
                emit('error', {'message': str(e)})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection."""
            print(f"Client disconnected: {request.sid}")
        
        @self.socketio.on('request_sensors')
        def handle_sensor_request():
            """Handle sensor data request."""
            try:
                data = self.controller.get_all_sensor_data()
                emit('sensors', data)
            except Exception as e:
                emit('error', {'message': str(e)})
        
        @self.socketio.on('command')
        def handle_command(data):
            """Handle command from client."""
            command = data.get('command')
            params = data.get('params', {})
            
            try:
                if command == 'water':
                    result = self.controller.water_plant(**params)
                elif command == 'light_on':
                    result = self.controller.uv_light.turn_on(manual=True)
                elif command == 'light_off':
                    result = self.controller.uv_light.turn_off(manual=True)
                elif command == 'light_toggle':
                    result = self.controller.uv_light.toggle(manual=True)
                else:
                    result = {'success': False, 'error': 'Unknown command'}
                
                emit('command_result', {
                    'command': command,
                    'result': result
                })
                
                # Broadcast to all clients
                self.socketio.emit('event', {
                    'type': command,
                    'data': result,
                    'timestamp': time.time()
                })
                
            except Exception as e:
                emit('error', {'message': str(e)})
    
    def _broadcast_sensors(self):
        """Background task to broadcast sensor data."""
        while self._running:
            try:
                data = self.controller.get_all_sensor_data()
                self.socketio.emit('sensors', data)
            except Exception as e:
                print(f"Broadcast error: {e}")
            
            time.sleep(5)  # Broadcast every 5 seconds
    
    def broadcast_event(self, event_type: str, data: Dict):
        """
        Broadcast an event to all connected clients.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        self.socketio.emit('event', {
            'type': event_type,
            'data': data,
            'timestamp': time.time()
        })
    
    def start(self, debug: bool = False):
        """
        Start the API server.
        
        Args:
            debug: Enable debug mode
        """
        self._running = True
        
        # Start sensor broadcast thread
        self._broadcast_thread = threading.Thread(
            target=self._broadcast_sensors,
            daemon=True
        )
        self._broadcast_thread.start()
        
        print(f"SmartGrow API Server starting on {self.host}:{self.port}")
        
        # Run Flask with SocketIO
        self.socketio.run(
            self.app,
            host=self.host,
            port=self.port,
            debug=debug,
            use_reloader=False
        )
    
    def stop(self):
        """Stop the API server."""
        self._running = False
        print("SmartGrow API Server stopped")


# Standalone testing (mock controller)
if __name__ == "__main__":
    print("SmartGrow - API Server Test")
    print("=" * 35)
    
    # Mock controller for testing
    class MockController:
        def get_all_sensor_data(self):
            return {
                'moisture': 45,
                'temperature': 24,
                'humidity': 60,
                'water_level': 75
            }
        
        def water_plant(self, **kwargs):
            return {'success': True, 'message': 'Mock watering'}
        
        def get_plant_health(self):
            return {'score': 85, 'grade': 'B'}
        
        def get_game_stats(self):
            return {'level': 5, 'xp': 350, 'gold': 150}
        
        def get_recent_events(self, limit):
            return []
        
        def set_auto_watering(self, enabled):
            pass
        
        class pump:
            @staticmethod
            def get_status():
                return {'is_running': False}
        
        class uv_light:
            @staticmethod
            def get_status():
                return {'is_on': True, 'auto_mode': True}
            
            @staticmethod
            def turn_on(manual=False):
                return {'success': True}
            
            @staticmethod
            def turn_off(manual=False):
                return {'success': True}
            
            @staticmethod
            def toggle(manual=False):
                return {'success': True}
            
            @staticmethod
            def set_auto_mode(enabled):
                return {'success': True}
            
            @staticmethod
            def set_schedule(start, end):
                return {'success': True}
        
        class analyzer:
            @staticmethod
            def get_hourly_averages(hours):
                return {}
            
            @staticmethod
            def calculate_statistics(hours):
                return {}
            
            @staticmethod
            def analyze_trends(hours=6):
                return {}
            
            @staticmethod
            def predict_watering_need():
                return {}
            
            @staticmethod
            def detect_anomalies(hours):
                return []
            
            @staticmethod
            def get_recommendations(sensors):
                return []
    
    # Create and start server
    api = SmartGrowAPI(
        MockController(),
        host='0.0.0.0',
        port=5000
    )
    
    print("Starting mock API server...")
    print("Test endpoints at http://localhost:5000/api/")
    api.start(debug=True)
