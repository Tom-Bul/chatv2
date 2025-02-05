"""
Event system implementation.
Provides concrete event types and the central event bus for the game.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, TypeVar, Generic

from .abstractions.base import Event, EventBus

T = TypeVar('T')

class ResourceEvent(Event[Dict[str, Any]]):
    """Event for resource-related changes."""
    def __init__(self, 
                 resource_id: str,
                 action: str,
                 old_value: Optional[float] = None,
                 new_value: Optional[float] = None,
                 quality_change: Optional[float] = None):
        super().__init__("resource", {
            "resource_id": resource_id,
            "action": action,
            "old_value": old_value,
            "new_value": new_value,
            "quality_change": quality_change
        })

class TaskEvent(Event[Dict[str, Any]]):
    """Event for task-related changes."""
    def __init__(self,
                 task_id: str,
                 action: str,
                 old_status: Optional[str] = None,
                 new_status: Optional[str] = None,
                 progress: Optional[float] = None):
        super().__init__("task", {
            "task_id": task_id,
            "action": action,
            "old_status": old_status,
            "new_status": new_status,
            "progress": progress
        })

class WeatherEvent(Event[Dict[str, Any]]):
    """Event for weather-related changes."""
    def __init__(self,
                 weather_type: str,
                 intensity: float,
                 affected_objects: List[str]):
        super().__init__("weather", {
            "type": weather_type,
            "intensity": intensity,
            "affected_objects": affected_objects
        })

class TimeEvent(Event[Dict[str, Any]]):
    """Event for time-related changes."""
    def __init__(self,
                 current_time: datetime,
                 time_scale: float,
                 day_phase: str):
        super().__init__("time", {
            "current_time": current_time,
            "time_scale": time_scale,
            "day_phase": day_phase
        })

class GameStateEvent(Event[Dict[str, Any]]):
    """Event for game state changes."""
    def __init__(self,
                 action: str,
                 state_type: str,
                 details: Dict[str, Any]):
        super().__init__("game_state", {
            "action": action,
            "state_type": state_type,
            "details": details
        })

# Global event bus instance
event_bus = EventBus()

def publish_event(event: Event) -> None:
    """Publish an event to the global event bus."""
    event_bus.publish(event)

def subscribe_to_event(event_type: str, handler: callable) -> None:
    """Subscribe to events of a specific type."""
    event_bus.subscribe(event_type, handler)

def unsubscribe_from_event(event_type: str, handler: callable) -> None:
    """Unsubscribe from events of a specific type."""
    event_bus.unsubscribe(event_type, handler) 