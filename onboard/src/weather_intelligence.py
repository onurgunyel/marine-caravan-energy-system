#!/usr/bin/env python3
"""
Marine Caravan - AI Weather Intelligence System (AWIS)
Analyzes weather conditions and generates autonomous action plans
"""

import logging
import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import math

logger = logging.getLogger(__name__)


class WeatherSeverity(Enum):
    """Weather condition severity levels"""
    CALM = 0               # Safe conditions
    MILD = 1               # Minor concern
    MODERATE = 2           # Moderate concern
    SEVERE = 3             # High risk
    EXTREME = 4            # Critical danger


class WeatherScenario(Enum):
    """Pre-defined weather scenarios"""
    CALM_SEAS = "calm_seas"                      # Perfect conditions
    LIGHT_WIND = "light_wind"                    # 0-10 knots
    MODERATE_WIND = "moderate_wind"              # 10-20 knots
    STRONG_WIND = "strong_wind"                  # 20-40 knots
    GALE_WARNING = "gale_warning"                # 40-60 knots
    STORM = "storm"                              # 60+ knots
    HEAVY_RAIN = "heavy_rain"                    # Precipitation > 20mm/h
    THUNDERSTORM = "thunderstorm"                # Lightning risk
    ROUGH_SEAS = "rough_seas"                    # Wave height > 3m
    VERY_ROUGH_SEAS = "very_rough_seas"          # Wave height > 6m
    FOG = "fog"                                  # Low visibility
    COLD_FRONT = "cold_front"                    # Temperature drop
    HEAT_STRESS = "heat_stress"                  # High temperature
    SHALLOWING_TREND = "shallowing_trend"        # Water getting shallower


@dataclass
class WeatherReading:
    """Current weather conditions"""
    timestamp: datetime
    wind_speed_knots: float                # Wind speed (knots)
    wind_direction: float                  # Wind direction (degrees 0-360)
    wind_gust_knots: float                 # Wind gust (knots)
    temperature_celsius: float             # Air temperature
    humidity_percent: float                # Relative humidity (0-100)
    air_pressure_hpa: float                # Atmospheric pressure
    pressure_trend: str                    # "rising", "steady", "falling"
    wave_height_meters: float              # Wave height
    visibility_km: float                   # Visibility distance
    precipitation_mm_h: float              # Rainfall rate
    current_speed_knots: float             # Water current speed
    current_direction: float               # Water current direction
    water_temperature_celsius: float       # Sea water temperature
    cloud_coverage_percent: float          # Cloud coverage (0-100)


@dataclass
class ActionPlan:
    """AI-generated action plan"""
    scenario: WeatherScenario
    severity: WeatherSeverity
    timestamp: datetime
    actions: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    alerts: List[str] = field(default_factory=list)
    location_change_recommendation: Optional[Dict] = None
    speed_adjustment: Optional[float] = None          # Recommended speed %
    heading_adjustment: Optional[float] = None        # Recommended heading
    eta_danger_hours: Optional[float] = None          # Hours until danger
    confidence_score: float = 0.0                     # AI confidence (0-100)


