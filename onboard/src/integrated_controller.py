#!/usr/bin/env python3
"""
Marine Caravan - Integrated System Controller
Coordinates autopilot, collision avoidance, and AI weather intelligence
"""

import logging
import asyncio
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import json

# Import subsystems
from autopilot import AutopilotNavigation, RudderController, MotorSpeedController, AutopilotMode
from collision_avoidance import CollisionAvoidanceController, CollisionLevel
from weather_intelligence import AIWeatherIntelligence, WeatherAnalyzer, WeatherReading

logger = logging.getLogger(__name__)


class MarineCaravanIntegratedController:
    """
    Master controller that integrates:
    - Autopilot navigation
    - Collision avoidance
    - AI weather intelligence
    - Emergency management
    """
    
    def __init__(self):
        # Initialize subsystems
        self.rudder = RudderController()
        self.motor = MotorSpeedController()
        self.autopilot = AutopilotNavigation(self.rudder, self.motor)
        
        self.collision_avoidance = CollisionAvoidanceController(self.autopilot)
        
        self.weather_analyzer = WeatherAnalyzer()
        self.ai_weather = AIWeatherIntelligence(
            self.weather_analyzer, 
            self.autopilot, 
            self.collision_avoidance
        )
        
        # System state
        self.is_running = False
        self.emergency_mode = False
        self.system_status = "standby"
        
        # Event log
        self.event_log: List[Dict] = []
        self.max_events = 1000
        
        # Override thresholds
        self.weather_override_enabled = True
        self.collision_override_enabled = True
    
    async def initialize(self):
        """Initialize all subsystems"""
        logger.info('=== Marine Caravan Integrated Controller Initializing ===')
        
        self.is_running = True
        self.system_status = "ready"
        
        logger.info('✓ Autopilot system ready')
        logger.info('✓ Collision avoidance ready')
        logger.info('✓ AI weather intelligence ready')
        logger.info('=== System Ready ===')
    
    async def update_sensor_data(self, sensor_data: Dict):
        """Update all systems with new sensor data"""
        
        # Extract sensor data
        motors = sensor_data.get('motors', {})
        environment = sensor_data.get('environment', {})
        navigation = sensor_data.get('navigation', {})
        water = sensor_data.get('water', {})
        weather_data = sensor_data.get('weather', {})
        distance_sensors = sensor_data.get('distance_sensors', {})
        
        # Update autopilot position
        if navigation:
            await self.autopilot.update(
                navigation.get('heading', 0),
                navigation.get('latitude', 0),
                navigation.get('longitude', 0),
                navigation.get('speed_knots', 0)
            )
        
        # Update collision avoidance with distance sensors
        if distance_sensors or water:
            cas_data = {
                'front': distance_sensors.get('front', float('inf')),
                'front_right': distance_sensors.get('front_right', float('inf')),
                'right': distance_sensors.get('right', float('inf')),
                'rear_right': distance_sensors.get('rear_right', float('inf')),
                'rear': distance_sensors.get('rear', float('inf')),
                'rear_left': distance_sensors.get('rear_left', float('inf')),
                'left': distance_sensors.get('left', float('inf')),
                'front_left': distance_sensors.get('front_left', float('inf')),
                'depth': water.get('depth_meters', float('inf')),
            }
            await self.collision_avoidance.process_sensor_readings(cas_data, datetime.now().timestamp())
        
        # Update weather intelligence
        if weather_data:
            weather_reading = WeatherReading(
                timestamp=datetime.now(),
                wind_speed_knots=weather_data.get('wind_speed_knots', 0),
                wind_direction=weather_data.get('wind_direction', 0),
                wind_gust_knots=weather_data.get('wind_gust_knots', 0),
                temperature_celsius=weather_data.get('temperature_celsius', 0),
                humidity_percent=weather_data.get('humidity_percent', 0),
                air_pressure_hpa=weather_data.get('air_pressure_hpa', 1013),
                pressure_trend=weather_data.get('pressure_trend', 'steady'),
                wave_height_meters=weather_data.get('wave_height_meters', 0),
                visibility_km=weather_data.get('visibility_km', 10),
                precipitation_mm_h=weather_data.get('precipitation_mm_h', 0),
                current_speed_knots=weather_data.get('current_speed_knots', 0),
                current_direction=weather_data.get('current_direction', 0),
                water_temperature_celsius=water.get('temperature_celsius', 0),
                cloud_coverage_percent=weather_data.get('cloud_coverage_percent', 0),
            )
            await self.weather_analyzer.update_weather(weather_reading)
    
    async def process_intelligence(self):
        """Process all intelligence systems and make coordinated decisions"""
        
        # Get collision avoidance status
        cas_status = self.collision_avoidance.get_collision_status()
        collision_threat = cas_status['threat_level']
        
        # Get weather analysis
        weather_plan = await self.ai_weather.analyze_and_plan()
        
        # Coordinate decisions
        await self._coordinate_systems(collision_threat, weather_plan)
        
        # Log event
        self._log_event({
            'type': 'intelligence_update',
            'collision_threat': collision_threat,
            'weather_scenario': weather_plan.scenario.value,
            'weather_severity': weather_plan.severity.name,
            'system_status': self.system_status,
            'current_speed': self.motor.motor_control.motor1_speed,
            'current_heading': self.autopilot.current_heading,
        })
    
    async def _coordinate_systems(self, collision_threat: str, weather_plan):
        """Coordinate autopilot, collision avoidance, and weather responses"""
        
        # Priority: Emergency (Collision) > Severe Weather > Normal Operations
        
        if self.collision_avoidance.emergency_stop_triggered:
            logger.critical('🚨 EMERGENCY: Collision avoidance activated - STOP')
            await self.motor.set_target_speed(0)
            self.emergency_mode = True
            self.system_status = "emergency"
            return
        
        # Handle collision threat
        if collision_threat in ['DANGER', 'CRITICAL']:
            logger.error(f'⚠️ Collision threat detected: {collision_threat}')
            # Weather plan will be overridden
            # Speed is already reduced by collision avoidance
            self.system_status = "collision_avoidance"
            
            # Attempt evasive maneuver
            if self.autopilot.mode != AutopilotMode.OFF:
                safe_heading = self.collision_avoidance.distance_sensors.get_safe_heading(
                    self.autopilot.current_heading
                )
                if safe_heading is not None:
                    await self.autopilot.hold_heading(safe_heading)
                    logger.info(f'Evasive maneuver: heading {safe_heading:.0f}°')
        
        # Apply weather-based actions
        elif weather_plan.speed_adjustment is not None:
            current_speed = self.motor.motor_control.motor1_speed
            
            # Only reduce speed if weather demands it
            if weather_plan.speed_adjustment < current_speed:
                await self.motor.set_target_speed(weather_plan.speed_adjustment)
                logger.info(f'Weather action: Speed reduced to {weather_plan.speed_adjustment:.0f}%')
            
            self.system_status = f"weather_management ({weather_plan.scenario.value})"
        
        else:
            # Normal operations
            if self.system_status != "normal":
                self.system_status = "normal"
                logger.info('System status: Normal operations')
        
        # Execute weather plan if not already handled
        if not self.emergency_mode:
            await self.ai_weather.execute_plan()
    
    async def handle_emergency(self, emergency_type: str, reason: str):
        """Handle emergency situations"""
        logger.critical(f'🚨 EMERGENCY: {emergency_type} - {reason}')
        
        self.emergency_mode = True
        self.system_status = "emergency"
        
        # Immediate actions
        await self.motor.set_target_speed(0)  # Stop
        await self.autopilot.set_autopilot_mode(AutopilotMode.OFF)
        
        self._log_event({
            'type': 'emergency',
            'emergency_type': emergency_type,
            'reason': reason,
            'timestamp': datetime.now().isoformat(),
        })
    
    async def exit_emergency(self):
        """Exit emergency mode"""
        logger.info('Exiting emergency mode')
        
        self.emergency_mode = False
        self.system_status = "standby"
        
        # User must manually resume operations
        self._log_event({
            'type': 'emergency_exit',
            'timestamp': datetime.now().isoformat(),
        })
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        cas_status = self.collision_avoidance.get_collision_status()
        weather_plan = self.ai_weather.current_plan
        
        return {
            'timestamp': datetime.now().isoformat(),
            'system_status': self.system_status,
            'emergency_mode': self.emergency_mode,
            'autopilot': {
                'mode': self.autopilot.mode.value,
                'heading': self.autopilot.current_heading,
                'speed': self.motor.motor_control.motor1_speed,
            },
            'collision_avoidance': cas_status,
            'weather': {
                'scenario': weather_plan.scenario.value if weather_plan else None,
                'severity': weather_plan.severity.name if weather_plan else None,
                'confidence': weather_plan.confidence_score if weather_plan else 0,
                'alerts': weather_plan.alerts if weather_plan else [],
            },
        }
    
    def _log_event(self, event: Dict):
        """Log system event"""
        event['timestamp'] = datetime.now().isoformat()
        self.event_log.append(event)
        
        if len(self.event_log) > self.max_events:
            self.event_log.pop(0)
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info('Marine Caravan Integrated Controller shutting down')
        
        # Stop motors
        await self.motor.set_target_speed(0)
        
        # Disable autopilot
        await self.autopilot.set_autopilot_mode(AutopilotMode.OFF)
        
        self.is_running = False
        self.system_status = "shutdown"


async def main():
    """Example integrated system usage"""
    controller = MarineCaravanIntegratedController()
    await controller.initialize()
    
    # Simulate sensor data
    sample_sensor_data = {
        'motors': {
            'motor1_speed': 50,
            'motor2_speed': 50,
        },
        'environment': {
            'temperature': 22.5,
            'humidity': 65,
        },
        'navigation': {
            'heading': 45.0,
            'latitude': 36.7523,
            'longitude': 29.2311,
            'speed_knots': 8.0,
        },
        'water': {
            'depth_meters': 12.5,
            'temperature_celsius': 22.0,
        },
        'weather': {
            'wind_speed_knots': 25.0,
            'wind_direction': 180.0,
            'wave_height_meters': 2.5,
            'air_pressure_hpa': 1010.0,
            'humidity_percent': 75,
            'visibility_km': 8.0,
        },
        'distance_sensors': {
            'front': 150.0,
            'right': 200.0,
            'left': 180.0,
        },
    }
    
    # Update and process
    await controller.update_sensor_data(sample_sensor_data)
    await controller.process_intelligence()
    
    # Get status
    status = controller.get_system_status()
    logger.info(f'System Status: {json.dumps(status, indent=2)}')


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(main())
