"""
Tests for core abstractions.
"""

import unittest
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import Mock

from src.core.abstractions.base import (
    IResource, ITask, IWeather, IModifier,
    Event, EventBus, IPlugin, IExtension
)

class TestEvent(unittest.TestCase):
    """Test the Event class."""
    def test_event_creation(self):
        """Test creating an event."""
        data = {"test": "data"}
        event = Event("test_type", data)
        
        self.assertEqual(event.type, "test_type")
        self.assertEqual(event.data, data)
        self.assertIsInstance(event.timestamp, datetime)
    
    def test_event_with_different_data_types(self):
        """Test event creation with different data types."""
        test_cases = [
            ("string_data", "test string"),
            ("int_data", 42),
            ("list_data", [1, 2, 3]),
            ("dict_data", {"key": "value"}),
            ("none_data", None)
        ]
        
        for type_name, data in test_cases:
            with self.subTest(type_name=type_name):
                event = Event(type_name, data)
                self.assertEqual(event.data, data)

class TestEventBus(unittest.TestCase):
    """Test the EventBus class."""
    def setUp(self):
        self.event_bus = EventBus()
        self.handler_called = False
        self.received_event = None
    
    def test_subscribe_and_publish(self):
        """Test subscribing to and publishing events."""
        def handler(event: Event):
            self.handler_called = True
            self.received_event = event
        
        self.event_bus.subscribe("test_event", handler)
        event = Event("test_event", {"data": "test"})
        self.event_bus.publish(event)
        
        self.assertTrue(self.handler_called)
        self.assertEqual(self.received_event, event)
    
    def test_unsubscribe(self):
        """Test unsubscribing from events."""
        def handler(event: Event):
            self.handler_called = True
        
        self.event_bus.subscribe("test_event", handler)
        self.event_bus.unsubscribe("test_event", handler)
        self.event_bus.publish(Event("test_event", {}))
        
        self.assertFalse(self.handler_called)
    
    def test_multiple_handlers(self):
        """Test multiple handlers for the same event type."""
        handlers_called = []
        
        def handler1(event: Event):
            handlers_called.append(1)
        
        def handler2(event: Event):
            handlers_called.append(2)
        
        self.event_bus.subscribe("test_event", handler1)
        self.event_bus.subscribe("test_event", handler2)
        self.event_bus.publish(Event("test_event", {}))
        
        self.assertEqual(handlers_called, [1, 2])

class MockResource(IResource):
    """Mock implementation of IResource for testing."""
    def __init__(self, id_: str = "test_id"):
        self._id = id_
        self._quantity = 1.0
        self._quality = 1.0
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def type(self) -> str:
        return "test_resource"
    
    @property
    def quantity(self) -> float:
        return self._quantity
    
    @property
    def quality(self) -> float:
        return self._quality
    
    def apply_modifier(self, modifier: IModifier) -> 'MockResource':
        return modifier.modify(self)
    
    def transform(self, modifier: IModifier) -> 'MockResource':
        return self.apply_modifier(modifier)
    
    def combine(self, other: 'MockResource') -> 'MockResource':
        result = MockResource(self._id)
        result._quantity = self._quantity + other._quantity
        result._quality = (self._quality + other._quality) / 2
        return result
    
    def split(self, amount: float) -> tuple['MockResource', 'MockResource']:
        if amount > self._quantity:
            raise ValueError("Cannot split more than available")
        
        split = MockResource(self._id)
        split._quantity = amount
        split._quality = self._quality
        
        remaining = MockResource(self._id)
        remaining._quantity = self._quantity - amount
        remaining._quality = self._quality
        
        return split, remaining

class MockTask(ITask):
    """Mock implementation of ITask for testing."""
    def __init__(self, id_: str = "test_id"):
        self._id = id_
        self._status = "available"
        self._progress = 0.0
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def status(self) -> str:
        return self._status
    
    @property
    def progress(self) -> float:
        return self._progress
    
    def apply_modifier(self, modifier: IModifier) -> 'MockTask':
        return modifier.modify(self)
    
    def check_prerequisites(self) -> bool:
        return True
    
    def apply_effects(self) -> None:
        pass
    
    def update(self, delta_time: float) -> None:
        self._progress = min(1.0, self._progress + delta_time)

