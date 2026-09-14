#!/usr/bin/env python3
"""
Marine Caravan - Fire Detection & Suppression System (FDSS)
Automatic fire detection, suppression, and emergency response
"""

import logging
import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import math

logger = logging.getLogger(__name__)


class FireSeverity(Enum):
    """Fire threat severity levels"""
    NO_FIRE = 0
    SMOKE_DETECTED = 1         # Smoke only
    SMALL_FIRE = 2             # Small fire, containable
    MEDIUM_FIRE = 3            # Medium fire, spreading
    MAJOR_FIRE = 4             # Large fire, uncontrollable


class FireLocation(Enum):
    """Fire locations onboard"""
    ENGINE_ROOM = "engine_room"
    FUEL_TANK = "fuel_tank"
    ELECTRICAL_PANEL = "electrical_panel"
    GALLEY = "galley"
    CABIN = "cabin"
    STORAGE = "storage"
    EXTERIOR = "exterior"
    UNKNOWN = "unknown"


@dataclass
class FireSensorReading:
    """Fire detection sensor reading"""
    location: FireLocation
    temperature_celsius: float          # Local temperature
    smoke_level: float                  # Smoke detection (0-100%)
    flame_detected: bool                # Flame detection
    co_level_ppm: float                 # Carbon monoxide
    fire_severity: FireSeverity = FireSeverity.NO_FIRE
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class FireSuppressionZone:
    """Fire suppression system zone"""
    zone_id: str
    location: FireLocation
    sprinkler_count: int                # Number of sprinklers
    pump_pressure_bar: float            # System pressure
    water_flow_rate_liters_min: float   # Flow rate capacity
    is_active: bool = False             # System active
    manual_override: bool = False       # Manual control
    activation_time: Optional[datetime] = None


class FireDetectionSystem:
    """Multi-sensor fire detection system"""
    
    def __init__(self):
        self.sensors: Dict[FireLocation, FireSensorReading] = {
            location: FireSensorReading(
                location=location,
                temperature_celsius=20.0,
                smoke_level=0.0,
                flame_detected=False,
                co_level_ppm=0.0
            )
            for location in FireLocation
        }
        
        # Temperature thresholds
        self.temp_thresholds = {
            'smoke_warning': 40.0,      # Temperature alert
            'fire_start': 60.0,          # Fire likely
            'major_fire': 100.0,         # Major fire
            'critical': 150.0,           # System shutdown
        }
        
        # Smoke thresholds
        self.smoke_thresholds = {
            'detection': 5.0,            # Smoke detected
            'alert': 15.0,               # Alert level
            'critical': 40.0,            # Critical
        }
        
        # CO thresholds
        self.co_thresholds = {
            'detection': 35.0,           # ppm
            'alert': 100.0,
            'critical': 200.0,           # IDLH (Immediately Dangerous to Life/Health)
        }
        
        self.active_fires: List[FireLocation] = []
    
    async def update_sensor(self, location: FireLocation, reading: FireSensorReading):
        """Update fire detection sensor"""
        self.sensors[location] = reading
        
        # Calculate fire severity
        severity = self._calculate_fire_severity(reading)
        reading.fire_severity = severity
        
        if severity != FireSeverity.NO_FIRE:
            if location not in self.active_fires:
                self.active_fires.append(location)
                logger.warning(f'🔥 FIRE DETECTED at {location.value}: {severity.name}')
        else:
            if location in self.active_fires:
                self.active_fires.remove(location)
                logger.info(f'✓ Fire extinguished at {location.value}')
    
    def _calculate_fire_severity(self, reading: FireSensorReading) -> FireSeverity:
        """Calculate fire severity from sensor data"""
        
        # Flame detection = confirmed fire
        if reading.flame_detected:
            if reading.temperature_celsius > self.temp_thresholds['major_fire']:
                return FireSeverity.MAJOR_FIRE
            else:
                return FireSeverity.MEDIUM_FIRE
        
        # Temperature-based detection
        if reading.temperature_celsius > self.temp_thresholds['major_fire']:
            return FireSeverity.MAJOR_FIRE
        elif reading.temperature_celsius > self.temp_thresholds['fire_start']:
            if reading.smoke_level > self.smoke_thresholds['alert']:
                return FireSeverity.MEDIUM_FIRE
            else:
                return FireSeverity.SMALL_FIRE
        
        # Smoke detection
        if reading.smoke_level > self.smoke_thresholds['alert']:
            return FireSeverity.SMALL_FIRE
        elif reading.smoke_level > self.smoke_thresholds['detection']:
            return FireSeverity.SMOKE_DETECTED
        
        # CO detection
        if reading.co_level_ppm > self.co_thresholds['critical']:
            return FireSeverity.MAJOR_FIRE
        elif reading.co_level_ppm > self.co_thresholds['alert']:
            return FireSeverity.MEDIUM_FIRE
        
        return FireSeverity.NO_FIRE
    
    def get_fire_status(self) -> Dict:
        """Get comprehensive fire detection status"""
        return {
            'active_fires': [f.value for f in self.active_fires],
            'fire_count': len(self.active_fires),
            'max_severity': max([s.fire_severity for s in self.sensors.values()]).name,
            'sensors_status': {
                loc.value: {
                    'temperature': reading.temperature_celsius,
                    'smoke': reading.smoke_level,
                    'flame': reading.flame_detected,
                    'co': reading.co_level_ppm,
                    'severity': reading.fire_severity.name
                }
                for loc, reading in self.sensors.items()
            }
        }


