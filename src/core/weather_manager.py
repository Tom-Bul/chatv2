"""
Weather system implementation.
Handles weather generation, transitions, and effects.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum, auto
import random
import logging
import json
from typing import Dict, List, Optional, Tuple, Any

from .abstractions.base import IWeather, IModifier
from .event_system import publish_event, WeatherEvent
from .modifiers import create_modifier

# Set up logging
logging.basicConfig(
    filename='game.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WeatherType(Enum):
    """Types of weather in the game."""
    CLEAR = auto()
    CLOUDY = auto()
    RAINY = auto()
    STORMY = auto()
    SNOWY = auto()
    HOT = auto()

class Weather(IWeather):
    """Implementation of a weather state."""
    def __init__(self,
                 weather_type: WeatherType,
                 intensity: float,
                 duration: timedelta,
                 start_time: datetime):
        self._type = weather_type
        self._intensity = max(0.0, min(1.0, intensity))
        self._duration = duration
        self._start_time = start_time
        self._effects = self._initialize_effects()
    
    @property
    def type(self) -> str:
        return self._type.name
    
    @property
    def intensity(self) -> float:
        return self._intensity
    
    @property
    def end_time(self) -> datetime:
        return self._start_time + self._duration
    
    @property
    def is_active(self) -> bool:
        return datetime.now() < self.end_time
    
    def affect(self, target: Any) -> None:
        """Apply weather effects to a target."""
        if hasattr(target, 'apply_weather_effects'):
            effects = self._get_current_effects()
            target.apply_weather_effects(self.type, effects)
    
    def combine(self, other: 'IWeather') -> 'IWeather':
        """Combine this weather with another."""
        if not isinstance(other, Weather):
            raise ValueError(f"Cannot combine with non-Weather object: {type(other)}")
        
        # Create transition weather
        intensity = (self._intensity + other.intensity) / 2
        duration = min(self._duration, other._duration)
        
        return Weather(
            self._type,
            intensity,
            duration,
            self._start_time
        )
    
    def _initialize_effects(self) -> Dict[str, float]:
        """Initialize base effects for this weather type."""
        base_effects = {
            WeatherType.CLEAR: {
                "task_speed": 1.0,
                "resource_rate": 1.0,
                "tool_wear": 1.0,
                "energy_cost": 1.0
            },
            WeatherType.CLOUDY: {
                "task_speed": 0.9,
                "resource_rate": 0.9,
                "tool_wear": 1.0,
                "energy_cost": 1.1
            },
            WeatherType.RAINY: {
                "task_speed": 0.7,
                "resource_rate": 0.8,
                "tool_wear": 1.2,
                "energy_cost": 1.3
            },
            WeatherType.STORMY: {
                "task_speed": 0.5,
                "resource_rate": 0.6,
                "tool_wear": 1.5,
                "energy_cost": 1.5
            },
            WeatherType.SNOWY: {
                "task_speed": 0.6,
                "resource_rate": 0.7,
                "tool_wear": 1.3,
                "energy_cost": 1.4
            },
            WeatherType.HOT: {
                "task_speed": 0.8,
                "resource_rate": 0.9,
                "tool_wear": 1.1,
                "energy_cost": 1.3
            }
        }
        return base_effects[self._type]
    
    def _get_current_effects(self) -> Dict[str, float]:
        """Get current weather effects with intensity applied."""
        effects = self._effects.copy()
        
        # Apply intensity
        for key in effects:
            if effects[key] < 1.0:
                effects[key] = 1.0 - ((1.0 - effects[key]) * self._intensity)
            else:
                effects[key] = 1.0 + ((effects[key] - 1.0) * self._intensity)
        
        return effects
    
    def to_dict(self) -> dict:
        """Convert weather to dictionary for saving."""
        return {
            "type": self._type.name,
            "intensity": self._intensity,
            "duration_seconds": self._duration.total_seconds(),
            "start_time": self._start_time.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Weather':
        """Create weather from dictionary."""
        return cls(
            weather_type=WeatherType[data["type"]],
            intensity=data["intensity"],
            duration=timedelta(seconds=data["duration_seconds"]),
            start_time=datetime.fromisoformat(data["start_time"])
        )

class WeatherManager:
    """Manages weather generation and transitions."""
    def __init__(self):
        self._current_weather: Optional[Weather] = None
        self._next_weather: Optional[Weather] = None
        self._transition_progress: float = 0.0  # 0.0 to 1.0
        self._seasonal_patterns = self._initialize_patterns()
    
    def _initialize_patterns(self) -> Dict[str, List[Tuple[WeatherType, float]]]:
        """Initialize seasonal weather patterns."""
        return {
            "SPRING": [
                (WeatherType.CLEAR, 0.3),
                (WeatherType.CLOUDY, 0.3),
                (WeatherType.RAINY, 0.3),
                (WeatherType.STORMY, 0.1)
            ],
            "SUMMER": [
                (WeatherType.CLEAR, 0.4),
                (WeatherType.HOT, 0.3),
                (WeatherType.CLOUDY, 0.2),
                (WeatherType.STORMY, 0.1)
            ],
            "FALL": [
                (WeatherType.CLOUDY, 0.4),
                (WeatherType.RAINY, 0.3),
                (WeatherType.CLEAR, 0.2),
                (WeatherType.STORMY, 0.1)
            ],
            "WINTER": [
                (WeatherType.SNOWY, 0.4),
                (WeatherType.CLOUDY, 0.3),
                (WeatherType.CLEAR, 0.2),
                (WeatherType.STORMY, 0.1)
            ]
        }
    
    def update(self, time_passed: timedelta, season: str) -> None:
        """Update weather state."""
        current_time = datetime.now()
        
        # Check if we need new weather
        if not self._current_weather or not self._current_weather.is_active:
            if self._next_weather:
                old_weather = self._current_weather
                self._current_weather = self._next_weather
                self._next_weather = None
                self._transition_progress = 0.0
                
                publish_event(WeatherEvent(
                    weather_type=self._current_weather.type,
                    intensity=self._current_weather.intensity,
                    affected_objects=[]
                ))
                
                logger.info(f"Weather changed from {old_weather.type if old_weather else 'None'} to {self._current_weather.type}")
            else:
                self._generate_weather(current_time, season)
        
        # Update transition if we have next weather
        if self._next_weather and self._current_weather:
            time_to_change = (self._current_weather.end_time - current_time).total_seconds()
            if time_to_change > 0:
                self._transition_progress = max(0.0, min(1.0, 1.0 - (time_to_change / 300)))  # 5 minutes transition
        
        # Generate next weather if needed
        if not self._next_weather and self._current_weather:
            time_to_end = (self._current_weather.end_time - current_time).total_seconds()
            if time_to_end < 300:  # 5 minutes before current weather ends
                self._generate_next_weather(current_time, season)
    
    def _generate_weather(self, current_time: datetime, season: str) -> None:
        """Generate new weather state."""
        weather_type = self._select_weather_type(season)
        duration = self._generate_duration(weather_type)
        intensity = random.uniform(0.5, 1.0)
        
        self._current_weather = Weather(
            weather_type=weather_type,
            intensity=intensity,
            duration=duration,
            start_time=current_time
        )
        
        publish_event(WeatherEvent(
            weather_type=self._current_weather.type,
            intensity=self._current_weather.intensity,
            affected_objects=[]
        ))
        
        logger.info(f"Generated new weather: {weather_type.name}")
    
    def _generate_next_weather(self, current_time: datetime, season: str) -> None:
        """Generate next weather state."""
        weather_type = self._select_weather_type(season)
        duration = self._generate_duration(weather_type)
        intensity = random.uniform(0.5, 1.0)
        
        self._next_weather = Weather(
            weather_type=weather_type,
            intensity=intensity,
            duration=duration,
            start_time=self._current_weather.end_time if self._current_weather else current_time
        )
        logger.info(f"Generated next weather: {weather_type.name}")
    
    def _select_weather_type(self, season: str) -> WeatherType:
        """Select weather type based on season."""
        if season not in self._seasonal_patterns:
            return WeatherType.CLEAR
        
        patterns = self._seasonal_patterns[season]
        total = sum(weight for _, weight in patterns)
        r = random.uniform(0, total)
        
        cumulative = 0
        for weather_type, weight in patterns:
            cumulative += weight
            if r <= cumulative:
                return weather_type
        
        return patterns[0][0]
    
    def _generate_duration(self, weather_type: WeatherType) -> timedelta:
        """Generate weather duration based on type."""
        if weather_type in [WeatherType.STORMY, WeatherType.HOT]:
            # Extreme weather lasts shorter
            minutes = random.randint(30, 120)
        else:
            # Normal weather lasts longer
            minutes = random.randint(60, 240)
        
        return timedelta(minutes=minutes)
    
    def get_current_weather(self) -> Optional[Weather]:
        """Get current weather state."""
        return self._current_weather
    
    def get_weather_description(self) -> Tuple[str, str]:
        """Get current weather description and intensity level."""
        if not self._current_weather:
            return "Clear", "Mild"
        
        weather_name = self._current_weather.type
        
        if self._current_weather.intensity < 0.3:
            intensity = "Mild"
        elif self._current_weather.intensity < 0.6:
            intensity = "Moderate"
        elif self._current_weather.intensity < 0.8:
            intensity = "Strong"
        else:
            intensity = "Severe"
        
        return weather_name, intensity
    
    def save_state(self) -> dict:
        """Save weather manager state."""
        return {
            "current_weather": self._current_weather.to_dict() if self._current_weather else None,
            "next_weather": self._next_weather.to_dict() if self._next_weather else None,
            "transition_progress": self._transition_progress
        }
    
    def load_state(self, state: dict) -> None:
        """Load weather manager state."""
        if state.get("current_weather"):
            self._current_weather = Weather.from_dict(state["current_weather"])
        
        if state.get("next_weather"):
            self._next_weather = Weather.from_dict(state["next_weather"])
        
        self._transition_progress = state.get("transition_progress", 0.0)
        logger.info("Weather manager state loaded") 