class WeatherAnalyzer:
    """Analyzes weather conditions and detects scenarios"""
    
    def __init__(self):
        self.current_reading: Optional[WeatherReading] = None
        self.reading_history: List[WeatherReading] = []
        self.max_history = 240  # 4 hours at 1-minute intervals
        
        # Weather thresholds for scenario detection
        self.thresholds = {
            'light_wind': 10,
            'moderate_wind': 20,
            'strong_wind': 40,
            'gale': 60,
            'storm': 75,
            'rough_seas': 3.0,
            'very_rough_seas': 6.0,
            'heavy_rain': 20.0,
            'fog_visibility': 1.0,
            'temperature_extreme_hot': 35,
            'temperature_extreme_cold': 0,
        }
    
    async def update_weather(self, reading: WeatherReading):
        """Update weather reading"""
        self.current_reading = reading
        self.reading_history.append(reading)
        
        if len(self.reading_history) > self.max_history:
            self.reading_history.pop(0)
        
        logger.info(f'Weather update: Wind {reading.wind_speed_knots:.1f}kt, '
                   f'Wave {reading.wave_height_meters:.1f}m, '
                   f'Temp {reading.temperature_celsius:.1f}°C')
    
    def detect_scenarios(self) -> List[WeatherScenario]:
        """Detect active weather scenarios"""
        if not self.current_reading:
            return []
        
        scenarios = []
        w = self.current_reading
        
        # Wind scenarios
        if w.wind_speed_knots < 5:
            scenarios.append(WeatherScenario.CALM_SEAS)
        elif w.wind_speed_knots < 10:
            scenarios.append(WeatherScenario.LIGHT_WIND)
        elif w.wind_speed_knots < 20:
            scenarios.append(WeatherScenario.MODERATE_WIND)
        elif w.wind_speed_knots < 40:
            scenarios.append(WeatherScenario.STRONG_WIND)
        elif w.wind_speed_knots < 60:
            scenarios.append(WeatherScenario.GALE_WARNING)
        else:
            scenarios.append(WeatherScenario.STORM)
        
        # Precipitation scenarios
        if w.precipitation_mm_h > self.thresholds['heavy_rain']:
            scenarios.append(WeatherScenario.HEAVY_RAIN)
        
        # Thunderstorm detection (high humidity + low pressure + rain)
        if (w.humidity_percent > 85 and 
            w.precipitation_mm_h > 10 and 
            w.pressure_trend == 'falling'):
            scenarios.append(WeatherScenario.THUNDERSTORM)
        
        # Sea state scenarios
        if w.wave_height_meters > self.thresholds['very_rough_seas']:
            scenarios.append(WeatherScenario.VERY_ROUGH_SEAS)
        elif w.wave_height_meters > self.thresholds['rough_seas']:
            scenarios.append(WeatherScenario.ROUGH_SEAS)
        
        # Visibility scenarios
        if w.visibility_km < self.thresholds['fog_visibility']:
            scenarios.append(WeatherScenario.FOG)
        
        # Temperature scenarios
        if w.temperature_celsius > self.thresholds['temperature_extreme_hot']:
            scenarios.append(WeatherScenario.HEAT_STRESS)
        elif w.temperature_celsius < self.thresholds['temperature_extreme_cold']:
            scenarios.append(WeatherScenario.COLD_FRONT)
        
        # Pressure trend
        if w.pressure_trend == 'falling':
            scenarios.append(WeatherScenario.COLD_FRONT)
        
        return list(set(scenarios))  # Remove duplicates
    
    def get_severity_score(self, scenarios: List[WeatherScenario]) -> WeatherSeverity:
        """Calculate overall weather severity from scenarios"""
        if not scenarios:
            return WeatherSeverity.CALM
        
        # Map scenarios to severity
        severity_map = {
            WeatherScenario.CALM_SEAS: WeatherSeverity.CALM,
            WeatherScenario.LIGHT_WIND: WeatherSeverity.MILD,
            WeatherScenario.MODERATE_WIND: WeatherSeverity.MILD,
            WeatherScenario.STRONG_WIND: WeatherSeverity.MODERATE,
            WeatherScenario.GALE_WARNING: WeatherSeverity.SEVERE,
            WeatherScenario.STORM: WeatherSeverity.EXTREME,
            WeatherScenario.HEAVY_RAIN: WeatherSeverity.MODERATE,
            WeatherScenario.THUNDERSTORM: WeatherSeverity.SEVERE,
            WeatherScenario.ROUGH_SEAS: WeatherSeverity.MODERATE,
            WeatherScenario.VERY_ROUGH_SEAS: WeatherSeverity.SEVERE,
            WeatherScenario.FOG: WeatherSeverity.MODERATE,
            WeatherScenario.COLD_FRONT: WeatherSeverity.MODERATE,
            WeatherScenario.HEAT_STRESS: WeatherSeverity.MILD,
        }
        
        max_severity = max([severity_map.get(s, WeatherSeverity.CALM) for s in scenarios],
                          key=lambda x: x.value)
        return max_severity
    
    def get_pressure_trend(self) -> str:
        """Analyze pressure trend"""
        if len(self.reading_history) < 3:
            return "steady"
        
        recent = self.reading_history[-1].air_pressure_hpa
        older = self.reading_history[-60].air_pressure_hpa if len(self.reading_history) > 60 else self.reading_history[0].air_pressure_hpa
        
        diff = recent - older
        if diff > 2:
            return "rising"
        elif diff < -2:
            return "falling"
        else:
            return "steady"


