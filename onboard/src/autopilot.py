#!/usr/bin/env python3
"""
Marine Caravan Energy System - Autopilot Control Module
Handles rudder control, motor speed management, and autonomous navigation
"""

import logging
import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple
import asyncio

logger = logging.getLogger(__name__)


class AutopilotMode(Enum):
    """Autopilot operation modes"""
    OFF = "off"                    # Manual control only
    HEADING = "heading"            # Maintain constant magnetic heading
    TRACK = "track"                # GPS waypoint tracking
    RETURN = "return"              # Return to home
    CIRCLE = "circle"              # Circle around waypoint
    FOLLOW = "follow"              # Follow moving target


@dataclass
class RudderState:
    """Current rudder position and state"""
    position: float                 # Current rudder angle (-45 to +45 degrees)
    target_position: float          # Target rudder angle
    speed: float                    # Rudder movement speed (degrees/second)
    is_moving: bool                 # Is rudder currently moving
    max_angle: float = 45.0         # Maximum rudder angle (degrees)
    min_angle: float = -45.0        # Minimum rudder angle (degrees)


@dataclass
class MotorSpeedControl:
    """Motor speed control parameters"""
    motor1_speed: float             # Motor 1 speed (0-100%)
    motor2_speed: float             # Motor 2 speed (0-100%)
    target_speed: float             # Target combined motor speed (0-100%)
    max_speed: float = 100.0        # Maximum speed percentage
    min_speed: float = 0.0          # Minimum speed percentage
    ramp_rate: float = 5.0          # Speed change rate (%/second)
    current_motor1_rpm: int = 0     # Current motor 1 RPM
    current_motor2_rpm: int = 0     # Current motor 2 RPM
    current_motor1_amps: float = 0.0  # Current motor 1 amperage
    current_motor2_amps: float = 0.0  # Current motor 2 amperage


@dataclass
class AutopilotWaypoint:
    """GPS waypoint for autonomous navigation"""
    latitude: float
    longitude: float
    radius: float = 10.0            # Waypoint acceptance radius (meters)
    speed: float = 50.0             # Target speed for this waypoint (0-100%)
    hold_time: float = 0.0          # Time to hold at waypoint (seconds)


class RudderController:
    """Manages rudder servo control with PID feedback"""
    
    def __init__(self, max_servo_pwm: int = 180):
        self.rudder_state = RudderState(position=0.0, target_position=0.0)
        self.max_servo_pwm = max_servo_pwm
        self.pid_kp = 2.0             # Proportional gain
        self.pid_ki = 0.5             # Integral gain
        self.pid_kd = 0.3             # Derivative gain
        self.integral_error = 0.0
        self.last_error = 0.0
    
    async def set_target_angle(self, target_angle: float):
        """Set target rudder angle"""
        # Clamp to max/min angles
        self.rudder_state.target_position = max(
            self.rudder_state.min_angle,
            min(self.rudder_state.max_angle, target_angle)
        )
        logger.info(f'Rudder target angle set to: {target_angle:.1f}°')
    
    async def update_position(self, current_position: float, dt: float = 0.1):
        """Update rudder position using PID controller"""
        error = self.rudder_state.target_position - current_position
        
        # PID calculation
        self.integral_error += error * dt
        derivative_error = (error - self.last_error) / dt
        
        pid_output = (
            self.pid_kp * error +
            self.pid_ki * self.integral_error +
            self.pid_kd * derivative_error
        )
        
        # Convert to servo PWM (0-180 degrees)
        servo_angle = max(0, min(180, 90 + pid_output))
        
        self.rudder_state.position = current_position
        self.last_error = error
        
        return servo_angle
    
    def get_servo_pwm(self) -> int:
        """Get current PWM value for servo"""
        # Convert angle to PWM (typical: 1000-2000 microseconds)
        angle_normalized = (self.rudder_state.position + 45) / 90
        return int(1000 + angle_normalized * 1000)


