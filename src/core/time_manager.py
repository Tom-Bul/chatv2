from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple
import logging

# Set up logging
logging.basicConfig(
    filename='game.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Season(Enum):
    SPRING = auto()
    SUMMER = auto()
    AUTUMN = auto()
    WINTER = auto()
    
    @property
    def next_season(self) -> 'Season':
        seasons = list(Season)
        current_idx = seasons.index(self)
        return seasons[(current_idx + 1) % len(seasons)]

@dataclass
class GameDate:
    year: int = 1
    season: Season = Season.SPRING
    day: int = 1  # 1-30 for each season
    hour: int = 6  # 0-23
    minute: int = 0  # 0-59
    
    def advance(self, minutes: int) -> None:
        """Advance time by specified minutes."""
        self.minute += minutes
        
        # Handle minute overflow
        if self.minute >= 60:
            hours_to_add = self.minute // 60
            self.minute %= 60
            self.hour += hours_to_add
        
        # Handle hour overflow
        if self.hour >= 24:
            days_to_add = self.hour // 24
            self.hour %= 24
            self.advance_days(days_to_add)
    
    def advance_days(self, days: int) -> None:
        """Advance by specified number of days."""
        self.day += days
        
        # Handle season change (30 days per season)
        while self.day > 30:
            self.day -= 30
            self.season = self.season.next_season
            if self.season == Season.SPRING:
                self.year += 1

@dataclass
class TimeManager:
    real_start_time: datetime = field(default_factory=datetime.now)
    game_date: GameDate = field(default_factory=GameDate)
    time_scale: float = 60.0  # 1 real second = 1 game minute
    fixed_time_step: float = 1/60  # 60 Hz update rate
    accumulator: float = 0.0
    last_update_time: float = field(default_factory=lambda: datetime.now().timestamp())
    
    # Time-based effects
    day_night_cycle: Dict[int, str] = field(default_factory=lambda: {
        5: "dawn",
        8: "morning",
        12: "noon",
        17: "evening",
        20: "dusk",
        22: "night"
    })
    
    seasonal_effects: Dict[Season, Dict[str, float]] = field(default_factory=lambda: {
        Season.SPRING: {
            "crop_growth": 1.2,
            "energy_cost": 1.0,
            "foraging": 1.2
        },
        Season.SUMMER: {
            "crop_growth": 1.5,
            "energy_cost": 1.2,
            "foraging": 1.0
        },
        Season.AUTUMN: {
            "crop_growth": 0.8,
            "energy_cost": 1.0,
            "foraging": 1.5
        },
        Season.WINTER: {
            "crop_growth": 0.3,
            "energy_cost": 1.5,
            "foraging": 0.5
        }
    })
    
    def update(self) -> bool:
        """Update game time based on real time passed.
        Returns True if a fixed update should occur."""
        current_time = datetime.now().timestamp()
        frame_time = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # Add frame time to accumulator
        self.accumulator += frame_time
        
        # Check if we should do a fixed update
        if self.accumulator >= self.fixed_time_step:
            # Calculate game minutes passed
            real_seconds = self.fixed_time_step
            game_minutes = int(real_seconds * self.time_scale)
            
            # Update game date
            self.game_date.advance(game_minutes)
            
            # Consume time step
            self.accumulator -= self.fixed_time_step
            return True
            
        return False
    
    def get_time_of_day(self) -> str:
        """Get the current time of day description."""
        hour = self.game_date.hour
        
        # Find the most recent time period
        current_period = "night"  # Default
        for time, period in sorted(self.day_night_cycle.items()):
            if hour >= time:
                current_period = period
            else:
                break
                
        return current_period
    
    def get_season_effects(self) -> Dict[str, float]:
        """Get the current season's effects on various activities."""
        return self.seasonal_effects[self.game_date.season]
    
    def get_formatted_date(self) -> str:
        """Get a formatted string of the current game date."""
        return (
            f"Year {self.game_date.year}, {self.game_date.season.name.capitalize()}, "
            f"Day {self.game_date.day:02d} - "
            f"{self.game_date.hour:02d}:{self.game_date.minute:02d} "
            f"({self.get_time_of_day()})"
        )
    
    def is_daytime(self) -> bool:
        """Check if it's currently daytime."""
        return 5 <= self.game_date.hour < 20
    
    def get_day_progress(self) -> float:
        """Get the progress through the current day (0.0 to 1.0)."""
        minutes_total = self.game_date.hour * 60 + self.game_date.minute
        return minutes_total / (24 * 60)
    
    def get_season_progress(self) -> float:
        """Get the progress through the current season (0.0 to 1.0)."""
        return (self.game_date.day - 1) / 30
    
    def get_year_progress(self) -> float:
        """Get the progress through the current year (0.0 to 1.0)."""
        season_idx = list(Season).index(self.game_date.season)
        return (season_idx * 30 + self.game_date.day - 1) / (4 * 30)
    
    def save_state(self) -> dict:
        """Save the time manager state."""
        return {
            "real_start_time": self.real_start_time.isoformat(),
            "game_date": {
                "year": self.game_date.year,
                "season": self.game_date.season.name,
                "day": self.game_date.day,
                "hour": self.game_date.hour,
                "minute": self.game_date.minute
            },
            "time_scale": self.time_scale
        }
    
    def load_state(self, state: dict) -> None:
        """Load the time manager state."""
        self.real_start_time = datetime.fromisoformat(state["real_start_time"])
        self.game_date = GameDate(
            year=state["game_date"]["year"],
            season=Season[state["game_date"]["season"]],
            day=state["game_date"]["day"],
            hour=state["game_date"]["hour"],
            minute=state["game_date"]["minute"]
        )
        self.time_scale = state["time_scale"]
        self.last_update_time = datetime.now().timestamp()
        logger.info("Time manager state loaded") 