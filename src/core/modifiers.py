"""
Modifier system implementation.
Provides base modifier types and a registry for managing modifiers.
"""

from typing import Any, Dict, List, Optional, Type, TypeVar
from abc import ABC, abstractmethod

from .abstractions.base import IModifier
from .event_system import publish_event, GameStateEvent

T = TypeVar('T')

class BaseModifier(IModifier, ABC):
    """Base class for all modifiers."""
    def __init__(self, modifier_type: str, strength: float = 1.0):
        self.type = modifier_type
        self.strength = strength
    
    @abstractmethod
    def modify(self, target: Any) -> Any:
        """Apply the modification to the target."""
        pass
    
    def combine(self, other: 'IModifier') -> 'IModifier':
        """Combine this modifier with another of the same type."""
        if not isinstance(other, type(self)):
            raise ValueError(f"Cannot combine modifiers of different types: {type(self)} and {type(other)}")
        return type(self)(self.type, self.strength + other.strength)

class MultiplyModifier(BaseModifier):
    """Modifier that multiplies a numeric value."""
    def modify(self, target: float) -> float:
        return target * self.strength

class AddModifier(BaseModifier):
    """Modifier that adds to a numeric value."""
    def modify(self, target: float) -> float:
        return target + self.strength

class QualityModifier(BaseModifier):
    """Modifier that affects resource quality."""
    def modify(self, target: Any) -> Any:
        if hasattr(target, 'quality'):
            target.quality = max(0.0, min(1.0, target.quality * self.strength))
        return target

class WeatherModifier(BaseModifier):
    """Modifier that applies weather effects."""
    def __init__(self, weather_type: str, intensity: float):
        super().__init__("weather", intensity)
        self.weather_type = weather_type
    
    def modify(self, target: Any) -> Any:
        # Apply weather-specific modifications
        if hasattr(target, 'apply_weather'):
            target.apply_weather(self.weather_type, self.strength)
        return target

class TimeModifier(BaseModifier):
    """Modifier that applies time-based effects."""
    def __init__(self, time_factor: float, day_phase: str):
        super().__init__("time", time_factor)
        self.day_phase = day_phase
    
    def modify(self, target: Any) -> Any:
        # Apply time-based modifications
        if hasattr(target, 'apply_time_effect'):
            target.apply_time_effect(self.day_phase, self.strength)
        return target

class ModifierRegistry:
    """Registry for managing and creating modifiers."""
    def __init__(self):
        self._modifiers: Dict[str, Type[BaseModifier]] = {}
    
    def register_modifier(self, modifier_type: str, modifier_class: Type[BaseModifier]) -> None:
        """Register a new modifier type."""
        self._modifiers[modifier_type] = modifier_class
        publish_event(GameStateEvent(
            action="register_modifier",
            state_type="modifier_registry",
            details={"modifier_type": modifier_type}
        ))
    
    def create_modifier(self, modifier_type: str, **kwargs) -> BaseModifier:
        """Create a new modifier instance."""
        if modifier_type not in self._modifiers:
            raise ValueError(f"Unknown modifier type: {modifier_type}")
        return self._modifiers[modifier_type](**kwargs)
    
    def get_available_modifiers(self) -> List[str]:
        """Get a list of all registered modifier types."""
        return list(self._modifiers.keys())

# Global modifier registry instance
modifier_registry = ModifierRegistry()

# Register built-in modifiers
modifier_registry.register_modifier("multiply", MultiplyModifier)
modifier_registry.register_modifier("add", AddModifier)
modifier_registry.register_modifier("quality", QualityModifier)
modifier_registry.register_modifier("weather", WeatherModifier)
modifier_registry.register_modifier("time", TimeModifier)

def create_modifier(modifier_type: str, **kwargs) -> BaseModifier:
    """Create a new modifier instance from the global registry."""
    return modifier_registry.create_modifier(modifier_type, **kwargs)

def register_modifier(modifier_type: str, modifier_class: Type[BaseModifier]) -> None:
    """Register a new modifier type in the global registry."""
    modifier_registry.register_modifier(modifier_type, modifier_class) 