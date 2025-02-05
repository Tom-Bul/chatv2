"""
Tests for the weather system.
"""

import unittest
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from unittest.mock import Mock, patch

from src.core.weather_manager import (
    WeatherType, Weather, WeatherManager,
    WeatherEvent
)

class TestWeatherType(unittest.TestCase):
    """Test the WeatherType enumeration."""
    def test_weather_types(self):
        """Test all weather types are defined."""
        expected_types = {
            "CLEAR", "CLOUDY", "RAINY",
            "STORMY", "SNOWY", "HOT"
        }
        actual_types = {t.name for t in WeatherType}
        self.assertEqual(expected_types, actual_types)

class TestWeather(unittest.TestCase):
    """Test the Weather class."""
    def setUp(self):
        self.current_time = datetime.now()
        self.weather = Weather(
            weather_type=WeatherType.RAINY,
            intensity=0.8,
            duration=timedelta(hours=2),
            start_time=self.current_time
        )
    
    def test_weather_creation(self):
        """Test creating weather states."""
        self.assertEqual(self.weather.type, "RAINY")
        self.assertEqual(self.weather.intensity, 0.8)
        self.assertEqual(
            self.weather.end_time,
            self.current_time + timedelta(hours=2)
        )
    
    def test_intensity_bounds(self):
        """Test intensity is properly bounded."""
        # Test upper bound
        weather = Weather(
            WeatherType.CLEAR,
            intensity=1.5,
            duration=timedelta(hours=1),
            start_time=self.current_time
        )
        self.assertEqual(weather.intensity, 1.0)
        
        # Test lower bound
        weather = Weather(
            WeatherType.CLEAR,
            intensity=-0.5,
            duration=timedelta(hours=1),
            start_time=self.current_time
        )
        self.assertEqual(weather.intensity, 0.0)
    
    def test_weather_effects(self):
        """Test weather effects calculation."""
        effects = self.weather._get_current_effects()
        
        # Test all effect types are present
        expected_effects = {
            "task_speed", "resource_rate",
            "tool_wear", "energy_cost"
        }
        self.assertEqual(set(effects.keys()), expected_effects)
        
        # Test effects are properly scaled by intensity
        base_effects = self.weather._initialize_effects()
        for key, value in effects.items():
            base = base_effects[key]
            if base < 1.0:
                expected = 1.0 - ((1.0 - base) * self.weather.intensity)
            else:
                expected = 1.0 + ((base - 1.0) * self.weather.intensity)
            self.assertAlmostEqual(value, expected)
    
    def test_weather_affect(self):
        """Test applying weather effects to targets."""
        # Test target with weather support
        target = Mock()
        target.apply_weather_effects = Mock()
        
        self.weather.affect(target)
        target.apply_weather_effects.assert_called_once()
        
        # Test target without weather support
        target_no_weather = Mock()
        self.weather.affect(target_no_weather)
        self.assertFalse(hasattr(target_no_weather, 'apply_weather_effects'))
    
    def test_weather_combine(self):
        """Test combining weather states."""
        other_weather = Weather(
            weather_type=WeatherType.RAINY,
            intensity=0.4,
            duration=timedelta(hours=1),
            start_time=self.current_time
        )
        
        combined = self.weather.combine(other_weather)
        
        # Test combined properties
        self.assertEqual(combined.type, "RAINY")
        self.assertEqual(combined.intensity, 0.6)  # (0.8 + 0.4) / 2
        self.assertEqual(
            combined._duration,
            timedelta(hours=1)  # min of both durations
        )
        
        # Test combining different types raises error
        different_type = Weather(
            weather_type=WeatherType.CLEAR,
            intensity=0.5,
            duration=timedelta(hours=1),
            start_time=self.current_time
        )
        with self.assertRaises(ValueError):
            self.weather.combine(different_type)
    
    def test_weather_serialization(self):
        """Test weather serialization."""
        # Convert to dict
        data = self.weather.to_dict()
        
        # Test all fields are present
        expected_fields = {
            "type", "intensity",
            "duration_seconds",
            "start_time"
        }
        self.assertEqual(set(data.keys()), expected_fields)
        
        # Create new weather from dict
        new_weather = Weather.from_dict(data)
        
        # Compare properties
        self.assertEqual(new_weather.type, self.weather.type)
        self.assertEqual(new_weather.intensity, self.weather.intensity)
        self.assertEqual(new_weather.end_time, self.weather.end_time)

