#!/usr/bin/env python3
"""
Marine Caravan - Collision Avoidance System (CAS)
Monitors distance sensors and prevents collisions with obstacles
"""

import logging
import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, List
import math

logger = logging.getLogger(__name__)


class CollisionLevel(Enum):
    """Collision threat levels"""
    SAFE = 0               # No threat
    CAUTION = 1            # 100m < distance < 150m
    WARNING = 2            # 30m < distance < 100m
    DANGER = 3             # 5m < distance < 30m
    CRITICAL = 4           # distance < 5m


class SensorDirection(Enum):
    """Distance sensor directions (bearing)"""
    FRONT = 0              # 0°
    FRONT_RIGHT = 45       # 45°
    RIGHT = 90             # 90°
    REAR_RIGHT = 135       # 135°
    REAR = 180             # 180°
    REAR_LEFT = 225        # 225°
    LEFT = 270             # 270°
    FRONT_LEFT = 315       # 315°


@dataclass
class DistanceSensorReading:
    """Single distance sensor reading"""
    direction: SensorDirection
    distance_meters: float          # Distance to obstacle (meters)
    is_active: bool                 # Sensor functioning properly
    last_update: float              # Timestamp of last update
    threat_level: CollisionLevel = CollisionLevel.SAFE


@dataclass
class DepthReading:
    """Underwater depth measurement"""
    depth_meters: float             # Water depth below vessel
    safe_depth_meters: float = 2.0  # Minimum safe operating depth
    is_warning: bool = False        # True if depth < safe_depth


class DistanceSensorArray:
    """Manages array of distance sensors around vessel"""
    
    def __init__(self):
        self.sensors: Dict[SensorDirection, DistanceSensorReading] = {
            direction: DistanceSensorReading(
                direction=direction,
                distance_meters=float('inf'),
                is_active=False,
                last_update=0.0
            )
            for direction in SensorDirection
        }
        
        # Distance thresholds for threat levels (meters)
        self.threat_thresholds = {
            CollisionLevel.CAUTION: 150,
            CollisionLevel.WARNING: 100,
            CollisionLevel.DANGER: 30,
            CollisionLevel.CRITICAL: 5
        }
    
    async def update_reading(self, direction: SensorDirection, 
                            distance_meters: float, timestamp: float):
        """Update sensor reading"""
        if direction in self.sensors:
            reading = self.sensors[direction]
            reading.distance_meters = distance_meters
            reading.is_active = True
            reading.last_update = timestamp
            
            # Calculate threat level
            reading.threat_level = self._calculate_threat_level(distance_meters)
    
    def _calculate_threat_level(self, distance: float) -> CollisionLevel:
        """Determine threat level based on distance"""
        if distance < self.threat_thresholds[CollisionLevel.CRITICAL]:
            return CollisionLevel.CRITICAL
        elif distance < self.threat_thresholds[CollisionLevel.DANGER]:
            return CollisionLevel.DANGER
        elif distance < self.threat_thresholds[CollisionLevel.WARNING]:
            return CollisionLevel.WARNING
        elif distance < self.threat_thresholds[CollisionLevel.CAUTION]:
            return CollisionLevel.CAUTION
        else:
            return CollisionLevel.SAFE
    
    def get_max_threat_level(self) -> CollisionLevel:
        """Get highest threat level from all sensors"""
        levels = [s.threat_level for s in self.sensors.values() if s.is_active]
        if not levels:
            return CollisionLevel.SAFE
        return max(levels, key=lambda x: x.value)
    
    def get_obstacles_by_direction(self, max_distance: float = 100.0) -> List[tuple]:
        """Get list of obstacles within range, sorted by distance"""
        obstacles = []
        for direction, reading in self.sensors.items():
            if reading.is_active and reading.distance_meters < max_distance:
                obstacles.append((direction, reading.distance_meters))
        
        # Sort by distance (closest first)
        return sorted(obstacles, key=lambda x: x[1])
    
    def get_safe_heading(self, current_heading: float, avoid_angle: float = 30.0) -> Optional[float]:
        """
        Calculate safe heading to avoid obstacles
        
        Args:
            current_heading: Current vessel heading (degrees)
            avoid_angle: How much to deviate from current heading (degrees)
        
        Returns:
            Safe heading in degrees, or None if no safe heading found
        """
        # Check quadrants around current heading
        safe_quadrants = []
        
        for direction in SensorDirection:
            reading = self.sensors[direction]
            if reading.is_active and reading.threat_level.value < CollisionLevel.DANGER.value:
                safe_quadrants.append(direction.value)
        
        if not safe_quadrants:
            return None
        
        # Find quadrant furthest from current obstacles
        best_heading = min(safe_quadrants, key=lambda x: abs(x - current_heading))
        return float(best_heading)