class MotorSpeedController:
    """Manages motor speed with acceleration/deceleration ramps"""
    
    def __init__(self):
        self.motor_control = MotorSpeedControl(
            motor1_speed=0.0,
            motor2_speed=0.0,
            target_speed=0.0
        )
        self.speed_pid_kp = 1.5
        self.speed_pid_ki = 0.2
        self.speed_pid_kd = 0.1
    
    async def set_target_speed(self, speed: float, synchronized: bool = True):
        """
        Set target motor speed
        
        Args:
            speed: Target speed (0-100%)
            synchronized: If True, both motors run at same speed
        """
        speed = max(0, min(100, speed))
        self.motor_control.target_speed = speed
        
        if synchronized:
            logger.info(f'Synchronized motor speed set to: {speed:.1f}%')
        else:
            logger.info(f'Target motor speed set to: {speed:.1f}%')
    
    async def update_speeds(self, dt: float = 0.1) -> Tuple[float, float]:
        """
        Update motor speeds with acceleration ramping
        
        Returns:
            Tuple of (motor1_speed, motor2_speed)
        """
        # Calculate acceleration step
        speed_diff = self.motor_control.target_speed - self.motor_control.motor1_speed
        max_change = self.motor_control.ramp_rate * dt
        
        if abs(speed_diff) > max_change:
            speed_change = max_change if speed_diff > 0 else -max_change
        else:
            speed_change = speed_diff
        
        self.motor_control.motor1_speed += speed_change
        self.motor_control.motor2_speed += speed_change
        
        # Clamp speeds
        self.motor_control.motor1_speed = max(0, min(100, self.motor_control.motor1_speed))
        self.motor_control.motor2_speed = max(0, min(100, self.motor_control.motor2_speed))
        
        return (self.motor_control.motor1_speed, self.motor_control.motor2_speed)
    
    async def set_motor_speeds(self, motor1: float, motor2: float):
        """Set individual motor speeds (0-100%)"""
        self.motor_control.motor1_speed = max(0, min(100, motor1))
        self.motor_control.motor2_speed = max(0, min(100, motor2))
        logger.info(f'Motor 1: {motor1:.1f}%, Motor 2: {motor2:.1f}%')