class TestWeatherManager(unittest.TestCase):
    """Test the WeatherManager class."""
    def setUp(self):
        self.manager = WeatherManager()
        self.current_time = datetime.now()
    
    def test_seasonal_patterns(self):
        """Test seasonal weather patterns."""
        patterns = self.manager._initialize_patterns()
        
        # Test all seasons are present
        expected_seasons = {"SPRING", "SUMMER", "FALL", "WINTER"}
        self.assertEqual(set(patterns.keys()), expected_seasons)
        
        # Test pattern probabilities sum to 1.0
        for season, pattern in patterns.items():
            total_prob = sum(prob for _, prob in pattern)
            self.assertAlmostEqual(total_prob, 1.0)
    
    @patch('random.uniform')
    @patch('random.randint')
    def test_weather_generation(self, mock_randint, mock_uniform):
        """Test weather generation."""
        # Mock random values
        mock_uniform.return_value = 0.7  # intensity
        mock_randint.return_value = 60  # duration in minutes
        
        # Generate weather
        self.manager._generate_weather(self.current_time, "SUMMER")
        
        # Test weather was generated
        self.assertIsNotNone(self.manager._current_weather)
        self.assertEqual(self.manager._current_weather.intensity, 0.7)
        self.assertEqual(
            self.manager._current_weather._duration,
            timedelta(minutes=60)
        )
    
    def test_weather_update(self):
        """Test weather state updates."""
        # Set up initial weather
        self.manager._generate_weather(self.current_time, "SUMMER")
        initial_weather = self.manager._current_weather
        
        # Update with small time step
        self.manager.update(timedelta(minutes=1), "SUMMER")
        self.assertEqual(self.manager._current_weather, initial_weather)
        
        # Update near end of weather duration
        future_time = self.current_time + initial_weather._duration - timedelta(minutes=4)
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = future_time
            self.manager.update(timedelta(minutes=1), "SUMMER")
            self.assertIsNotNone(self.manager._next_weather)
    
    def test_weather_transition(self):
        """Test weather transition handling."""
        # Set up initial weather
        self.manager._generate_weather(self.current_time, "SUMMER")
        
        # Generate next weather
        self.manager._generate_next_weather(self.current_time, "SUMMER")
        
        # Test transition progress
        future_time = self.current_time + timedelta(minutes=4)  # Within 5-minute transition
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = future_time
            self.manager.update(timedelta(minutes=1), "SUMMER")
            self.assertGreater(self.manager._transition_progress, 0.0)
            self.assertLess(self.manager._transition_progress, 1.0)
    
    def test_weather_description(self):
        """Test getting weather descriptions."""
        # Test with no weather
        description, intensity = self.manager.get_weather_description()
        self.assertEqual(description, "Clear")
        self.assertEqual(intensity, "Mild")
        
        # Test with weather
        self.manager._current_weather = Weather(
            weather_type=WeatherType.STORMY,
            intensity=0.9,
            duration=timedelta(hours=1),
            start_time=self.current_time
        )
        description, intensity = self.manager.get_weather_description()
        self.assertEqual(description, "STORMY")
        self.assertEqual(intensity, "Severe")
    
    def test_save_load_state(self):
        """Test saving and loading weather state."""
        # Set up initial state
        self.manager._generate_weather(self.current_time, "SUMMER")
        self.manager._generate_next_weather(self.current_time, "SUMMER")
        
        # Save state
        state = self.manager.save_state()
        
        # Create new manager and load state
        new_manager = WeatherManager()
        new_manager.load_state(state)
        
        # Compare states
        self.assertEqual(
            new_manager._current_weather.type,
            self.manager._current_weather.type
        )
        self.assertEqual(
            new_manager._current_weather.intensity,
            self.manager._current_weather.intensity
        )
        self.assertEqual(
            new_manager._next_weather.type,
            self.manager._next_weather.type
        )
        self.assertEqual(
            new_manager._transition_progress,
            self.manager._transition_progress
        )

if __name__ == '__main__':
    unittest.main() 