class UnderwaterNavigationSystem:
    """Manages sonar depth measurement and underwater hazards"""
    
    def __init__(self):
        self.depth_reading = DepthReading(depth_meters=float('inf'))
        self.sonar_active = False
        self.depth_history: List[float] = []
        self.max_history = 100
        
        # Depth warning thresholds
        self.shallow_water_threshold = 5.0  # meters
        self.critical_shallow_threshold = 2.0  # meters
    
    async def update_depth(self, depth_meters: float, timestamp: float):
        """Update depth reading from sonar"""
        self.depth_reading.depth_meters = depth_meters
        self.sonar_active = True
        
        # Check for shallow water warning
        if depth_meters < self.critical_shallow_threshold:
            self.depth_reading.is_warning = True
            logger.critical(f'CRITICAL: Shallow water! Depth: {depth_meters:.1f}m')
        elif depth_meters < self.shallow_water_threshold:
            self.depth_reading.is_warning = True
            logger.warning(f'WARNING: Shallow water approaching! Depth: {depth_meters:.1f}m')
        else:
            self.depth_reading.is_warning = False
        
        # Keep history for trend analysis
        self.depth_history.append(depth_meters)
        if len(self.depth_history) > self.max_history:
            self.depth_history.pop(0)
    
    def get_depth_trend(self) -> str:
        """Analyze depth trend (getting shallower or deeper)"""
        if len(self.depth_history) < 2:
            return "unknown"
        
        recent_avg = sum(self.depth_history[-10:]) / 10
        older_avg = sum(self.depth_history[-20:-10]) / 10
        
        if recent_avg < older_avg:
            return "shallower"
        elif recent_avg > older_avg:
            return "deeper"
        else:
            return "stable"
    
    def is_safe_depth(self) -> bool:
        """Check if current depth is safe for operation"""
        return self.depth_reading.depth_meters > self.depth_reading.safe_depth_meters


