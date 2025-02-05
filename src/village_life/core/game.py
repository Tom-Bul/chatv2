from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum, auto
import json
import yaml
from pathlib import Path
import time
from village_life.ai import AIManager, DialogueManager, NPC, NPCRole, DialogueType
from village_life.core.time_manager import TimeManager, Season
from village_life.core.resource_manager import ResourceManager, ResourceType
from village_life.core.task_manager import TaskManager, TaskType, TaskStatus
from village_life.core.character import Character
from village_life.core.weather_manager import WeatherManager
import logging

# Set up logging
logging.basicConfig(
    filename='game.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SkillType(Enum):
    STRENGTH = auto()
    STAMINA = auto()
    KNOWLEDGE = auto()
    CRAFTING = auto()
    SOCIAL = auto()

@dataclass
class GameTime:
    real_time: datetime = field(default_factory=datetime.now)
    game_time: datetime = field(default_factory=datetime.now)
    time_scale: float = 1.0  # 1 real hour = 1 game hour
    fixed_time_step: float = 1/60  # 60 Hz update rate
    accumulator: float = 0.0
    last_update_time: float = field(default_factory=lambda: time.time())
    alpha: float = 0.0  # Interpolation factor
    
    def update(self) -> bool:
        """Update game time based on real time passed.
        Returns True if a fixed update should occur."""
        current_time = time.time()
        frame_time = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # Add frame time to accumulator
        self.accumulator += frame_time
        
        # Check if we should do a fixed update
        if self.accumulator >= self.fixed_time_step:
            # Update game time
            now = datetime.now()
            real_time_passed = now - self.real_time
            game_time_passed = real_time_passed * self.time_scale
            self.game_time += game_time_passed
            self.real_time = now
            
            # Consume time step
            self.accumulator -= self.fixed_time_step
            
            # Calculate alpha for interpolation
            self.alpha = self.accumulator / self.fixed_time_step
            return True
            
        return False

@dataclass
class Task:
    name: str
    description: str
    type: TaskType
    duration: Optional[timedelta] = None
    requirements: Dict[str, float] = field(default_factory=dict)
    rewards: Dict[str, float] = field(default_factory=dict)
    story_elements: Dict[str, str] = field(default_factory=dict)
    completed: bool = False
    started_at: Optional[datetime] = None

@dataclass
class Character:
    name: str
    stats: Dict[str, float] = field(default_factory=lambda: {
        "health": 100.0,
        "energy": 100.0,
        "happiness": 50.0
    })
    skills: Dict[SkillType, float] = field(default_factory=lambda: {
        skill: 0.0 for skill in SkillType
    })
    inventory: List[str] = field(default_factory=list)
    relationships: Dict[str, float] = field(default_factory=dict)
    
    def update_skill(self, skill: SkillType, value: float) -> None:
        """Update a skill value with diminishing returns."""
        current = self.skills[skill]
        # Harder to improve as skill gets higher
        improvement = value / (1 + current/50)
        self.skills[skill] = min(100, current + improvement)

class Game:
    def __init__(self, save_dir: Path = Path("saves")):
        self.save_dir = save_dir
        self.save_dir.mkdir(exist_ok=True)
        
        # Initialize managers
        self.time_manager = TimeManager()
        self.resource_manager = ResourceManager()
        self.ai_manager = AIManager()
        self.dialogue_manager = DialogueManager(self.ai_manager)
        self.task_manager = TaskManager()
        self.weather_manager = WeatherManager()
        
        self.character = None
        self.active_tasks: List[Task] = []
        self.completed_tasks: List[Task] = []
        
        # Load configuration
        self.config = self.load_config()
        
        # For interpolation
        self.previous_state = None
        self.current_state = self.get_current_state()
        
        # Village state
        self.npcs: Dict[str, NPC] = {}
        self.active_conversations: Dict[str, bool] = {}  # NPC ID -> is_talking
        
        logger.info("Game initialized")
    
    def load_config(self) -> dict:
        """Load game configuration from YAML."""
        config_path = Path("config/game.yaml")
        if not config_path.exists():
            return {}
        with open(config_path) as f:
            return yaml.safe_load(f)
    
    def create_character(self, name: str) -> None:
        """Create a new character."""
        self.character = Character(name=name)
    
    def add_task(self, task: Task) -> None:
        """Add a new task to active tasks."""
        self.active_tasks.append(task)
    
    def complete_task(self, task: Task) -> None:
        """Mark a task as completed and apply rewards."""
        if task not in self.active_tasks:
            return
            
        task.completed = True
        self.active_tasks.remove(task)
        self.completed_tasks.append(task)
        
        # Apply rewards
        for skill_name, value in task.rewards.items():
            try:
                skill = SkillType[skill_name.upper()]
                self.character.update_skill(skill, value)
            except KeyError:
                continue
    
    async def generate_initial_npcs(self, count: int = 3) -> None:
        """Generate initial NPCs for the village."""
        village_context = {
            "population": len(self.npcs),
            "player": {
                "name": self.character.name if self.character else "Unknown",
                "skills": self.character.skills if self.character else {}
            },
            "existing_npcs": [
                {
                    "name": npc.name,
                    "role": npc.role.name,
                    "skills": npc.skills
                }
                for npc in self.npcs.values()
            ]
        }
        
        for _ in range(count):
            npc_data = await self.ai_manager.generate_npc(village_context)
            npc = NPC(**npc_data)
            self.npcs[npc.id] = npc
            village_context["existing_npcs"].append({
                "name": npc.name,
                "role": npc.role.name,
                "skills": npc.skills
            })
    
    async def start_conversation(self, npc_id: str) -> Optional[str]:
        """Start a conversation with an NPC."""
        if npc_id not in self.npcs:
            return None
        
        npc = self.npcs[npc_id]
        if npc_id in self.active_conversations:
            return None
        
        self.active_conversations[npc_id] = True
        response = await self.dialogue_manager.start_conversation(
            npc,
            DialogueType.GREETING,
            "village"  # TODO: Track actual location
        )
        
        return response.text if response else None
    
    async def continue_conversation(
        self,
        npc_id: str,
        player_input: str
    ) -> Optional[str]:
        """Continue a conversation with an NPC."""
        if npc_id not in self.npcs or npc_id not in self.active_conversations:
            return None
        
        npc = self.npcs[npc_id]
        response = await self.dialogue_manager.continue_conversation(
            npc,
            player_input
        )
        
        return response.text if response else None
    
    async def end_conversation(self, npc_id: str) -> Optional[str]:
        """End a conversation with an NPC."""
        if npc_id not in self.npcs or npc_id not in self.active_conversations:
            return None
        
        npc = self.npcs[npc_id]
        response = await self.dialogue_manager.end_conversation(npc)
        del self.active_conversations[npc_id]
        
        return response.text if response else None
    
    def update(self) -> None:
        """Update game state using fixed time step."""
        if self.time_manager.update():  # Only update on fixed time step
            # Store previous state for interpolation
            self.previous_state = self.current_state
            
            # Get time passed and season effects
            time_passed = timedelta(seconds=self.time_manager.fixed_time_step)
            season_effects = self.time_manager.get_season_effects()
            
            # Update resources
            self.resource_manager.update(time_passed, season_effects)
            
            # Update active tasks
            current_time = datetime.now()
            for task in self.active_tasks:
                if task.started_at and task.duration:
                    if current_time - task.started_at >= task.duration:
                        # Apply seasonal effects to rewards
                        if task.type == TaskType.CRAFTING:
                            task.rewards = {
                                k: v * season_effects.get("crafting", 1.0)
                                for k, v in task.rewards.items()
                            }
                        elif task.type == TaskType.EXERCISE:
                            task.rewards = {
                                k: v * season_effects.get("energy_cost", 1.0)
                                for k, v in task.rewards.items()
                            }
                        self.complete_task(task)
            
            # Update NPCs based on time of day
            time_of_day = self.time_manager.get_time_of_day()
            for npc in self.npcs.values():
                activity = npc.get_current_activity(current_time)
                if time_of_day == "night" and npc.id in self.active_conversations:
                    # End conversations at night
                    self.end_conversation(npc.id)
            
            # Store new state
            self.current_state = self.get_current_state()
    
    def get_current_state(self) -> dict:
        """Get current game state for interpolation."""
        if not self.character:
            return {}
            
        return {
            "stats": self.character.stats.copy(),
            "skills": {k: v for k, v in self.character.skills.items()},
            "tasks": [(t.name, t.duration.total_seconds() if t.duration else 0) 
                     for t in self.active_tasks],
            "time": {
                "formatted": self.time_manager.get_formatted_date(),
                "is_daytime": self.time_manager.is_daytime(),
                "day_progress": self.time_manager.get_day_progress(),
                "season_progress": self.time_manager.get_season_progress(),
                "season_effects": self.time_manager.get_season_effects()
            },
            "resources": self.resource_manager.get_storage_info()
        }
    
    def save_game(self, slot: str = "autosave") -> None:
        """Save the game state."""
        save_path = self.save_dir / f"{slot}.json"
        
        save_data = {
            "time": self.time_manager.save_state(),
            "resources": self.resource_manager.save_state(),
            "character": {
                "name": self.character.name,
                "stats": self.character.stats,
                "skills": {k.name: v for k, v in self.character.skills.items()},
                "inventory": self.character.inventory,
                "relationships": self.character.relationships
            },
            "tasks": {
                "active": [{
                    "name": t.name,
                    "description": t.description,
                    "type": t.type.name,
                    "duration": t.duration.total_seconds() if t.duration else None,
                    "requirements": t.requirements,
                    "rewards": t.rewards,
                    "story_elements": t.story_elements,
                    "completed": t.completed,
                    "started_at": t.started_at.isoformat() if t.started_at else None
                } for t in self.active_tasks],
                "completed": [{
                    "name": t.name,
                    "description": t.description,
                    "type": t.type.name,
                    "duration": t.duration.total_seconds() if t.duration else None,
                    "requirements": t.requirements,
                    "rewards": t.rewards,
                    "story_elements": t.story_elements,
                    "completed": t.completed,
                    "started_at": t.started_at.isoformat() if t.started_at else None
                } for t in self.completed_tasks]
            },
            "npcs": {
                npc_id: {
                    "id": npc.id,
                    "name": npc.name,
                    "role": npc.role.name,
                    "personality": vars(npc.personality),
                    "background": npc.background,
                    "skills": npc.skills,
                    "relationships": npc.relationships,
                    "schedule": vars(npc.schedule)
                }
                for npc_id, npc in self.npcs.items()
            }
        }
        
        with open(save_path, 'w') as f:
            json.dump(save_data, f, indent=2)
    
    def load_game(self, slot: str = "autosave") -> bool:
        """Load a saved game state."""
        save_path = self.save_dir / f"{slot}.json"
        if not save_path.exists():
            return False
            
        with open(save_path) as f:
            save_data = json.load(f)
        
        # Restore manager states
        self.time_manager.load_state(save_data["time"])
        self.resource_manager.load_state(save_data["resources"])
        
        # Restore character
        char_data = save_data["character"]
        self.character = Character(
            name=char_data["name"],
            stats=char_data["stats"],
            skills={SkillType[k]: v for k, v in char_data["skills"].items()},
            inventory=char_data["inventory"],
            relationships=char_data["relationships"]
        )
        
        # Restore tasks
        def create_task(data: dict) -> Task:
            return Task(
                name=data["name"],
                description=data["description"],
                type=TaskType[data["type"]],
                duration=timedelta(seconds=data["duration"]) if data["duration"] else None,
                requirements=data["requirements"],
                rewards=data["rewards"],
                story_elements=data["story_elements"],
                completed=data["completed"],
                started_at=datetime.fromisoformat(data["started_at"]) if data["started_at"] else None
            )
        
        self.active_tasks = [create_task(t) for t in save_data["tasks"]["active"]]
        self.completed_tasks = [create_task(t) for t in save_data["tasks"]["completed"]]
        
        # Restore NPCs
        self.npcs = {}
        for npc_id, npc_data in save_data["npcs"].items():
            self.npcs[npc_id] = NPC(
                id=npc_data["id"],
                name=npc_data["name"],
                role=NPCRole[npc_data["role"]],
                personality=NPCPersonality(**npc_data["personality"]),
                background=npc_data["background"],
                skills=npc_data["skills"],
                relationships=npc_data["relationships"],
                schedule=NPCSchedule(**npc_data["schedule"])
            )
        
        return True
    
    def get_interpolated_state(self) -> dict:
        """Get interpolated game state for rendering."""
        if not self.previous_state or not self.current_state:
            return self.current_state or {}
            
        alpha = self.time_manager.alpha
        interpolated = {}
        
        # Interpolate stats
        if "stats" in self.previous_state and "stats" in self.current_state:
            interpolated["stats"] = {}
            for key in self.previous_state["stats"]:
                prev = self.previous_state["stats"][key]
                curr = self.current_state["stats"][key]
                interpolated["stats"][key] = prev + (curr - prev) * alpha
        
        # Interpolate skills
        if "skills" in self.previous_state and "skills" in self.current_state:
            interpolated["skills"] = {}
            for key in self.previous_state["skills"]:
                prev = self.previous_state["skills"][key]
                curr = self.current_state["skills"][key]
                interpolated["skills"][key] = prev + (curr - prev) * alpha
        
        return interpolated 