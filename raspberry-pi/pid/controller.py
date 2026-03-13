"""
SmartGrow PID Controller for Automatic Irrigation
================================================

Implements a PID (Proportional-Integral-Derivative) controller
for maintaining optimal soil moisture levels.

The controller calculates pump duration based on the error
between target and current moisture levels.
"""

import time
import json
import logging
from dataclasses import dataclass, field
from typing import Optional, Tuple, List
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)


@dataclass
class PIDConfig:
    """PID controller configuration parameters."""
    
    # Target moisture level (%)
    target_moisture: float = 45.0
    
    # PID gains
    kp: float = 2.0      # Proportional gain
    ki: float = 0.1      # Integral gain
    kd: float = 0.5      # Derivative gain
    
    # Output limits
    min_output: float = 0.0      # Minimum pump duration (seconds)
    max_output: float = 5.0      # Maximum pump duration (seconds)
    
    # Integral windup prevention
    integral_limit: float = 50.0
    
    # Deadband - don't water if error is within this range
    deadband: float = 3.0
    
    # Minimum time between watering cycles (seconds)
    min_cycle_time: float = 300.0  # 5 minutes
    
    # Sample time for PID calculation (seconds)
    sample_time: float = 5.0
    
    @classmethod
    def from_yaml(cls, config_path: str) -> 'PIDConfig':
        """Load PID configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                pid_config = config.get('pid', {})
                return cls(
                    target_moisture=pid_config.get('target_moisture', 45.0),
                    kp=pid_config.get('kp', 2.0),
                    ki=pid_config.get('ki', 0.1),
                    kd=pid_config.get('kd', 0.5),
                    min_output=pid_config.get('min_output', 0.0),
                    max_output=pid_config.get('max_output', 5.0),
                    integral_limit=pid_config.get('integral_limit', 50.0),
                    deadband=pid_config.get('deadband', 3.0),
                    min_cycle_time=pid_config.get('min_cycle_time', 300.0),
                    sample_time=pid_config.get('sample_time', 5.0)
                )
        except Exception as e:
            logger.warning(f"Failed to load PID config: {e}, using defaults")
            return cls()
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            'target_moisture': self.target_moisture,
            'kp': self.kp,
            'ki': self.ki,
            'kd': self.kd,
            'min_output': self.min_output,
            'max_output': self.max_output,
            'integral_limit': self.integral_limit,
            'deadband': self.deadband,
            'min_cycle_time': self.min_cycle_time,
            'sample_time': self.sample_time
        }


@dataclass
class PIDState:
    """Internal state of the PID controller."""
    
    integral: float = 0.0
    last_error: float = 0.0
    last_time: float = field(default_factory=time.time)
    last_watering_time: float = 0.0
    
    # History for analysis
    error_history: List[Tuple[float, float]] = field(default_factory=list)
    output_history: List[Tuple[float, float]] = field(default_factory=list)
    
    def reset(self):
        """Reset controller state."""
        self.integral = 0.0
        self.last_error = 0.0
        self.last_time = time.time()
        self.error_history.clear()
        self.output_history.clear()


class PIDController:
    """
    PID Controller for SmartGrow Irrigation System.
    
    Maintains optimal soil moisture by calculating appropriate
    pump activation duration based on moisture sensor readings.
    
    Features:
    - Anti-windup protection
    - Deadband to prevent oscillation
    - Minimum cycle time to protect pump
    - Configurable gains via YAML
    - History tracking for analysis
    """
    
    def __init__(self, config: Optional[PIDConfig] = None):
        """Initialize PID controller with configuration."""
        self.config = config or PIDConfig()
        self.state = PIDState()
        self._enabled = True
        
        logger.info(f"PID Controller initialized with config: {self.config.to_dict()}")
    
    @classmethod
    def from_config_file(cls, config_path: str) -> 'PIDController':
        """Create PID controller from configuration file."""
        config = PIDConfig.from_yaml(config_path)
        return cls(config)
    
    def update(self, current_moisture: float) -> Tuple[float, dict]:
        """
        Calculate PID output based on current moisture reading.
        
        Args:
            current_moisture: Current soil moisture percentage (0-100)
            
        Returns:
            Tuple of (pump_duration_seconds, debug_info)
        """
        current_time = time.time()
        
        # Calculate time delta
        dt = current_time - self.state.last_time
        if dt < self.config.sample_time:
            return 0.0, {'status': 'waiting', 'remaining': self.config.sample_time - dt}
        
        # Calculate error
        error = self.config.target_moisture - current_moisture
        
        # Store error in history
        self.state.error_history.append((current_time, error))
        if len(self.state.error_history) > 1000:
            self.state.error_history = self.state.error_history[-500:]
        
        # Debug info
        debug_info = {
            'current_moisture': current_moisture,
            'target_moisture': self.config.target_moisture,
            'error': error,
            'dt': dt
        }
        
        # Check if controller is enabled
        if not self._enabled:
            debug_info['status'] = 'disabled'
            return 0.0, debug_info
        
        # Check deadband - don't water if error is small
        if abs(error) <= self.config.deadband:
            debug_info['status'] = 'in_deadband'
            debug_info['deadband'] = self.config.deadband
            self.state.last_time = current_time
            return 0.0, debug_info
        
        # Check minimum cycle time
        time_since_watering = current_time - self.state.last_watering_time
        if time_since_watering < self.config.min_cycle_time and error > 0:
            debug_info['status'] = 'cycle_cooldown'
            debug_info['cooldown_remaining'] = self.config.min_cycle_time - time_since_watering
            self.state.last_time = current_time
            return 0.0, debug_info
        
        # Only water if soil is too dry (positive error)
        if error <= 0:
            debug_info['status'] = 'moisture_ok'
            self.state.last_time = current_time
            self.state.last_error = error
            return 0.0, debug_info
        
        # Calculate PID terms
        # Proportional term
        p_term = self.config.kp * error
        
        # Integral term with anti-windup
        self.state.integral += error * dt
        self.state.integral = max(
            -self.config.integral_limit,
            min(self.config.integral_limit, self.state.integral)
        )
        i_term = self.config.ki * self.state.integral
        
        # Derivative term
        derivative = (error - self.state.last_error) / dt if dt > 0 else 0.0
        d_term = self.config.kd * derivative
        
        # Calculate total output
        output = p_term + i_term + d_term
        
        # Clamp output to limits
        output = max(self.config.min_output, min(self.config.max_output, output))
        
        # Store output in history
        self.state.output_history.append((current_time, output))
        if len(self.state.output_history) > 1000:
            self.state.output_history = self.state.output_history[-500:]
        
        # Update state
        self.state.last_error = error
        self.state.last_time = current_time
        
        if output > 0:
            self.state.last_watering_time = current_time
        
        # Detailed debug info
        debug_info.update({
            'status': 'watering' if output > 0 else 'idle',
            'p_term': p_term,
            'i_term': i_term,
            'd_term': d_term,
            'integral': self.state.integral,
            'derivative': derivative,
            'output': output,
            'pump_duration': output
        })
        
        logger.debug(f"PID Update: error={error:.2f}, output={output:.2f}s")
        
        return output, debug_info
    
    def set_target(self, target_moisture: float):
        """Set new target moisture level."""
        if 0 <= target_moisture <= 100:
            self.config.target_moisture = target_moisture
            logger.info(f"PID target moisture set to {target_moisture}%")
    
    def set_gains(self, kp: float = None, ki: float = None, kd: float = None):
        """Update PID gains."""
        if kp is not None:
            self.config.kp = kp
        if ki is not None:
            self.config.ki = ki
        if kd is not None:
            self.config.kd = kd
        
        # Reset integral when gains change
        self.state.integral = 0.0
        
        logger.info(f"PID gains updated: Kp={self.config.kp}, Ki={self.config.ki}, Kd={self.config.kd}")
    
    def enable(self):
        """Enable PID controller."""
        self._enabled = True
        logger.info("PID controller enabled")
    
    def disable(self):
        """Disable PID controller."""
        self._enabled = False
        logger.info("PID controller disabled")
    
    def reset(self):
        """Reset controller state."""
        self.state.reset()
        logger.info("PID controller reset")
    
    def get_status(self) -> dict:
        """Get current controller status."""
        return {
            'enabled': self._enabled,
            'config': self.config.to_dict(),
            'state': {
                'integral': self.state.integral,
                'last_error': self.state.last_error,
                'last_watering_time': self.state.last_watering_time,
                'error_history_length': len(self.state.error_history),
                'output_history_length': len(self.state.output_history)
            }
        }
    
    def get_performance_metrics(self) -> dict:
        """Calculate performance metrics from history."""
        if not self.state.error_history:
            return {'status': 'no_data'}
        
        errors = [e for _, e in self.state.error_history]
        outputs = [o for _, o in self.state.output_history]
        
        return {
            'average_error': sum(errors) / len(errors),
            'max_error': max(errors),
            'min_error': min(errors),
            'total_water_time': sum(outputs),
            'watering_cycles': sum(1 for o in outputs if o > 0),
            'samples': len(errors)
        }


class AdaptivePIDController(PIDController):
    """
    Adaptive PID Controller that auto-tunes gains based on performance.
    
    Uses simple gradient descent to optimize gains based on
    settling time and overshoot metrics.
    """
    
    def __init__(self, config: Optional[PIDConfig] = None):
        super().__init__(config)
        self._adaptation_enabled = False
        self._learning_rate = 0.01
        self._performance_window = 100
    
    def enable_adaptation(self, learning_rate: float = 0.01):
        """Enable adaptive gain tuning."""
        self._adaptation_enabled = True
        self._learning_rate = learning_rate
        logger.info(f"Adaptive PID enabled with learning rate {learning_rate}")
    
    def disable_adaptation(self):
        """Disable adaptive gain tuning."""
        self._adaptation_enabled = False
        logger.info("Adaptive PID disabled")
    
    def update(self, current_moisture: float) -> Tuple[float, dict]:
        """Update with optional gain adaptation."""
        output, debug_info = super().update(current_moisture)
        
        if self._adaptation_enabled and len(self.state.error_history) >= self._performance_window:
            self._adapt_gains()
        
        return output, debug_info
    
    def _adapt_gains(self):
        """Adapt gains based on recent performance."""
        recent_errors = [e for _, e in self.state.error_history[-self._performance_window:]]
        
        # Calculate metrics
        avg_error = sum(abs(e) for e in recent_errors) / len(recent_errors)
        error_variance = sum((e - avg_error) ** 2 for e in recent_errors) / len(recent_errors)
        
        # Simple adaptation rules
        # If average error is high, increase Kp
        if avg_error > self.config.deadband * 2:
            self.config.kp += self._learning_rate
        elif avg_error < self.config.deadband:
            self.config.kp = max(0.1, self.config.kp - self._learning_rate * 0.5)
        
        # If variance is high (oscillating), reduce gains
        if error_variance > 100:
            self.config.kp = max(0.1, self.config.kp * 0.95)
            self.config.kd += self._learning_rate
        
        logger.debug(f"Adaptive PID: avg_error={avg_error:.2f}, variance={error_variance:.2f}")


# Singleton instance for global access
_pid_controller: Optional[PIDController] = None


def get_pid_controller(config_path: str = None) -> PIDController:
    """Get or create the global PID controller instance."""
    global _pid_controller
    
    if _pid_controller is None:
        if config_path:
            _pid_controller = PIDController.from_config_file(config_path)
        else:
            _pid_controller = PIDController()
    
    return _pid_controller


def reset_pid_controller():
    """Reset the global PID controller."""
    global _pid_controller
    _pid_controller = None
