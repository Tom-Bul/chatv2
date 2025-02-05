"""
Tests for the modifier system.
"""

import unittest
from datetime import datetime, timedelta
from typing import Any, Dict
from unittest.mock import Mock, patch

from src.core.modifiers import (
    BaseModifier, MultiplyModifier, AddModifier,
    QualityModifier, WeatherModifier, TimeModifier,
    ModifierRegistry, create_modifier, register_modifier
)

class TestBaseModifier(unittest.TestCase):
    """Test the BaseModifier class."""
    def test_base_modifier_creation(self):
        """Test creating a base modifier."""
        class TestModifier(BaseModifier):
            def modify(self, target: Any) -> Any:
                return target
        
        modifier = TestModifier("test", 1.0)
        self.assertEqual(modifier.type, "test")
        self.assertEqual(modifier.strength, 1.0)
    
    def test_base_modifier_combine(self):
        """Test combining base modifiers."""
        class TestModifier(BaseModifier):
            def modify(self, target: Any) -> Any:
                return target
        
        mod1 = TestModifier("test", 1.0)
        mod2 = TestModifier("test", 2.0)
        combined = mod1.combine(mod2)
        
        self.assertEqual(combined.strength, 3.0)
        
        # Test combining different types
        class OtherModifier(BaseModifier):
            def modify(self, target: Any) -> Any:
                return target
        
        other = OtherModifier("test", 1.0)
        with self.assertRaises(ValueError):
            mod1.combine(other)

class TestMultiplyModifier(unittest.TestCase):
    """Test the MultiplyModifier class."""
    def test_multiply_modifier(self):
        """Test multiply modifier functionality."""
        modifier = MultiplyModifier("multiply", 2.0)
        
        # Test with numbers
        self.assertEqual(modifier.modify(10), 20)
        self.assertEqual(modifier.modify(0.5), 1.0)
        
        # Test combining
        other = MultiplyModifier("multiply", 3.0)
        combined = modifier.combine(other)
        self.assertEqual(combined.modify(10), 50)

class TestAddModifier(unittest.TestCase):
    """Test the AddModifier class."""
    def test_add_modifier(self):
        """Test add modifier functionality."""
        modifier = AddModifier("add", 5.0)
        
        # Test with numbers
        self.assertEqual(modifier.modify(10), 15)
        self.assertEqual(modifier.modify(0.5), 5.5)
        
        # Test combining
        other = AddModifier("add", 3.0)
        combined = modifier.combine(other)
        self.assertEqual(combined.modify(10), 18)

class TestQualityModifier(unittest.TestCase):
    """Test the QualityModifier class."""
    def test_quality_modifier(self):
        """Test quality modifier functionality."""
        modifier = QualityModifier("quality", 0.5)
        
        # Test with mock resource
        resource = Mock()
        resource.quality = 1.0
        
        modified = modifier.modify(resource)
        self.assertEqual(modified.quality, 0.5)
        
        # Test quality bounds
        resource.quality = 2.0
        modified = modifier.modify(resource)
        self.assertEqual(modified.quality, 1.0)
        
        resource.quality = -1.0
        modified = modifier.modify(resource)
        self.assertEqual(modified.quality, 0.0)

class TestWeatherModifier(unittest.TestCase):
    """Test the WeatherModifier class."""
    def test_weather_modifier(self):
        """Test weather modifier functionality."""
        modifier = WeatherModifier("rainy", 0.8)
        
        # Test with mock target
        target = Mock()
        target.apply_weather = Mock()
        
        modifier.modify(target)
        target.apply_weather.assert_called_once_with("rainy", 0.8)
        
        # Test with target without weather support
        other_target = Mock()
        modified = modifier.modify(other_target)
        self.assertEqual(modified, other_target)

class TestTimeModifier(unittest.TestCase):
    """Test the TimeModifier class."""
    def test_time_modifier(self):
        """Test time modifier functionality."""
        modifier = TimeModifier(0.5, "night")
        
        # Test with mock target
        target = Mock()
        target.apply_time_effect = Mock()
        
        modifier.modify(target)
        target.apply_time_effect.assert_called_once_with("night", 0.5)
        
        # Test with target without time support
        other_target = Mock()
        modified = modifier.modify(other_target)
        self.assertEqual(modified, other_target)

class TestModifierRegistry(unittest.TestCase):
    """Test the ModifierRegistry class."""
    def setUp(self):
        self.registry = ModifierRegistry()
    
    def test_register_modifier(self):
        """Test registering modifiers."""
        class TestModifier(BaseModifier):
            def modify(self, target: Any) -> Any:
                return target
        
        self.registry.register_modifier("test", TestModifier)
        self.assertIn("test", self.registry.get_available_modifiers())
    
    def test_create_modifier(self):
        """Test creating modifiers from registry."""
        self.registry.register_modifier("multiply", MultiplyModifier)
        modifier = self.registry.create_modifier("multiply", strength=2.0)
        
        self.assertIsInstance(modifier, MultiplyModifier)
        self.assertEqual(modifier.strength, 2.0)
        
        # Test creating unknown modifier
        with self.assertRaises(ValueError):
            self.registry.create_modifier("unknown")

class TestModifierFunctions(unittest.TestCase):
    """Test the global modifier functions."""
    def test_create_modifier(self):
        """Test creating modifiers using global function."""
        modifier = create_modifier("multiply", strength=2.0)
        self.assertIsInstance(modifier, MultiplyModifier)
        self.assertEqual(modifier.strength, 2.0)
    
    def test_register_modifier(self):
        """Test registering modifiers using global function."""
        class TestModifier(BaseModifier):
            def modify(self, target: Any) -> Any:
                return target
        
        register_modifier("test", TestModifier)
        modifier = create_modifier("test")
        self.assertIsInstance(modifier, TestModifier)

if __name__ == '__main__':
    unittest.main() 