from typing import Dict, List, Optional, Set
import json
import logging
import os
from datetime import datetime

from .task_template import TaskTemplate, TaskChain
from .task import Task, TaskStatus
from .resource_manager import ResourceType

# Set up logging
logging.basicConfig(
    filename='game.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TaskTemplateManager:
    """Manages task templates and chains, handles task generation."""
    
    def __init__(self, templates_dir: str = "data/templates"):
        self.templates_dir = templates_dir
        self.task_templates: Dict[str, TaskTemplate] = {}
        self.task_chains: Dict[str, TaskChain] = {}
        self.completed_chains: Set[str] = set()
        self.chain_cooldowns: Dict[str, datetime] = {}
        
        # Ensure templates directory exists
        os.makedirs(templates_dir, exist_ok=True)
        
        # Load templates and chains
        self.load_templates()
        logger.info(f"Loaded {len(self.task_templates)} task templates and {len(self.task_chains)} task chains")
    
    def load_templates(self) -> None:
        """Load all task templates and chains from files."""
        # Load task chains first
        chains_file = os.path.join(self.templates_dir, "task_chains.json")
        if os.path.exists(chains_file):
            try:
                with open(chains_file, 'r') as f:
                    chains_data = json.load(f)
                for chain_data in chains_data:
                    chain = TaskChain.from_dict(chain_data)
                    self.task_chains[chain.id] = chain
                logger.info(f"Loaded {len(self.task_chains)} task chains")
            except Exception as e:
                logger.error(f"Error loading task chains: {e}")
        
        # Load task templates
        templates_file = os.path.join(self.templates_dir, "task_templates.json")
        if os.path.exists(templates_file):
            try:
                with open(templates_file, 'r') as f:
                    templates_data = json.load(f)
                for template_data in templates_data:
                    template = TaskTemplate.from_dict(template_data)
                    self.task_templates[template.id] = template
                logger.info(f"Loaded {len(self.task_templates)} task templates")
            except Exception as e:
                logger.error(f"Error loading task templates: {e}")
    
    def save_templates(self) -> None:
        """Save all task templates and chains to files."""
        # Save task chains
        chains_file = os.path.join(self.templates_dir, "task_chains.json")
        try:
            chains_data = [chain.to_dict() for chain in self.task_chains.values()]
            with open(chains_file, 'w') as f:
                json.dump(chains_data, f, indent=2)
            logger.info(f"Saved {len(self.task_chains)} task chains")
        except Exception as e:
            logger.error(f"Error saving task chains: {e}")
        
        # Save task templates
        templates_file = os.path.join(self.templates_dir, "task_templates.json")
        try:
            templates_data = [template.to_dict() for template in self.task_templates.values()]
            with open(templates_file, 'w') as f:
                json.dump(templates_data, f, indent=2)
            logger.info(f"Saved {len(self.task_templates)} task templates")
        except Exception as e:
            logger.error(f"Error saving task templates: {e}")
    
    def add_template(self, template: TaskTemplate) -> None:
        """Add a new task template."""
        self.task_templates[template.id] = template
        logger.info(f"Added task template: {template.name} ({template.id})")
    
    def add_chain(self, chain: TaskChain) -> None:
        """Add a new task chain."""
        self.task_chains[chain.id] = chain
        logger.info(f"Added task chain: {chain.name} ({chain.id})")
    
    def get_available_chains(
        self,
        village_level: int,
        reputation: float,
        completed_tasks: Set[str],
        season: str,
        weather: str,
        current_time: datetime
    ) -> List[TaskChain]:
        """Get all task chains available to start."""
        available_chains = []
        
        for chain in self.task_chains.values():
            # Skip if chain is completed and not repeatable
            if chain.id in self.completed_chains and not chain.is_repeatable:
                continue
            
            # Check cooldown
            if chain.id in self.chain_cooldowns:
                if chain.cooldown and current_time < self.chain_cooldowns[chain.id]:
                    continue
            
            # Check village level and reputation
            if village_level < chain.village_level_required:
                continue
            if reputation < chain.reputation_required:
                continue
            
            # Check season and weather availability
            if chain.season_availability and season not in chain.season_availability:
                continue
            if chain.weather_availability and weather not in chain.weather_availability:
                continue
            
            # Check prerequisites
            prerequisites_met = True
            for prereq_chain_id in chain.prerequisites:
                if prereq_chain_id not in self.completed_chains:
                    prerequisites_met = False
                    break
            
            if prerequisites_met:
                available_chains.append(chain)
        
        return available_chains
    
    def get_chain_tasks(
        self,
        chain_id: str,
        village_level: int,
        completed_tasks: Set[str]
    ) -> List[TaskTemplate]:
        """Get all tasks in a chain, with difficulty scaled by village level."""
        chain = self.task_chains.get(chain_id)
        if not chain:
            return []
        
        chain_tasks = []
        for task_id in chain.tasks:
            template = self.task_templates.get(task_id)
            if template:
                # Scale difficulty based on village level
                if village_level > 1:
                    template = self._scale_template_difficulty(template, village_level)
                chain_tasks.append(template)
        
        return chain_tasks
    
    def _scale_template_difficulty(
        self,
        template: TaskTemplate,
        village_level: int
    ) -> TaskTemplate:
        """Create a new template with scaled difficulty based on village level."""
        scaling_factor = (village_level - 1) * template.difficulty_scaling
        reward_factor = 1.0 + (scaling_factor * template.reward_scaling)
        
        # Create a new template with scaled values
        scaled = TaskTemplate(
            id=template.id,
            name=template.name,
            description=template.description,
            type=template.type,
            base_duration=template.base_duration,
            prerequisites=template.prerequisites.copy(),
            required_resources=[
                ResourceRequirement(
                    type=r.type,
                    quantity=r.quantity * (1.0 + scaling_factor),
                    min_quality=min(1.0, r.min_quality * (1.0 + scaling_factor * 0.5)),
                    consumed=r.consumed
                )
                for r in template.required_resources
            ],
            required_tools=[
                ResourceRequirement(
                    type=t.type,
                    quantity=t.quantity,
                    min_quality=min(1.0, t.min_quality * (1.0 + scaling_factor * 0.3)),
                    consumed=t.consumed
                )
                for t in template.required_tools
            ],
            resource_rewards=[
                ResourceReward(
                    type=r.type,
                    base_quantity=r.base_quantity * reward_factor,
                    quality_multiplier=r.quality_multiplier,
                    skill_multiplier=r.skill_multiplier,
                    random_bonus=r.random_bonus
                )
                for r in template.resource_rewards
            ],
            skill_requirements={
                skill: level * (1.0 + scaling_factor * 0.5)
                for skill, level in template.skill_requirements.items()
            },
            skill_rewards={
                skill: xp * reward_factor
                for skill, xp in template.skill_rewards.items()
            },
            base_reputation_reward=template.base_reputation_reward * reward_factor,
            base_village_exp_reward=template.base_village_exp_reward * reward_factor,
            valid_time_ranges=template.valid_time_ranges.copy(),
            season_multipliers=template.season_multipliers.copy(),
            weather_requirements=template.weather_requirements.copy(),
            chain_id=template.chain_id,
            position_in_chain=template.position_in_chain,
            difficulty_scaling=template.difficulty_scaling,
            reward_scaling=template.reward_scaling,
            is_hidden=template.is_hidden
        )
        
        return scaled
    
    def generate_task(
        self,
        template: TaskTemplate,
        current_time: datetime
    ) -> Task:
        """Generate a new task instance from a template."""
        return Task(
            id=template.id,
            name=template.name,
            description=template.description,
            type=template.type,
            duration=template.base_duration,
            prerequisites=template.prerequisites.copy(),
            required_resources=template.required_resources.copy(),
            required_tools=template.required_tools.copy(),
            resource_rewards=template.resource_rewards.copy(),
            skill_requirements=template.skill_requirements.copy(),
            skill_rewards=template.skill_rewards.copy(),
            reputation_reward=template.base_reputation_reward,
            village_exp_reward=template.base_village_exp_reward,
            valid_time_ranges=template.valid_time_ranges.copy(),
            season_multipliers=template.season_multipliers.copy(),
            weather_requirements=template.weather_requirements.copy(),
            status=TaskStatus.AVAILABLE,
            progress=0.0,
            start_time=None,
            rewards_claimed=False,
            chain_id=template.chain_id,
            event_id=None
        )
    
    def mark_chain_completed(
        self,
        chain_id: str,
        current_time: datetime
    ) -> None:
        """Mark a chain as completed and set cooldown if repeatable."""
        chain = self.task_chains.get(chain_id)
        if chain:
            self.completed_chains.add(chain_id)
            if chain.is_repeatable and chain.cooldown:
                self.chain_cooldowns[chain_id] = current_time + chain.cooldown
            logger.info(f"Marked chain as completed: {chain.name} ({chain_id})")
    
    def to_dict(self) -> dict:
        """Convert manager state to dictionary for saving."""
        return {
            "completed_chains": list(self.completed_chains),
            "chain_cooldowns": {
                chain_id: cooldown.isoformat()
                for chain_id, cooldown in self.chain_cooldowns.items()
            }
        }
    
    def load_state(self, data: dict) -> None:
        """Load manager state from dictionary."""
        self.completed_chains = set(data.get("completed_chains", []))
        self.chain_cooldowns = {
            chain_id: datetime.fromisoformat(cooldown_str)
            for chain_id, cooldown_str in data.get("chain_cooldowns", {}).items()
        }
        logger.info("Loaded task template manager state") 