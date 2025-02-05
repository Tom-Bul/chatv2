import pytest
from datetime import datetime, timedelta
from src.core.weather_manager import WeatherManager, WeatherType, WeatherState

@pytest.fixture
def weather_manager():
    return WeatherManager()

def test_weather_generation(weather_manager):
    """Test weather generation for different seasons."""
    current_time = datetime.now()
    
    # Test spring weather
    weather_manager.generate_weather(current_time, "SPRING")
    assert weather_manager.current_weather is not None
    assert weather_manager.current_weather.type in [
        WeatherType.CLEAR,
        WeatherType.CLOUDY,
        WeatherType.RAINY,
        WeatherType.STORMY
    ]
    
    # Test summer weather
    weather_manager.generate_weather(current_time, "SUMMER")
    assert weather_manager.current_weather.type in [
        WeatherType.CLEAR,
        WeatherType.HOT,
        WeatherType.CLOUDY,
        WeatherType.STORMY
    ]
    
    # Test winter weather
    weather_manager.generate_weather(current_time, "WINTER")
    assert weather_manager.current_weather.type in [
        WeatherType.SNOWY,
        WeatherType.CLOUDY,
        WeatherType.CLEAR,
        WeatherType.STORMY
    ]

def test_weather_duration(weather_manager):
    """Test weather duration generation."""
    current_time = datetime.now()
    
    # Test normal weather duration
    weather_manager.current_weather = WeatherState(
        type=WeatherType.CLEAR,
        intensity=0.5,
        duration=weather_manager._generate_duration(WeatherType.CLEAR),
        start_time=current_time
    )
    assert 60 <= weather_manager.current_weather.duration.total_seconds() / 60 <= 240
    
    # Test extreme weather duration
    weather_manager.current_weather = WeatherState(
        type=WeatherType.STORMY,
        intensity=0.8,
        duration=weather_manager._generate_duration(WeatherType.STORMY),
        start_time=current_time
    )
    assert 30 <= weather_manager.current_weather.duration.total_seconds() / 60 <= 120

def test_weather_transitions(weather_manager):
    """Test weather state transitions."""
    current_time = datetime.now()
    
    # Set up initial weather
    weather_manager.current_weather = WeatherState(
        type=WeatherType.CLEAR,
        intensity=0.5,
        duration=timedelta(minutes=10),
        start_time=current_time - timedelta(minutes=5)
    )
    
    # Generate next weather
    weather_manager.generate_next_weather(current_time, "SUMMER")
    assert weather_manager.next_weather is not None
    
    # Update weather state
    weather_manager.update(timedelta(minutes=1), "SUMMER")
    assert 0 < weather_manager.transition_progress < 1
    
    # Test weather change
    weather_manager.current_weather = WeatherState(
        type=WeatherType.CLEAR,
        intensity=0.5,
        duration=timedelta(minutes=1),
        start_time=current_time - timedelta(minutes=2)
    )
    weather_manager.update(timedelta(minutes=1), "SUMMER")
    assert weather_manager.current_weather.type == weather_manager.next_weather.type

def test_weather_effects(weather_manager):
    """Test weather effects calculation."""
    current_time = datetime.now()
    
    # Test clear weather effects
    weather_manager.current_weather = WeatherState(
        type=WeatherType.CLEAR,
        intensity=1.0,
        duration=timedelta(minutes=30),
        start_time=current_time
    )
    effects = weather_manager.get_current_effects()
    assert effects["task_speed"] == 1.0
    assert effects["resource_rate"] == 1.0
    
    # Test stormy weather effects
    weather_manager.current_weather = WeatherState(
        type=WeatherType.STORMY,
        intensity=1.0,
        duration=timedelta(minutes=30),
        start_time=current_time
    )
    effects = weather_manager.get_current_effects()
    assert effects["task_speed"] == 0.5
    assert effects["tool_wear"] == 1.5
    
    # Test effect scaling with intensity
    weather_manager.current_weather = WeatherState(
        type=WeatherType.RAINY,
        intensity=0.5,
        duration=timedelta(minutes=30),
        start_time=current_time
    )
    effects = weather_manager.get_current_effects()
    assert 0.7 < effects["task_speed"] < 0.85
    assert 1.0 < effects["tool_wear"] < 1.2

def test_weather_description(weather_manager):
    """Test weather description generation."""
    current_time = datetime.now()
    
    # Test mild weather
    weather_manager.current_weather = WeatherState(
        type=WeatherType.CLOUDY,
        intensity=0.2,
        duration=timedelta(minutes=30),
        start_time=current_time
    )
    weather, intensity = weather_manager.get_weather_description()
    assert weather == "Cloudy"
    assert intensity == "Mild"
    
    # Test severe weather
    weather_manager.current_weather = WeatherState(
        type=WeatherType.STORMY,
        intensity=0.95,
        duration=timedelta(minutes=30),
        start_time=current_time
    )
    weather, intensity = weather_manager.get_weather_description()
    assert weather == "Stormy"
    assert intensity == "Severe"

def test_save_load_state(weather_manager):
    """Test saving and loading weather state."""
    current_time = datetime.now()
    
    # Set up weather states
    weather_manager.current_weather = WeatherState(
        type=WeatherType.CLEAR,
        intensity=0.5,
        duration=timedelta(minutes=30),
        start_time=current_time
    )
    weather_manager.next_weather = WeatherState(
        type=WeatherType.CLOUDY,
        intensity=0.7,
        duration=timedelta(minutes=30),
        start_time=current_time + timedelta(minutes=30)
    )
    weather_manager.transition_progress = 0.3
    
    # Save state
    state = weather_manager.save_state()
    
    # Create new manager and load state
    new_manager = WeatherManager()
    new_manager.load_state(state)
    
    # Verify state
    assert new_manager.current_weather.type == weather_manager.current_weather.type
    assert new_manager.current_weather.intensity == weather_manager.current_weather.intensity
    assert new_manager.next_weather.type == weather_manager.next_weather.type
    assert new_manager.transition_progress == weather_manager.transition_progress

def test_weather_pattern_distribution(weather_manager):
    """Test weather pattern distribution by season."""
    current_time = datetime.now()
    weather_counts = {weather_type: 0 for weather_type in WeatherType}
    
    # Generate multiple weather states
    for _ in range(1000):
        weather_manager.generate_weather(current_time, "SUMMER")
        weather_counts[weather_manager.current_weather.type] += 1
    
    # Check distribution
    assert weather_counts[WeatherType.CLEAR] > weather_counts[WeatherType.STORMY]
    assert weather_counts[WeatherType.HOT] > weather_counts[WeatherType.STORMY]
    assert weather_counts[WeatherType.SNOWY] == 0  # No snow in summer 