class MockWeather(IWeather):
    """Mock implementation of IWeather for testing."""
    def __init__(self, type_: str = "clear", intensity: float = 1.0):
        self._type = type_
        self._intensity = intensity
    
    @property
    def type(self) -> str:
        return self._type
    
    @property
    def intensity(self) -> float:
        return self._intensity
    
    def affect(self, target: Any) -> None:
        if hasattr(target, 'apply_weather_effects'):
            target.apply_weather_effects(self._type, self._intensity)
    
    def combine(self, other: 'MockWeather') -> 'MockWeather':
        return MockWeather(
            self._type,
            (self._intensity + other._intensity) / 2
        )

class MockModifier(IModifier):
    """Mock implementation of IModifier for testing."""
    def __init__(self, multiplier: float = 1.0):
        self._multiplier = multiplier
    
    def modify(self, target: Any) -> Any:
        if isinstance(target, (int, float)):
            return target * self._multiplier
        return target
    
    def combine(self, other: 'MockModifier') -> 'MockModifier':
        return MockModifier(self._multiplier * other._multiplier)

class TestInterfaces(unittest.TestCase):
    """Test the core interfaces with mock implementations."""
    def setUp(self):
        self.resource = MockResource()
        self.task = MockTask()
        self.weather = MockWeather()
        self.modifier = MockModifier(2.0)
    
    def test_resource_interface(self):
        """Test the IResource interface."""
        # Test basic properties
        self.assertEqual(self.resource.id, "test_id")
        self.assertEqual(self.resource.type, "test_resource")
        self.assertEqual(self.resource.quantity, 1.0)
        self.assertEqual(self.resource.quality, 1.0)
        
        # Test combining resources
        other_resource = MockResource()
        combined = self.resource.combine(other_resource)
        self.assertEqual(combined.quantity, 2.0)
        self.assertEqual(combined.quality, 1.0)
        
        # Test splitting resources
        split, remaining = self.resource.split(0.5)
        self.assertEqual(split.quantity, 0.5)
        self.assertEqual(remaining.quantity, 0.5)
        self.assertEqual(split.quality, 1.0)
        self.assertEqual(remaining.quality, 1.0)
    
    def test_task_interface(self):
        """Test the ITask interface."""
        # Test basic properties
        self.assertEqual(self.task.id, "test_id")
        self.assertEqual(self.task.status, "available")
        self.assertEqual(self.task.progress, 0.0)
        
        # Test updating progress
        self.task.update(0.5)
        self.assertEqual(self.task.progress, 0.5)
        
        # Test prerequisites and effects
        self.assertTrue(self.task.check_prerequisites())
        self.task.apply_effects()  # Should not raise any errors
    
    def test_weather_interface(self):
        """Test the IWeather interface."""
        # Test basic properties
        self.assertEqual(self.weather.type, "clear")
        self.assertEqual(self.weather.intensity, 1.0)
        
        # Test affecting objects
        target = Mock()
        self.weather.affect(target)
        self.assertFalse(target.apply_weather_effects.called)  # No method defined
        
        target.apply_weather_effects = Mock()
        self.weather.affect(target)
        target.apply_weather_effects.assert_called_once_with("clear", 1.0)
        
        # Test combining weather
        other_weather = MockWeather("clear", 0.5)
        combined = self.weather.combine(other_weather)
        self.assertEqual(combined.intensity, 0.75)
    
    def test_modifier_interface(self):
        """Test the IModifier interface."""
        # Test modifying values
        self.assertEqual(self.modifier.modify(10), 20)
        
        # Test combining modifiers
        other_modifier = MockModifier(3.0)
        combined = self.modifier.combine(other_modifier)
        self.assertEqual(combined.modify(10), 60)

if __name__ == '__main__':
    unittest.main() 