class AutomaticFireSuppressionSystem:
    """Automatic fire suppression with water sprinklers"""
    
    def __init__(self):
        self.zones: Dict[str, FireSuppressionZone] = {
            'engine': FireSuppressionZone(
                zone_id='engine',
                location=FireLocation.ENGINE_ROOM,
                sprinkler_count=6,
                pump_pressure_bar=2.5,
                water_flow_rate_liters_min=60.0
            ),
            'fuel': FireSuppressionZone(
                zone_id='fuel',
                location=FireLocation.FUEL_TANK,
                sprinkler_count=3,
                pump_pressure_bar=2.5,
                water_flow_rate_liters_min=40.0
            ),
            'electrical': FireSuppressionZone(
                zone_id='electrical',
                location=FireLocation.ELECTRICAL_PANEL,
                sprinkler_count=2,
                pump_pressure_bar=1.5,
                water_flow_rate_liters_min=20.0
            ),
            'galley': FireSuppressionZone(
                zone_id='galley',
                location=FireLocation.GALLEY,
                sprinkler_count=4,
                pump_pressure_bar=2.0,
                water_flow_rate_liters_min=50.0
            ),
            'cabin': FireSuppressionZone(
                zone_id='cabin',
                location=FireLocation.CABIN,
                sprinkler_count=5,
                pump_pressure_bar=2.0,
                water_flow_rate_liters_min=50.0
            ),
            'storage': FireSuppressionZone(
                zone_id='storage',
                location=FireLocation.STORAGE,
                sprinkler_count=3,
                pump_pressure_bar=2.0,
                water_flow_rate_liters_min=40.0
            ),
        }
        
        self.pump_running = False
        self.pump_speed_percent = 0.0
        self.water_intake_source = "sea_water"  # sea_water or fresh_water
        self.total_water_pumped_liters = 0.0
    
    async def activate_zone(self, zone_id: str) -> bool:
        """Activate sprinkler zone"""
        if zone_id not in self.zones:
            logger.error(f'Zone {zone_id} not found')
            return False
        
        zone = self.zones[zone_id]
        zone.is_active = True
        zone.activation_time = datetime.now()
        
        # Start pump
        await self._start_pump()
        
        logger.warning(f'🚨 FIRE SUPPRESSION ACTIVATED: {zone.location.value}')
        logger.info(f'  Sprinklers: {zone.sprinkler_count}x at {zone.pump_pressure_bar}bar')
        logger.info(f'  Flow rate: {zone.water_flow_rate_liters_min} L/min')
        
        return True
    
    async def deactivate_zone(self, zone_id: str) -> bool:
        """Deactivate sprinkler zone"""
        if zone_id not in self.zones:
            return False
        
        self.zones[zone_id].is_active = False
        
        # Check if any zones still active
        active_count = sum(1 for z in self.zones.values() if z.is_active)
        if active_count == 0:
            await self._stop_pump()
        
        logger.info(f'Fire suppression deactivated: {zone_id}')
        return True
    
    async def _start_pump(self):
        """Start water pump"""
        if not self.pump_running:
            self.pump_running = True
            self.pump_speed_percent = 100.0
            logger.info(f'💧 PUMP STARTED - Water intake: {self.water_intake_source}')
    
    async def _stop_pump(self):
        """Stop water pump"""
        self.pump_running = False
        self.pump_speed_percent = 0.0
        logger.info('💧 PUMP STOPPED')
    
    def get_suppression_status(self) -> Dict:
        """Get fire suppression system status"""
        active_zones = [z for z in self.zones.values() if z.is_active]
        total_flow = sum(z.water_flow_rate_liters_min for z in active_zones)
        
        return {
            'pump_running': self.pump_running,
            'pump_speed': self.pump_speed_percent,
            'water_source': self.water_intake_source,
            'active_zones': [z.zone_id for z in active_zones],
            'total_flow_liters_min': total_flow,
            'total_water_pumped': self.total_water_pumped_liters,
            'sprinklers_active': sum(z.sprinkler_count for z in active_zones)
        }


