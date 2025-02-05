"""
Task system implementation.
Handles task management, progression, and rewards.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime, timedelta
from enum import Enum, auto
import logging
import random
import uuid

from .abstractions.base import ITask, IModifier
from .event_system import publish_event, TaskEvent
from .modifiers import create_modifier
from .resource_manager import ResourceType

# Set up logging
logging.basicConfig(
    filename='game.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TaskType(Enum):
    """Types of tasks available in the game."""
    # Resource gathering
    GATHERING = auto()
    MINING = auto()
    FARMING = auto()
    HUNTING = auto()
    FISHING = auto()
    
    # Crafting and construction
    CRAFTING = auto()
    BUILDING = auto()
    CONSTRUCTION = auto()
    REPAIR = auto()
    
    # Knowledge and research
    RESEARCH = auto()
    STUDY = auto()
    EXPERIMENT = auto()
    
    # Commerce and social
    TRADING = auto()
    NEGOTIATION = auto()
    DIPLOMACY = auto()
    
    # Village management
    PLANNING = auto()
    ORGANIZING = auto()
    TRAINING = auto()
    
    # Events and special tasks
    EVENT = auto()
    EXPEDITION = auto()
    DEFENSE = auto()
    CELEBRATION = auto()

class TaskStatus(Enum):
    """Status of a task."""
    LOCKED = auto()      # Prerequisites not met
    AVAILABLE = auto()   # Can be started
    IN_PROGRESS = auto() # Currently active
    COMPLETED = auto()   # Successfully finished
    FAILED = auto()      # Failed to complete

@dataclass
class ResourceRequirement:
    """Resource requirement for a task."""
    type: ResourceType
    quantity: float
    min_quality: float = 0.0
    consumed: bool = True  # Whether the resource is consumed by the task

@dataclass
class ResourceReward:
    """Resource reward for completing a task."""
    type: ResourceType
    base_quantity: float
    quality_multiplier: float = 1.0
    skill_multiplier: float = 1.0
    random_bonus: float = 0.0  # Random bonus percentage (0.0-1.0)

@dataclass
class TaskPrerequisite:
    """Prerequisites for starting a task."""
    task_id: Optional[str] = None  # ID of required task
    skill_name: Optional[str] = None  # Name of required skill
    skill_level: Optional[float] = None  # Required skill level
    building_type: Optional[str] = None  # Required building type
    resource_type: Optional[ResourceType] = None  # Required resource type
    resource_quantity: Optional[float] = None  # Required resource quantity
    resource_quality: Optional[float] = None  # Required resource quality
    season: Optional[str] = None  # Required season
    weather_type: Optional[str] = None  # Required weather type
    time_range: Optional[Tuple[int, int]] = None  # Required time range (hours)
    village_level: Optional[int] = None  # Required village development level

class Task(ITask):
    """Implementation of a game task."""
    def __init__(
        self,
        name: str,
        description: str,
        task_type: TaskType,
        duration: timedelta,
        prerequisites: List[TaskPrerequisite] = None,
        required_resources: List[ResourceRequirement] = None,
        required_tools: List[ResourceRequirement] = None,
        resource_rewards: List[ResourceReward] = None,
        skill_requirements: Dict[str, float] = None,
        skill_rewards: Dict[str, float] = None,
        reputation_reward: float = 0.0,
        village_exp_reward: float = 0.0,
        valid_time_ranges: List[Tuple[int, int]] = None,
        season_multipliers: Dict[str, float] = None,
        weather_requirements: List[str] = None,
        chain_id: Optional[str] = None,
        event_id: Optional[str] = None
    ):
        self._id = str(uuid.uuid4())
        self._name = name
        self._description = description
        self._type = task_type
        self._duration = duration
        self._prerequisites = prerequisites or []
        self._required_resources = required_resources or []
        self._required_tools = required_tools or []
        self._resource_rewards = resource_rewards or []
        self._skill_requirements = skill_requirements or {}
        self._skill_rewards = skill_rewards or {}
        self._reputation_reward = reputation_reward
        self._village_exp_reward = village_exp_reward
        self._valid_time_ranges = valid_time_ranges or []
        self._season_multipliers = season_multipliers or {}
        self._weather_requirements = weather_requirements or []
        self._chain_id = chain_id
        self._event_id = event_id
        
        self._status = TaskStatus.AVAILABLE
        self._progress = 0.0
        self._start_time = None
        self._rewards_claimed = False
        self._modifiers: List[IModifier] = []
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def status(self) -> str:
        return self._status.name
    
    @property
    def progress(self) -> float:
        return self._progress
    
    def apply_modifier(self, modifier: IModifier) -> 'Task':
        """Apply a modifier to this task."""
        modified = modifier.modify(self)
        if not isinstance(modified, Task):
            raise ValueError(f"Modifier returned invalid type: {type(modified)}")
        return modified
    
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met."""
        # This is just a placeholder - actual implementation would need game state
        return self._status != TaskStatus.LOCKED
    
    def apply_effects(self) -> None:
        """Apply task effects when completed."""
        if self._status != TaskStatus.COMPLETED or self._rewards_claimed:
            return
        
        publish_event(TaskEvent(
            task_id=self.id,
            action="complete",
            old_status=TaskStatus.IN_PROGRESS.name,
            new_status=TaskStatus.COMPLETED.name,
            progress=1.0
        ))
        
        self._rewards_claimed = True
    
    def update(self, delta_time: float) -> None:
        """Update task progress."""
        if self._status != TaskStatus.IN_PROGRESS:
            return
        
        # Apply modifiers to progress rate
        rate = 1.0
        for modifier in self._modifiers:
            rate = modifier.modify(rate)
        
        # Update progress
        progress_amount = delta_time / self._duration.total_seconds() * rate
        old_progress = self._progress
        self._progress = min(1.0, self._progress + progress_amount)
        
        # Publish progress event
        publish_event(TaskEvent(
            task_id=self.id,
            action="progress",
            progress=self._progress
        ))
        
        # Check for completion
        if self._progress >= 1.0 and old_progress < 1.0:
            self._status = TaskStatus.COMPLETED
            publish_event(TaskEvent(
                task_id=self.id,
                action="complete",
                old_status=TaskStatus.IN_PROGRESS.name,
                new_status=TaskStatus.COMPLETED.name,
                progress=1.0
            ))
    
    def can_start(
        self,
        current_time: datetime,
        available_resources: Dict[ResourceType, Tuple[float, float]],
        completed_task_ids: Set[str],
        current_skills: Dict[str, float],
        season: str,
        weather: str
    ) -> Tuple[bool, str]:
        """Check if task can be started."""
        # Check prerequisites
        for prereq in self._prerequisites:
            if prereq.task_id and prereq.task_id not in completed_task_ids:
                return False, f"Required task {prereq.task_id} not completed"
            
            if prereq.skill_name and prereq.skill_level:
                if current_skills.get(prereq.skill_name, 0) < prereq.skill_level:
                    return False, f"Required {prereq.skill_name} level {prereq.skill_level} not met"
            
            if prereq.season and season != prereq.season:
                return False, f"Task requires {prereq.season} season"
            
            if prereq.weather_type and weather != prereq.weather_type:
                return False, f"Task requires {prereq.weather_type} weather"
            
            if prereq.time_range:
                start_hour, end_hour = prereq.time_range
                current_hour = current_time.hour
                if not (start_hour <= current_hour < end_hour):
                    return False, f"Task can only be done between {start_hour}:00 and {end_hour}:00"
        
        # Check required resources
        for req in self._required_resources:
            if req.type not in available_resources:
                return False, f"Missing required resource: {req.type.name}"
            
            quantity, quality = available_resources[req.type]
            if quantity < req.quantity:
                return False, f"Not enough {req.type.name}: need {req.quantity}, have {quantity}"
            
            if quality < req.min_quality:
                return False, f"Quality of {req.type.name} too low: need {req.min_quality}, have {quality}"
        
        # Check required tools
        for tool in self._required_tools:
            if tool.type not in available_resources:
                return False, f"Missing required tool: {tool.type.name}"
            
            quantity, quality = available_resources[tool.type]
            if quantity < tool.quantity:
                return False, f"Not enough {tool.type.name}: need {tool.quantity}, have {quantity}"
            
            if quality < tool.min_quality:
                return False, f"Quality of {tool.type.name} too low: need {tool.min_quality}, have {quality}"
        
        # Check skill requirements
        for skill, required_level in self._skill_requirements.items():
            if current_skills.get(skill, 0) < required_level:
                return False, f"Required {skill} level {required_level} not met"
        
        # Check time restrictions
        if self._valid_time_ranges:
            current_hour = current_time.hour
            valid_time = False
            for start_hour, end_hour in self._valid_time_ranges:
                if start_hour <= current_hour < end_hour:
                    valid_time = True
                    break
            if not valid_time:
                return False, "Task cannot be done at this time"
        
        # Check weather requirements
        if self._weather_requirements and weather not in self._weather_requirements:
            return False, f"Task requires specific weather: {', '.join(self._weather_requirements)}"
        
        return True, "Ready to start"
    
    def start(self, current_time: datetime) -> None:
        """Start the task."""
        if self._status != TaskStatus.AVAILABLE:
            raise ValueError("Task cannot be started")
        
        self._status = TaskStatus.IN_PROGRESS
        self._start_time = current_time
        self._progress = 0.0
        
        publish_event(TaskEvent(
            task_id=self.id,
            action="start",
            old_status=TaskStatus.AVAILABLE.name,
            new_status=TaskStatus.IN_PROGRESS.name,
            progress=0.0
        ))
    
    def fail(self, reason: str) -> None:
        """Mark the task as failed."""
        if self._status != TaskStatus.IN_PROGRESS:
            raise ValueError("Only in-progress tasks can fail")
        
        self._status = TaskStatus.FAILED
        
        publish_event(TaskEvent(
            task_id=self.id,
            action="fail",
            old_status=TaskStatus.IN_PROGRESS.name,
            new_status=TaskStatus.FAILED.name,
            progress=self._progress
        ))
    
    def to_dict(self) -> dict:
        """Convert task to dictionary for saving."""
        return {
            "id": self._id,
            "name": self._name,
            "description": self._description,
            "type": self._type.name,
            "duration_seconds": self._duration.total_seconds(),
            "prerequisites": [
                {
                    "task_id": p.task_id,
                    "skill_name": p.skill_name,
                    "skill_level": p.skill_level,
                    "building_type": p.building_type,
                    "resource_type": p.resource_type.name if p.resource_type else None,
                    "resource_quantity": p.resource_quantity,
                    "resource_quality": p.resource_quality,
                    "season": p.season,
                    "weather_type": p.weather_type,
                    "time_range": p.time_range,
                    "village_level": p.village_level
                }
                for p in self._prerequisites
            ],
            "required_resources": [
                {
                    "type": r.type.name,
                    "quantity": r.quantity,
                    "min_quality": r.min_quality,
                    "consumed": r.consumed
                }
                for r in self._required_resources
            ],
            "required_tools": [
                {
                    "type": t.type.name,
                    "quantity": t.quantity,
                    "min_quality": t.min_quality,
                    "consumed": t.consumed
                }
                for t in self._required_tools
            ],
            "resource_rewards": [
                {
                    "type": r.type.name,
                    "base_quantity": r.base_quantity,
                    "quality_multiplier": r.quality_multiplier,
                    "skill_multiplier": r.skill_multiplier,
                    "random_bonus": r.random_bonus
                }
                for r in self._resource_rewards
            ],
            "skill_requirements": self._skill_requirements,
            "skill_rewards": self._skill_rewards,
            "reputation_reward": self._reputation_reward,
            "village_exp_reward": self._village_exp_reward,
            "valid_time_ranges": self._valid_time_ranges,
            "season_multipliers": self._season_multipliers,
            "weather_requirements": self._weather_requirements,
            "status": self._status.name,
            "progress": self._progress,
            "start_time": self._start_time.isoformat() if self._start_time else None,
            "rewards_claimed": self._rewards_claimed,
            "chain_id": self._chain_id,
            "event_id": self._event_id
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Task':
        """Create task from dictionary."""
        prerequisites = [
            TaskPrerequisite(
                task_id=p["task_id"],
                skill_name=p["skill_name"],
                skill_level=p["skill_level"],
                building_type=p["building_type"],
                resource_type=ResourceType[p["resource_type"]] if p["resource_type"] else None,
                resource_quantity=p["resource_quantity"],
                resource_quality=p["resource_quality"],
                season=p["season"],
                weather_type=p["weather_type"],
                time_range=p["time_range"],
                village_level=p["village_level"]
            )
            for p in data["prerequisites"]
        ]
        
        required_resources = [
            ResourceRequirement(
                type=ResourceType[r["type"]],
                quantity=r["quantity"],
                min_quality=r["min_quality"],
                consumed=r["consumed"]
            )
            for r in data["required_resources"]
        ]
        
        required_tools = [
            ResourceRequirement(
                type=ResourceType[t["type"]],
                quantity=t["quantity"],
                min_quality=t["min_quality"],
                consumed=t["consumed"]
            )
            for t in data["required_tools"]
        ]
        
        resource_rewards = [
            ResourceReward(
                type=ResourceType[r["type"]],
                base_quantity=r["base_quantity"],
                quality_multiplier=r["quality_multiplier"],
                skill_multiplier=r["skill_multiplier"],
                random_bonus=r["random_bonus"]
            )
            for r in data["resource_rewards"]
        ]
        
        task = cls(
            name=data["name"],
            description=data["description"],
            task_type=TaskType[data["type"]],
            duration=timedelta(seconds=data["duration_seconds"]),
            prerequisites=prerequisites,
            required_resources=required_resources,
            required_tools=required_tools,
            resource_rewards=resource_rewards,
            skill_requirements=data["skill_requirements"],
            skill_rewards=data["skill_rewards"],
            reputation_reward=data["reputation_reward"],
            village_exp_reward=data["village_exp_reward"],
            valid_time_ranges=data["valid_time_ranges"],
            season_multipliers=data["season_multipliers"],
            weather_requirements=data["weather_requirements"],
            chain_id=data["chain_id"],
            event_id=data["event_id"]
        )
        
        # Set state
        task._id = data["id"]
        task._status = TaskStatus[data["status"]]
        task._progress = data["progress"]
        task._start_time = datetime.fromisoformat(data["start_time"]) if data["start_time"] else None
        task._rewards_claimed = data["rewards_claimed"]
        
        return task 