class AutopilotNavigation:
    """Main autopilot navigation controller"""
    
    def __init__(self, rudder_controller: RudderController, 
                 motor_controller: MotorSpeedController):
        self.rudder_controller = rudder_controller
        self.motor_controller = motor_controller
        self.mode = AutopilotMode.OFF
        self.current_heading = 0.0      # Degrees (0-360)
        self.current_lat = 0.0
        self.current_lon = 0.0
        self.current_speed = 0.0        # Knots
        self.waypoints: list[AutopilotWaypoint] = []
        self.current_waypoint_idx = 0
        self.home_lat = 0.0
        self.home_lon = 0.0
        
        # Wind compensation
        self.wind_speed = 0.0           # m/s
        self.wind_direction = 0.0       # Degrees
        self.wind_compensation_factor = 0.5  # How much to compensate (0-1)
    
    async def set_autopilot_mode(self, mode: AutopilotMode):
        """Switch autopilot mode"""
        self.mode = mode
        logger.info(f'Autopilot mode changed to: {mode.value}')
        
        if mode == AutopilotMode.OFF:
            await self.motor_controller.set_target_speed(0)
    
    async def hold_heading(self, target_heading: float):
        """Maintain constant magnetic heading"""
        if self.mode != AutopilotMode.HEADING:
            await self.set_autopilot_mode(AutopilotMode.HEADING)
        
        # Normalize heading to 0-360
        target_heading = target_heading % 360
        
        # Calculate shortest turn direction
        heading_error = target_heading - self.current_heading
        
        # Normalize error to -180 to +180
        if heading_error > 180:
            heading_error -= 360
        elif heading_error < -180:
            heading_error += 360
        
        # PID-based rudder control
        # Scale error to rudder angle (-45 to +45 degrees)
        rudder_angle = max(-45, min(45, heading_error * 0.5))
        
        await self.rudder_controller.set_target_angle(rudder_angle)
        logger.debug(f'Holding heading: {target_heading:.1f}°, Error: {heading_error:.1f}°')
    
    async def track_waypoint(self, waypoint: AutopilotWaypoint):
        """Navigate to waypoint"""
        if self.mode != AutopilotMode.TRACK:
            await self.set_autopilot_mode(AutopilotMode.TRACK)
        
        # Calculate bearing and distance to waypoint
        bearing = self._calculate_bearing(
            self.current_lat, self.current_lon,
            waypoint.latitude, waypoint.longitude
        )
        distance = self._calculate_distance(
            self.current_lat, self.current_lon,
            waypoint.latitude, waypoint.longitude
        )
        
        logger.debug(f'Waypoint bearing: {bearing:.1f}°, Distance: {distance:.1f}m')
        
        # Apply wind compensation
        compensated_bearing = self._apply_wind_compensation(bearing)
        
        # Maintain heading towards waypoint
        await self.hold_heading(compensated_bearing)
        
        # Check if waypoint reached
        if distance <= waypoint.radius:
            logger.info(f'Waypoint reached! Distance: {distance:.1f}m')
            return True
        
        return False
    
    async def return_to_home(self):
        """Navigate back to home position"""
        if self.mode != AutopilotMode.RETURN:
            await self.set_autopilot_mode(AutopilotMode.RETURN)
        
        home_waypoint = AutopilotWaypoint(
            latitude=self.home_lat,
            longitude=self.home_lon
        )
        
        return await self.track_waypoint(home_waypoint)
    
    def _calculate_bearing(self, lat1: float, lon1: float, 
                          lat2: float, lon2: float) -> float:
        """Calculate bearing between two points (Haversine formula)"""
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        lon_diff = math.radians(lon2 - lon1)
        
        x = math.sin(lon_diff) * math.cos(lat2_rad)
        y = (math.cos(lat1_rad) * math.sin(lat2_rad) -
             math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(lon_diff))
        
        bearing = math.degrees(math.atan2(x, y))
        return bearing % 360
    
    def _calculate_distance(self, lat1: float, lon1: float, 
                           lat2: float, lon2: float) -> float:
        """Calculate distance between two points (meters)"""
        R = 6371000  # Earth radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat/2)**2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def _apply_wind_compensation(self, target_bearing: float) -> float:
        """Adjust bearing based on wind"""
        wind_effect = (self.wind_direction - target_bearing) * self.wind_compensation_factor
        return (target_bearing + wind_effect) % 360
    
    async def update(self, current_heading: float, current_lat: float, 
                    current_lon: float, current_speed: float):
        """Update autopilot with current position and heading"""
        self.current_heading = current_heading
        self.current_lat = current_lat
        self.current_lon = current_lon
        self.current_speed = current_speed
        
        # Execute autopilot mode logic
        if self.mode == AutopilotMode.HEADING:
            # Heading hold is handled by hold_heading method
            pass
        
        elif self.mode == AutopilotMode.TRACK:
            if self.waypoints and self.current_waypoint_idx < len(self.waypoints):
                reached = await self.track_waypoint(self.waypoints[self.current_waypoint_idx])
                if reached:
                    self.current_waypoint_idx += 1
        
        elif self.mode == AutopilotMode.RETURN:
            await self.return_to_home()


async def main():
    """Example autopilot usage"""
    logger.info('Marine Caravan Autopilot System Initialized')
    
    rudder = RudderController()
    motor = MotorSpeedController()
    autopilot = AutopilotNavigation(rudder, motor)
    
    # Example: Set home position
    autopilot.home_lat = 36.7523
    autopilot.home_lon = 29.2311
    
    # Example: Set heading mode to North
    await autopilot.set_autopilot_mode(AutopilotMode.HEADING)
    await autopilot.hold_heading(0.0)  # North
    
    # Example: Set motor speed
    await motor.set_target_speed(75.0)
    
    logger.info('Autopilot ready for operation')


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(main())