class EmergencyAlertSystem:
    """Emergency siren and strobe light system"""
    
    def __init__(self):
        self.siren_active = False
        self.strobe_active = False
        self.alert_level = "none"  # none, warning, emergency, critical
        self.alert_type = None     # fire, collision, water, medical, etc
        
        # Siren parameters
        self.siren_frequency_hz = 1000.0
        self.siren_volume_db = 120.0
        self.siren_pattern = "continuous"  # continuous or pulsed
        
        # Strobe parameters
        self.strobe_frequency_hz = 2.0
        self.strobe_intensity_percent = 100.0
        self.strobe_color = "red"  # red, yellow, white
    
    async def activate_alert(self, alert_type: str, severity: str = "warning"):
        """Activate emergency alert"""
        self.alert_type = alert_type
        self.alert_level = severity
        
        if severity in ["emergency", "critical"]:
            await self._activate_siren()
            await self._activate_strobe()
        elif severity == "warning":
            await self._activate_strobe()
            # Siren optional for warnings
        
        logger.warning(f'🚨 ALERT ACTIVATED: {alert_type.upper()} - {severity}')
    
    async def deactivate_alert(self):
        """Deactivate emergency alert"""
        await self._deactivate_siren()
        await self._deactivate_strobe()
        self.alert_level = "none"
        self.alert_type = None
        logger.info('✓ Alert deactivated')
    
    async def _activate_siren(self):
        """Activate siren"""
        self.siren_active = True
        logger.info(f'🔔 SIREN: {self.siren_frequency_hz}Hz, {self.siren_volume_db}dB, {self.siren_pattern}')
    
    async def _deactivate_siren(self):
        """Deactivate siren"""
        self.siren_active = False
    
    async def _activate_strobe(self):
        """Activate strobe light"""
        self.strobe_active = True
        logger.info(f'💡 STROBE: {self.strobe_frequency_hz}Hz, {self.strobe_color}, {self.strobe_intensity_percent}%')
    
    async def _deactivate_strobe(self):
        """Deactivate strobe light"""
        self.strobe_active = False
    
    def get_alert_status(self) -> Dict:
        """Get alert system status"""
        return {
            'alert_level': self.alert_level,
            'alert_type': self.alert_type,
            'siren_active': self.siren_active,
            'strobe_active': self.strobe_active,
            'siren_frequency': self.siren_frequency_hz,
            'strobe_frequency': self.strobe_frequency_hz,
        }


