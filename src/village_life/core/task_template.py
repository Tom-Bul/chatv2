from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from datetime import timedelta
import uuid
import logging

from .task import TaskType, ResourceRequirement, ResourceReward, TaskPrerequisite
from .resource_types import ResourceType

# Set up logging
logging.basicConfig(
    filename='game.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TaskChain:
    """Represents a sequence of related tasks that form a progression chain."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    prerequisites: List[str] = field(default_factory=list)  # List of required chain IDs
    tasks: List[str] = field(default_factory=list)  # List of task template IDs in order
    village_level_required: int = 0
    reputation_required: float = 0.0
    is_repeatable: bool = False
    cooldown: Optional[timedelta] = None
    season_availability: Set[str] = field(default_factory=set)
    weather_availability: Set[str] = field(default_factory=set)
    
    def to_dict(self) -> dict:
        """Convert chain to dictionary for saving."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "prerequisites": self.prerequisites,
            "tasks": self.tasks,
            "village_level_required": self.village_level_required,
            "reputation_required": self.reputation_required,
            "is_repeatable": self.is_repeatable,
            "cooldown_seconds": self.cooldown.total_seconds() if self.cooldown else None,
            "season_availability": list(self.season_availability),
            "weather_availability": list(self.weather_availability)
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TaskChain':
        """Create chain from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            prerequisites=data.get("prerequisites", []),
            tasks=data.get("tasks", []),
            village_level_required=data.get("village_level_required", 0),
            reputation_required=data.get("reputation_required", 0.0),
            is_repeatable=data.get("is_repeatable", False),
            cooldown=timedelta(seconds=data["cooldown_seconds"]) if data.get("cooldown_seconds") else None,
            season_availability=set(data.get("season_availability", [])),
            weather_availability=set(data.get("weather_availability", []))
        )

@dataclass
class TaskTemplate:
    """Template for generating tasks with consistent properties."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    type: TaskType = TaskType.GATHERING
    base_duration: timedelta = field(default_factory=lambda: timedelta(minutes=30))
    prerequisites: List[TaskPrerequisite] = field(default_factory=list)
    required_resources: List[ResourceRequirement] = field(default_factory=list)
    required_tools: List[ResourceRequirement] = field(default_factory=list)
    resource_rewards: List[ResourceReward] = field(default_factory=list)
    skill_requirements: Dict[str, float] = field(default_factory=dict)
    skill_rewards: Dict[str, float] = field(default_factory=dict)
    base_reputation_reward: float = 0.0
    base_village_exp_reward: float = 0.0
    valid_time_ranges: List[tuple[int, int]] = field(default_factory=list)
    season_multipliers: Dict[str, float] = field(default_factory=dict)
    weather_requirements: List[str] = field(default_factory=list)
    chain_id: Optional[str] = None
    position_in_chain: int = 0
    difficulty_scaling: float = 1.0  # How much requirements scale with village level
    reward_scaling: float = 1.0  # How much rewards scale with difficulty
    is_hidden: bool = False  # Whether task is visible before prerequisites are met
    
    def to_dict(self) -> dict:
        """Convert template to dictionary for saving."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.type.name,
            "base_duration_seconds": self.base_duration.total_seconds(),
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
            "base_reputation_reward": self.base_reputation_reward,
            "base_village_exp_reward": self.base_village_exp_reward,
            "valid_time_ranges": self.valid_time_ranges,
            "season_multipliers": self.season_multipliers,
            "weather_requirements": self.weather_requirements,
            "chain_id": self.chain_id,
            "position_in_chain": self.position_in_chain,
            "difficulty_scaling": self.difficulty_scaling,
            "reward_scaling": self.reward_scaling,
            "is_hidden": self.is_hidden
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TaskTemplate':
        """Create template from dictionary."""
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
        
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            type=TaskType[data["type"]],
            base_duration=timedelta(seconds=data["base_duration_seconds"]),
            prerequisites=prerequisites,
            required_resources=required_resources,
            required_tools=required_tools,
            resource_rewards=resource_rewards,
            skill_requirements=data["skill_requirements"],
            skill_rewards=data["skill_rewards"],
            base_reputation_reward=data["base_reputation_reward"],
            base_village_exp_reward=data["base_village_exp_reward"],
            valid_time_ranges=data["valid_time_ranges"],
            season_multipliers=data["season_multipliers"],
            weather_requirements=data["weather_requirements"],
            chain_id=data["chain_id"],
            position_in_chain=data["position_in_chain"],
            difficulty_scaling=data["difficulty_scaling"],
            reward_scaling=data["reward_scaling"],
            is_hidden=data["is_hidden"]
        ) 