class CollisionAvoidanceController:
    """Main collision avoidance system coordinator"""
    
    def __init__(self, autopilot_controller=None):
        self.distance_sensors = DistanceSensorArray()
        self.underwater_nav = UnderwaterNavigationSystem()
        self.autopilot = autopilot_controller
        
        # System state
        self.cas_enabled = True
        self.emergency_stop_triggered = False
        self.max_speed_reduction = 0.25  # Can reduce speed to 25%
        self.current_threat_level = CollisionLevel.SAFE
        
        # Callback for external systems
        self.on_threat_level_changed = None
        self.on_emergency_stop = None
    
    async def process_sensor_readings(self, readings_dict: Dict[str, float], timestamp: float):
        """
        Process all sensor readings
        
        Args:
            readings_dict: {
                'front': distance,
                'front_right': distance,
                'right': distance,
                'rear_right': distance,
                'rear': distance,
                'rear_left': distance,
                'left': distance,
                'front_left': distance,
                'depth': depth
            }
            timestamp: Current timestamp
        """
        if not self.cas_enabled:
            return
        
        # Update distance sensors
        direction_map = {
            'front': SensorDirection.FRONT,
            'front_right': SensorDirection.FRONT_RIGHT,
            'right': SensorDirection.RIGHT,
            'rear_right': SensorDirection.REAR_RIGHT,
            'rear': SensorDirection.REAR,
            'rear_left': SensorDirection.REAR_LEFT,
            'left': SensorDirection.LEFT,
            'front_left': SensorDirection.FRONT_LEFT,
        }
        
        for key, direction in direction_map.items():
            if key in readings_dict:
                await self.distance_sensors.update_reading(
                    direction, 
                    readings_dict[key],
                    timestamp
                )
        
        # Update depth
        if 'depth' in readings_dict:
            await self.underwater_nav.update_depth(readings_dict['depth'], timestamp)
        
        # Evaluate threat and take action
        await self._evaluate_and_respond()
    
    async def _evaluate_and_respond(self):
        """Evaluate collision threat and respond appropriately"""
        max_threat = self.distance_sensors.get_max_threat_level()
        depth_safe = self.underwater_nav.is_safe_depth()
        
        # Threat level changed
        if max_threat != self.current_threat_level:
            self.current_threat_level = max_threat
            if self.on_threat_level_changed:
                await self.on_threat_level_changed(max_threat)
        
        # Handle based on threat level
        if max_threat == CollisionLevel.CRITICAL or not depth_safe:
            await self._handle_critical_threat()
        
        elif max_threat == CollisionLevel.DANGER:
            await self._handle_danger_threat()
        
        elif max_threat == CollisionLevel.WARNING:
            await self._handle_warning_threat()
        
        elif max_threat == CollisionLevel.CAUTION:
            await self._handle_caution_threat()
    
    async def _handle_critical_threat(self):
        """Handle critical collision threat - emergency stop"""
        logger.critical('🚨 CRITICAL COLLISION THREAT - EMERGENCY STOP')
        
        if self.autopilot:
            # Disable autopilot
            from autopilot import AutopilotMode
            await self.autopilot.set_autopilot_mode(AutopilotMode.OFF)
            
            # Emergency stop motors
            await self.autopilot.motor_controller.set_target_speed(0)
        
        self.emergency_stop_triggered = True
        if self.on_emergency_stop:
            await self.on_emergency_stop()
    
    async def _handle_danger_threat(self):
        """Handle danger threat - aggressive speed reduction"""
        logger.error('⚠️ DANGER: Collision threat - reducing speed to 25%')
        
        if self.autopilot:
            current_speed = self.autopilot.motor_controller.motor_control.motor1_speed
            reduced_speed = current_speed * self.max_speed_reduction
            await self.autopilot.motor_controller.set_target_speed(reduced_speed)
    
    async def _handle_warning_threat(self):
        """Handle warning threat - moderate speed reduction"""
        logger.warning('⚠️ WARNING: Obstacle detected - reducing speed to 50%')
        
        if self.autopilot:
            current_speed = self.autopilot.motor_controller.motor_control.motor1_speed
            reduced_speed = current_speed * 0.5
            await self.autopilot.motor_controller.set_target_speed(reduced_speed)
    
    async def _handle_caution_threat(self):
        """Handle caution threat - slight speed reduction"""
        logger.info('ℹ️ CAUTION: Obstacle at distance - reducing speed to 75%')
        
        if self.autopilot:
            current_speed = self.autopilot.motor_controller.motor_control.motor1_speed
            reduced_speed = current_speed * 0.75
            await self.autopilot.motor_controller.set_target_speed(reduced_speed)
    
    def get_collision_status(self) -> Dict:
        """Get detailed collision avoidance status"""
        obstacles = self.distance_sensors.get_obstacles_by_direction()
        
        return {
            'cas_enabled': self.cas_enabled,
            'threat_level': self.current_threat_level.name,
            'emergency_stop': self.emergency_stop_triggered,
            'obstacles': [(d.name, dist) for d, dist in obstacles],
            'depth': self.underwater_nav.depth_reading.depth_meters,
            'depth_safe': self.underwater_nav.is_safe_depth(),
            'depth_trend': self.underwater_nav.get_depth_trend(),
        }


async def example_usage():
    """Example usage of collision avoidance system"""
    cas = CollisionAvoidanceController()
    
    # Simulate sensor readings
    sensor_data = {
        'front': 50.0,          # 50m obstacle ahead
        'front_right': 80.0,
        'right': 150.0,
        'rear_right': 200.0,
        'rear': 300.0,
        'rear_left': 200.0,
        'left': 120.0,
        'front_left': 75.0,
        'depth': 8.5             # 8.5m depth
    }
    
    import time
    await cas.process_sensor_readings(sensor_data, time.time())
    
    status = cas.get_collision_status()
    logger.info(f'CAS Status: {status}')


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(example_usage())