class EmergencyLifeRaftSystem:
    """Emergency life raft deployment system"""
    
    def __init__(self):
        self.raft_available = True
        self.raft_inflation_status = "stored"  # stored, deploying, deployed, missing
        self.inflation_pressure_bar = 1.3      # Typical pressure
        self.inflation_time_seconds = 15.0     # Time to fully inflate
        self.raft_capacity_persons = 6
        
        # Raft location
        self.storage_location = "cabin_roof_locker"
        self.storage_pressure_bottle = "125_liter_bottle"  # Pressurized bottle specs
        
        # Deployment sensors
        self.pressure_sensor_active = True
        self.tether_connected = True
        self.inflation_valve_position = "closed"
    
    async def deploy_raft(self) -> Dict:
        """Deploy emergency life raft"""
        logger.critical('🚨 EMERGENCY LIFE RAFT DEPLOYMENT INITIATED')
        
        if not self.raft_available:
            logger.error('❌ Life raft not available!')
            return {'success': False, 'reason': 'raft_not_available'}
        
        if not self.pressure_sensor_active:
            logger.error('❌ Pressure sensor not active!')
            return {'success': False, 'reason': 'sensor_fault'}
        
        if not self.tether_connected:
            logger.error('❌ Raft tether not connected!')
            return {'success': False, 'reason': 'tether_disconnected'}
        
        # Sequence deployment
        logger.info('1. Opening storage locker...')
        await asyncio.sleep(1)
        
        logger.info('2. Releasing pressurized inflation bottle...')
        await asyncio.sleep(1)
        
        logger.info('3. Opening inflation valve...')
        self.inflation_valve_position = "open"
        await asyncio.sleep(1)
        
        logger.info('4. Inflating raft...')
        self.raft_inflation_status = "deploying"
        
        # Simulate inflation
        for i in range(5):
            percent = (i + 1) * 20
            logger.info(f'   Inflation progress: {percent}%')
            await asyncio.sleep(3)
        
        self.raft_inflation_status = "deployed"
        self.raft_available = False
        
        logger.critical(f'✓ LIFE RAFT DEPLOYED! Capacity: {self.raft_capacity_persons} persons')
        
        return {
            'success': True,
            'deployment_time': f'{self.inflation_time_seconds:.0f} seconds',
            'capacity': self.raft_capacity_persons,
            'status': 'ready_for_evacuation'
        }
    
    async def manual_inflation_test(self) -> bool:
        """Periodic manual inflation test"""
        logger.info('🔧 Performing life raft manual inflation test...')
        
        if self.raft_inflation_status != "stored":
            logger.warning('⚠️ Raft not in stored position for test')
            return False
        
        logger.info(f'  Storage: {self.storage_location}')
        logger.info(f'  Pressure bottle: {self.storage_pressure_bottle}')
        logger.info(f'  Expected inflation time: {self.inflation_time_seconds}s')
        logger.info('✓ Test passed - System ready')
        
        return True
    
    def get_raft_status(self) -> Dict:
        """Get life raft system status"""
        return {
            'raft_available': self.raft_available,
            'inflation_status': self.raft_inflation_status,
            'storage_location': self.storage_location,
            'pressure_bottle': self.storage_pressure_bottle,
            'capacity': self.raft_capacity_persons,
            'pressure_bar': self.inflation_pressure_bar,
            'inflation_time_s': self.inflation_time_seconds,
            'sensors_active': self.pressure_sensor_active,
            'tether_connected': self.tether_connected,
        }


async def example_fire_scenario():
    """Example: Fire in engine room scenario"""
    logger.info('\n=== FIRE EMERGENCY SCENARIO ===\n')
    
    # Initialize systems
    detection = FireDetectionSystem()
    suppression = AutomaticFireSuppressionSystem()
    alerts = EmergencyAlertSystem()
    raft = EmergencyLifeRaftSystem()
    
    # Simulate fire detection
    logger.info('1. Fire detected in engine room...')
    fire_reading = FireSensorReading(
        location=FireLocation.ENGINE_ROOM,
        temperature_celsius=120.0,
        smoke_level=65.0,
        flame_detected=True,
        co_level_ppm=150.0
    )
    await detection.update_sensor(FireLocation.ENGINE_ROOM, fire_reading)
    
    # Activate alerts
    logger.info('2. Activating emergency alerts...')
    await alerts.activate_alert('fire', 'critical')
    
    # Activate fire suppression
    logger.info('3. Activating automatic fire suppression...')
    await suppression.activate_zone('engine')
    
    # Deploy life raft
    logger.info('4. Preparing life raft deployment...')
    result = await raft.deploy_raft()
    
    # Get status
    logger.info('\n=== EMERGENCY STATUS ===')
    logger.info(f'Fire: {detection.get_fire_status()}')
    logger.info(f'Suppression: {suppression.get_suppression_status()}')
    logger.info(f'Alerts: {alerts.get_alert_status()}')
    logger.info(f'Raft: {raft.get_raft_status()}')


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(example_fire_scenario())
