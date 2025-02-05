"""
Core abstractions for the game system.
Defines the base interfaces and types that all components must implement.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Dict, Generic, List, Optional, Protocol, Tuple, Type, TypeVar, Union

# Type variables for generic types
T = TypeVar('T')
S = TypeVar('S')

class Identifier(Protocol):
    """Protocol for objects that can be uniquely identified."""
    @property
    def id(self) -> str: ...

class Modifiable(Protocol):
    """Protocol for objects that can be modified."""
    def apply_modifier(self, modifier: 'IModifier') -> 'Modifiable': ...

class IModifier(Protocol):
    """Protocol for modifier objects that can change other objects."""
    def modify(self, target: Any) -> Any: ...
    def combine(self, other: 'IModifier') -> 'IModifier': ...

class IResource(Identifier, Modifiable, Protocol):
    """Protocol for resource objects."""
    @property
    def quantity(self) -> float: ...
    
    @property
    def quality(self) -> float: ...
    
    @property
    def type(self) -> str: ...
    
    def transform(self, modifier: IModifier) -> 'IResource': ...
    def combine(self, other: 'IResource') -> 'IResource': ...
    def split(self, amount: float) -> Tuple['IResource', 'IResource']: ...

class ITask(Identifier, Modifiable, Protocol):
    """Protocol for task objects."""
    @property
    def status(self) -> str: ...
    
    @property
    def progress(self) -> float: ...
    
    def check_prerequisites(self) -> bool: ...
    def apply_effects(self) -> None: ...
    def update(self, delta_time: float) -> None: ...

class IWeather(Protocol):
    """Protocol for weather objects."""
    @property
    def type(self) -> str: ...
    
    @property
    def intensity(self) -> float: ...
    
    def affect(self, target: Any) -> None: ...
    def combine(self, other: 'IWeather') -> 'IWeather': ...

class ITimeManager(Protocol):
    """Protocol for time management."""
    @property
    def current_time(self) -> datetime: ...
    
    @property
    def time_scale(self) -> float: ...
    
    def update(self, delta_time: float) -> None: ...
    def schedule(self, when: datetime, callback: Callable[[], None]) -> None: ...

class IGameState(Protocol):
    """Protocol for game state management."""
    def save(self) -> Dict[str, Any]: ...
    def load(self, data: Dict[str, Any]) -> None: ...
    def update(self, delta_time: float) -> None: ...

class Event(Generic[T]):
    """Base class for all events in the system."""
    def __init__(self, type_: str, data: T):
        self.type = type_
        self.data = data
        self.timestamp = datetime.now()

class EventBus:
    """Central event management system."""
    def __init__(self):
        self._handlers: Dict[str, List[Callable[[Event], None]]] = {}
    
    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """Subscribe to an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def unsubscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """Unsubscribe from an event type."""
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)
    
    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        if event.type in self._handlers:
            for handler in self._handlers[event.type]:
                handler(event)

class IPlugin(Protocol):
    """Protocol for plugin objects."""
    @property
    def name(self) -> str: ...
    
    @property
    def version(self) -> str: ...
    
    def initialize(self) -> None: ...
    def get_extensions(self) -> List['IExtension']: ...

class IExtension(Protocol):
    """Protocol for extension points."""
    @property
    def point_id(self) -> str: ...
    
    def initialize(self) -> None: ...

class PluginManager:
    """Manages plugin loading and registration."""
    def __init__(self):
        self._plugins: Dict[str, IPlugin] = {}
        self._extensions: Dict[str, List[IExtension]] = {}
    
    def register_plugin(self, plugin: IPlugin) -> None:
        """Register a new plugin."""
        self._plugins[plugin.name] = plugin
        plugin.initialize()
        for extension in plugin.get_extensions():
            if extension.point_id not in self._extensions:
                self._extensions[extension.point_id] = []
            self._extensions[extension.point_id].append(extension)
            extension.initialize()
    
    def get_extensions(self, point_id: str) -> List[IExtension]:
        """Get all extensions for a specific extension point."""
        return self._extensions.get(point_id, []) 