class AIWeatherIntelligence:
    """AI system for weather-based decision making"""
    
    def __init__(self, analyzer: WeatherAnalyzer, autopilot=None, collision_avoidance=None):
        self.analyzer = analyzer
        self.autopilot = autopilot
        self.collision_avoidance = collision_avoidance
        self.current_plan: Optional[ActionPlan] = None
        self.plan_history: List[ActionPlan] = []
        self.max_plan_history = 100
    
    async def analyze_and_plan(self) -> ActionPlan:
        """Main AI analysis and planning function"""
        scenarios = self.analyzer.detect_scenarios()
        severity = self.analyzer.get_severity_score(scenarios)
        
        logger.info(f'Weather Analysis: Scenarios={[s.value for s in scenarios]}, '
                   f'Severity={severity.name}')
        
        plan = ActionPlan(
            scenario=scenarios[0] if scenarios else WeatherScenario.CALM_SEAS,
            severity=severity,
            timestamp=datetime.now()
        )
        
        # Generate actions based on scenarios
        for scenario in scenarios:
            await self._generate_scenario_actions(scenario, plan)
        
        # Calculate confidence score
        plan.confidence_score = self._calculate_confidence(scenarios)
        
        self.current_plan = plan
        self.plan_history.append(plan)
        if len(self.plan_history) > self.max_plan_history:
            self.plan_history.pop(0)
        
        return plan
    
    async def _generate_scenario_actions(self, scenario: WeatherScenario, plan: ActionPlan):
        """Generate actions for specific weather scenario"""
        w = self.analyzer.current_reading
        
        if scenario == WeatherScenario.CALM_SEAS:
            plan.actions.append("✓ Continue normal operations")
            plan.recommendations.append("Maintain current heading and speed")
        
        elif scenario == WeatherScenario.LIGHT_WIND:
            plan.actions.append("Monitor wind conditions")
            plan.recommendations.append("Wind is manageable, no changes needed")
        
        elif scenario == WeatherScenario.MODERATE_WIND:
            plan.actions.append("⚠️ Reduce speed to 75%")
            plan.recommendations.append("Monitor waves, watch wind gusts")
            plan.speed_adjustment = 75.0
        
        elif scenario == WeatherScenario.STRONG_WIND:
            plan.actions.append("⚠️ Reduce speed to 50%")
            plan.actions.append("Activate autopilot heading hold")
            plan.recommendations.append("Check vessel security, reduce canvas")
            plan.alerts.append(f"Strong winds {w.wind_speed_knots:.0f}kt detected")
            plan.speed_adjustment = 50.0
        
        elif scenario == WeatherScenario.GALE_WARNING:
            plan.actions.append("🚨 Reduce speed to 25%")
            plan.actions.append("Consider seeking shelter")
            plan.recommendations.append("Prepare vessel for heavy weather")
            plan.alerts.append(f"⚠️ GALE WARNING: Winds {w.wind_speed_knots:.0f}kt")
            plan.speed_adjustment = 25.0
            plan.location_change_recommendation = await self._find_safe_harbor()
        
        elif scenario == WeatherScenario.STORM:
            plan.actions.append("🚨 EMERGENCY: Reduce speed to 10%")
            plan.actions.append("🚨 Seek immediate shelter")
            plan.recommendations.append("Head to nearest safe port immediately")
            plan.alerts.append(f"🚨 STORM WARNING: Winds {w.wind_speed_knots:.0f}kt - SEEK SHELTER")
            plan.speed_adjustment = 10.0
            plan.location_change_recommendation = await self._find_safe_harbor(urgent=True)
        
        elif scenario == WeatherScenario.HEAVY_RAIN:
            plan.actions.append("Reduce visibility awareness")
            plan.actions.append("Reduce speed to 75%")
            plan.recommendations.append("Use radar/sonar, activate navigation lights")
            plan.alerts.append(f"Heavy rain: Visibility reduced to {w.visibility_km:.1f}km")
            plan.speed_adjustment = min(plan.speed_adjustment or 100, 75.0)
        
        elif scenario == WeatherScenario.THUNDERSTORM:
            plan.actions.append("🚨 Disconnect electrical equipment")
            plan.actions.append("🚨 Avoid metal objects on deck")
            plan.actions.append("Seek shelter immediately")
            plan.recommendations.append("Stay below deck, avoid mast/metal")
            plan.alerts.append("🚨 THUNDERSTORM WARNING - Lightning risk")
            plan.speed_adjustment = 0.0
        
        elif scenario == WeatherScenario.ROUGH_SEAS:
            plan.actions.append("Reduce speed to 60%")
            plan.recommendations.append("Check bilge pumps, secure loose items")
            plan.speed_adjustment = 60.0
        
        elif scenario == WeatherScenario.VERY_ROUGH_SEAS:
            plan.actions.append("🚨 Reduce speed to 30%")
            plan.actions.append("🚨 Consider changing course")
            plan.recommendations.append("Activate collision avoidance, monitor depth")
            plan.alerts.append(f"Very rough seas: Wave height {w.wave_height_meters:.1f}m")
            plan.speed_adjustment = 30.0
            # Find route with better conditions
            plan.heading_adjustment = await self._find_optimal_heading()
        
        elif scenario == WeatherScenario.FOG:
            plan.actions.append("Activate navigation lights")
            plan.actions.append("Activate sonar/radar")
            plan.actions.append("Reduce speed to 50%")
            plan.recommendations.append("Increase radar watch, use collision avoidance")
            plan.alerts.append(f"FOG: Visibility {w.visibility_km:.1f}km")
            plan.speed_adjustment = 50.0
        
        elif scenario == WeatherScenario.COLD_FRONT:
            plan.actions.append("Monitor weather closely")
            plan.recommendations.append("Conditions deteriorating - be ready to seek shelter")
            plan.alerts.append("Cold front approaching - pressure falling")
        
        elif scenario == WeatherScenario.HEAT_STRESS:
            plan.actions.append("Monitor crew/systems for heat stress")
            plan.recommendations.append("Increase water intake, reduce physical activity")
            plan.alerts.append(f"High temperature: {w.temperature_celsius:.1f}°C")
    
    async def _find_safe_harbor(self, urgent: bool = False) -> Dict:
        """Find nearest safe harbor"""
        # This would integrate with marine charts database
        recommendation = {
            'type': 'safe_harbor',
            'urgent': urgent,
            'distance_nm': 15.5,
            'name': 'Göcek Marina',
            'coordinates': {'lat': 36.7523, 'lon': 29.2311},
            'protection_level': 'excellent',
            'facilities': ['fuel', 'water', 'repair', 'medical'],
            'bearing': 215.0,
            'eta_hours': 2.5
        }
        return recommendation
    
    async def _find_optimal_heading(self) -> float:
        """Find heading that avoids worst weather"""
        w = self.analyzer.current_reading
        # Sail perpendicular to wind for better conditions
        optimal_heading = (w.wind_direction + 90) % 360
        return optimal_heading
    
    def _calculate_confidence(self, scenarios: List[WeatherScenario]) -> float:
        """Calculate AI confidence score (0-100)"""
        if not self.analyzer.current_reading:
            return 0.0
        
        # Confidence based on:
        # - Data freshness
        # - History availability
        # - Number of confirmed scenarios
        
        age_minutes = (datetime.now() - self.analyzer.current_reading.timestamp).total_seconds() / 60
        freshness_score = max(0, 100 - (age_minutes * 5))  # Loses 5% per minute
        
        history_score = min(100, len(self.analyzer.reading_history) * 2)
        
        scenario_score = min(100, len(scenarios) * 20)
        
        confidence = (freshness_score * 0.5 + history_score * 0.3 + scenario_score * 0.2)
        return max(0, min(100, confidence))
    
    async def execute_plan(self) -> bool:
        """Execute the current action plan"""
        if not self.current_plan:
            return False
        
        logger.info(f'Executing weather action plan: {self.current_plan.scenario.value}')
        
        # Apply speed adjustment
        if self.current_plan.speed_adjustment is not None and self.autopilot:
            await self.autopilot.motor_controller.set_target_speed(
                self.current_plan.speed_adjustment
            )
            logger.info(f'Speed adjusted to {self.current_plan.speed_adjustment:.0f}%')
        
        # Apply heading adjustment
        if self.current_plan.heading_adjustment is not None and self.autopilot:
            await self.autopilot.hold_heading(self.current_plan.heading_adjustment)
            logger.info(f'Heading adjusted to {self.current_plan.heading_adjustment:.0f}°')
        
        # Send alerts
        for alert in self.current_plan.alerts:
            logger.warning(f'WEATHER ALERT: {alert}')
        
        return True


