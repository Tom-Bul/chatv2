import pytest
from datetime import datetime, timedelta
from village_life.core.time_manager import TimeManager, GameDate, Season

@pytest.fixture
def time_manager():
    """Create a TimeManager instance for testing."""
    return TimeManager()

def test_game_date_initialization():
    """Test GameDate initialization with default values."""
    date = GameDate()
    assert date.year == 1
    assert date.season == Season.SPRING
    assert date.day == 1
    assert date.hour == 6
    assert date.minute == 0

def test_game_date_advance_minutes():
    """Test advancing GameDate by minutes."""
    date = GameDate()
    
    # Test minute advance
    date.advance(30)
    assert date.minute == 30
    assert date.hour == 6
    
    # Test hour rollover
    date.advance(40)
    assert date.minute == 10
    assert date.hour == 7

def test_game_date_advance_days():
    """Test advancing GameDate by multiple days."""
    date = GameDate()
    
    # Test season change
    date.advance_days(30)
    assert date.season == Season.SUMMER
    assert date.day == 1
    
    # Test year change
    date.advance_days(90)  # 3 seasons
    assert date.year == 2
    assert date.season == Season.SPRING
    assert date.day == 1

def test_time_manager_update():
    """Test TimeManager update mechanism."""
    manager = TimeManager()
    
    # Force an update by setting accumulator
    manager.accumulator = manager.fixed_time_step
    
    # Update should occur
    assert manager.update() is True
    
    # Accumulator should be reset
    assert manager.accumulator < manager.fixed_time_step

def test_time_of_day():
    """Test time of day calculations."""
    manager = TimeManager()
    
    # Test different times of day
    test_times = [
        (4, "night"),
        (5, "dawn"),
        (8, "morning"),
        (12, "noon"),
        (17, "evening"),
        (20, "dusk"),
        (22, "night")
    ]
    
    for hour, expected in test_times:
        manager.game_date.hour = hour
        assert manager.get_time_of_day() == expected

def test_season_effects():
    """Test seasonal effects on activities."""
    manager = TimeManager()
    
    # Test each season's effects
    for season in Season:
        manager.game_date.season = season
        effects = manager.get_season_effects()
        
        assert "crop_growth" in effects
        assert "energy_cost" in effects
        assert "foraging" in effects
        assert all(isinstance(v, float) for v in effects.values())

def test_formatted_date():
    """Test date formatting."""
    manager = TimeManager()
    manager.game_date = GameDate(
        year=2,
        season=Season.SUMMER,
        day=15,
        hour=14,
        minute=30
    )
    
    formatted = manager.get_formatted_date()
    assert "Year 2" in formatted
    assert "SUMMER" in formatted.upper()
    assert "Day 15" in formatted
    assert "14:30" in formatted

def test_progress_calculations():
    """Test various progress calculations."""
    manager = TimeManager()
    
    # Test day progress
    manager.game_date.hour = 12
    manager.game_date.minute = 0
    assert manager.get_day_progress() == 0.5
    
    # Test season progress
    manager.game_date.day = 15
    assert manager.get_season_progress() == 14/30  # (15-1)/30
    
    # Test year progress
    manager.game_date.season = Season.SUMMER
    manager.game_date.day = 15
    # (1 season * 30 + 14 days) / (4 seasons * 30 days)
    assert manager.get_year_progress() == (30 + 14)/(4 * 30)

def test_save_load_state():
    """Test saving and loading TimeManager state."""
    manager = TimeManager()
    
    # Modify state
    manager.game_date = GameDate(
        year=2,
        season=Season.SUMMER,
        day=15,
        hour=14,
        minute=30
    )
    manager.time_scale = 120.0
    
    # Save state
    state = manager.save_state()
    
    # Create new manager and load state
    new_manager = TimeManager()
    new_manager.load_state(state)
    
    # Verify state was restored
    assert new_manager.game_date.year == 2
    assert new_manager.game_date.season == Season.SUMMER
    assert new_manager.game_date.day == 15
    assert new_manager.game_date.hour == 14
    assert new_manager.game_date.minute == 30
    assert new_manager.time_scale == 120.0

def test_day_night_cycle():
    """Test day/night cycle detection."""
    manager = TimeManager()
    
    # Test daytime
    manager.game_date.hour = 12
    assert manager.is_daytime() is True
    
    # Test nighttime
    manager.game_date.hour = 22
    assert manager.is_daytime() is False

def test_interpolation_alpha():
    """Test the interpolation alpha value calculation."""
    manager = TimeManager()
    
    # Initially alpha should be 0
    assert manager.alpha == 0.0
    
    # Set accumulator to half of fixed time step
    manager.accumulator = manager.fixed_time_step / 2
    manager.update()
    assert 0.0 <= manager.alpha <= 1.0
    
    # Set accumulator to exactly fixed time step
    manager.accumulator = manager.fixed_time_step
    assert manager.update() is True  # Should trigger an update
    assert manager.alpha < 1.0  # Alpha should be reset after update

def test_multiple_updates():
    """Test multiple consecutive updates."""
    manager = TimeManager()
    initial_date = GameDate(
        year=manager.game_date.year,
        season=manager.game_date.season,
        day=manager.game_date.day,
        hour=manager.game_date.hour,
        minute=manager.game_date.minute
    )
    
    # Simulate multiple updates
    for _ in range(10):
        manager.accumulator = manager.fixed_time_step
        manager.update()
        
    # Verify time has advanced
    assert (
        manager.game_date.minute > initial_date.minute or
        manager.game_date.hour > initial_date.hour or
        manager.game_date.day > initial_date.day
    )
    
    # Verify alpha remains valid
    assert 0.0 <= manager.alpha <= 1.0 