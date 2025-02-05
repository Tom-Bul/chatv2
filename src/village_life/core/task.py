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
from .resource_types import ResourceType

# Set up logging
logging.basicConfig(
    filename='game.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TaskType(Enum):
    """Types of tasks available in the game."""
    GATHERING = auto()
    CRAFTING = auto()
    CONSTRUCTION = auto()
    PLANNING = auto()
    COMBAT = auto()
    SOCIAL = auto()
    EXPLORATION = auto()
    RESEARCH = auto()

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

@dataclass
class Task:
    """A task that can be performed by the player."""
    id: str
    name: str
    description: str
    type: TaskType
    duration: timedelta
    prerequisites: List[TaskPrerequisite]
    required_resources: List[ResourceRequirement]
    required_tools: List[ResourceRequirement]
    resource_rewards: List[ResourceReward]
    skill_requirements: Dict[str, float]
    skill_rewards: Dict[str, float]
    reputation_reward: float
    village_exp_reward: float
    valid_time_ranges: List[Tuple[int, int]]
    season_multipliers: Dict[str, float]
    weather_requirements: List[str]
    status: TaskStatus = TaskStatus.AVAILABLE
    progress: float = 0.0  # Progress from 0.0 to 1.0
    start_time: Optional[datetime] = None
    rewards_claimed: bool = False
    chain_id: Optional[str] = None
    event_id: Optional[str] = None

    def can_start(
        self,
        current_time: datetime,
        available_resources: Dict[ResourceType, Tuple[float, float]],
        completed_tasks: List[str],
        current_skills: Dict[str, float],
        current_season: str,
        current_weather: str
    ) -> Tuple[bool, str]:
        """Check if task can be started.
        Returns (can_start, reason_if_cannot)"""
        
        # Check prerequisites
        for prereq in self.prerequisites:
            # Check task completion
            if prereq.task_id and prereq.task_id not in completed_tasks:
                return False, f"Required task {prereq.task_id} not completed"
            
            # Check skill requirements
            if prereq.skill_name:
                if prereq.skill_name not in current_skills:
                    return False, f"Missing required skill: {prereq.skill_name}"
                if current_skills[prereq.skill_name] < prereq.skill_level:
                    return False, f"Skill {prereq.skill_name} too low"
            
            # Check resource requirements
            if prereq.resource_type:
                if prereq.resource_type not in available_resources:
                    return False, f"Missing required resource: {prereq.resource_type.name}"
                quantity, quality = available_resources[prereq.resource_type]
                if quantity < prereq.resource_quantity:
                    return False, f"Not enough {prereq.resource_type.name}"
                if quality < prereq.resource_quality:
                    return False, f"{prereq.resource_type.name} quality too low"
        
        # Check required resources
        for req in self.required_resources:
            if req.type not in available_resources:
                return False, f"Missing required resource: {req.type.name}"
            quantity, quality = available_resources[req.type]
            if quantity < req.quantity:
                return False, f"Not enough {req.type.name}"
            if quality < req.min_quality:
                return False, f"{req.type.name} quality too low"
        
        # Check required tools
        for tool in self.required_tools:
            if tool.type not in available_resources:
                return False, f"Missing required tool: {tool.type.name}"
            quantity, quality = available_resources[tool.type]
            if quantity < tool.quantity:
                return False, f"Not enough {tool.type.name}"
            if quality < tool.min_quality:
                return False, f"{tool.type.name} quality too low"
        
        # Check skill requirements
        for skill, level in self.skill_requirements.items():
            if skill not in current_skills:
                return False, f"Missing required skill: {skill}"
            if current_skills[skill] < level:
                return False, f"Skill {skill} too low"
        
        # Check season and weather
        if current_season not in self.season_multipliers:
            return False, f"Cannot be done in {current_season}"
        if current_weather not in self.weather_requirements:
            return False, f"Cannot be done in {current_weather} weather"
        
        # Check time of day
        current_hour = current_time.hour
        valid_time = False
        for start, end in self.valid_time_ranges:
            if start <= current_hour < end:
                valid_time = True
                break
        if not valid_time:
            return False, "Not the right time of day"
        
        return True, ""

    def start(self, current_time: datetime) -> None:
        """Start the task."""
        self.status = TaskStatus.IN_PROGRESS
        self.start_time = current_time
        self.progress = 0.0
        logger.info(f"Started task: {self.name}")

    def update_progress(
        self,
        time_passed: timedelta,
        current_season: str,
        current_weather: str
    ) -> None:
        """Update task progress based on time passed."""
        if self.status != TaskStatus.IN_PROGRESS:
            return
        
        # Calculate progress increase
        base_progress = time_passed.total_seconds() / self.duration.total_seconds()
        
        # Apply season multiplier
        season_mult = self.season_multipliers.get(current_season, 0.0)
        progress_increase = base_progress * season_mult
        
        # Update progress
        self.progress = min(1.0, self.progress + progress_increase)
        
        # Check if completed
        if self.progress >= 1.0:
            self.status = TaskStatus.COMPLETED
            logger.info(f"Completed task: {self.name}")

    def claim_rewards(
        self,
        skill_levels: Dict[str, float]
    ) -> Tuple[List[Tuple[ResourceType, float, float]], Dict[str, float], float, float]:
        """Claim task rewards.
        Returns (resource_rewards, skill_rewards, reputation, village_exp)"""
        if self.status != TaskStatus.COMPLETED or self.rewards_claimed:
            return [], {}, 0.0, 0.0
        
        self.rewards_claimed = True
        
        # Calculate resource rewards
        resource_rewards = []
        for reward in self.resource_rewards:
            # Apply skill multiplier
            skill_mult = 1.0
            for skill, level in skill_levels.items():
                skill_mult = max(skill_mult, level * reward.skill_multiplier)
            
            # Calculate final quantity and quality
            quantity = reward.base_quantity * skill_mult
            quality = min(1.0, skill_mult * reward.quality_multiplier)
            
            resource_rewards.append((reward.type, quantity, quality))
        
        return (
            resource_rewards,
            self.skill_rewards,
            self.reputation_reward,
            self.village_exp_reward
        )

    def apply_modifier(self, modifier: IModifier) -> 'Task':
        """Apply a modifier to this task."""
        modified = modifier.modify(self)
        if not isinstance(modified, Task):
            raise ValueError(f"Modifier returned invalid type: {type(modified)}")
        return modified
    
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met."""
        # This is just a placeholder - actual implementation would need game state
        return self.status != TaskStatus.LOCKED
    
    def apply_effects(self) -> None:
        """Apply task effects when completed."""
        if self.status != TaskStatus.COMPLETED or self.rewards_claimed:
            return
        
        publish_event(TaskEvent(
            task_id=self.id,
            action="complete",
            old_status=TaskStatus.IN_PROGRESS.name,
            new_status=TaskStatus.COMPLETED.name,
            progress=1.0
        ))
        
        self.rewards_claimed = True
    
    def update(self, delta_time: float) -> None:
        """Update task progress."""
        if self.status != TaskStatus.IN_PROGRESS:
            return
        
        # Apply modifiers to progress rate
        rate = 1.0
        for modifier in self._modifiers:
            rate = modifier.modify(rate)
        
        # Update progress
        progress_amount = delta_time / self.duration.total_seconds() * rate
        old_progress = self.progress
        self.progress = min(1.0, self.progress + progress_amount)
        
        # Publish progress event
        publish_event(TaskEvent(
            task_id=self.id,
            action="progress",
            progress=self.progress
        ))
        
        # Check for completion
        if self.progress >= 1.0 and old_progress < 1.0:
            self.status = TaskStatus.COMPLETED
            publish_event(TaskEvent(
                task_id=self.id,
                action="complete",
                old_status=TaskStatus.IN_PROGRESS.name,
                new_status=TaskStatus.COMPLETED.name,
                progress=1.0
            ))
    
    def to_dict(self) -> dict:
        """Convert task to dictionary for saving."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.type.name,
            "duration_seconds": self.duration.total_seconds(),
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
                for p in self.prerequisites
            ],
            "required_resources": [
                {
                    "type": r.type.name,
                    "quantity": r.quantity,
                    "min_quality": r.min_quality,
                    "consumed": r.consumed
                }
                for r in self.required_resources
            ],
            "required_tools": [
                {
                    "type": t.type.name,
                    "quantity": t.quantity,
                    "min_quality": t.min_quality,
                    "consumed": t.consumed
                }
                for t in self.required_tools
            ],
            "resource_rewards": [
                {
                    "type": r.type.name,
                    "base_quantity": r.base_quantity,
                    "quality_multiplier": r.quality_multiplier,
                    "skill_multiplier": r.skill_multiplier,
                    "random_bonus": r.random_bonus
                }
                for r in self.resource_rewards
            ],
            "skill_requirements": self.skill_requirements,
            "skill_rewards": self.skill_rewards,
            "reputation_reward": self.reputation_reward,
            "village_exp_reward": self.village_exp_reward,
            "valid_time_ranges": self.valid_time_ranges,
            "season_multipliers": self.season_multipliers,
            "weather_requirements": self.weather_requirements,
            "status": self.status.name,
            "progress": self.progress,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "rewards_claimed": self.rewards_claimed,
            "chain_id": self.chain_id,
            "event_id": self.event_id
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
            id=data["id"],
            name=data["name"],
            description=data["description"],
            type=TaskType[data["type"]],
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
        task.status = TaskStatus[data["status"]]
        task.progress = data["progress"]
        task.start_time = datetime.fromisoformat(data["start_time"]) if data["start_time"] else None
        task.rewards_claimed = data["rewards_claimed"]
        
        return task 