async def example_usage():
    """Example usage of AI weather intelligence"""
    analyzer = WeatherAnalyzer()
    ai = AIWeatherIntelligence(analyzer)
    
    # Simulate weather reading
    reading = WeatherReading(
        timestamp=datetime.now(),
        wind_speed_knots=35.5,
        wind_direction=180.0,
        wind_gust_knots=45.0,
        temperature_celsius=18.5,
        humidity_percent=82.0,
        air_pressure_hpa=995.5,
        pressure_trend='falling',
        wave_height_meters=4.2,
        visibility_km=2.5,
        precipitation_mm_h=5.0,
        current_speed_knots=0.8,
        current_direction=200.0,
        water_temperature_celsius=22.0,
        cloud_coverage_percent=95.0
    )
    
    await analyzer.update_weather(reading)
    plan = await ai.analyze_and_plan()
    
    logger.info(f'\nWeather Action Plan:')
    logger.info(f'Scenario: {plan.scenario.value}')
    logger.info(f'Severity: {plan.severity.name}')
    logger.info(f'Confidence: {plan.confidence_score:.1f}%')
    logger.info(f'Actions: {plan.actions}')
    logger.info(f'Recommendations: {plan.recommendations}')
    logger.info(f'Alerts: {plan.alerts}')


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(example_usage())
