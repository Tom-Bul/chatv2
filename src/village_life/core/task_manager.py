from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
import logging
import json
from pathlib import Path
import uuid

from .task import Task, TaskType, TaskStatus, ResourceRequirement, ResourceReward
from .resource_manager import ResourceType
from .task_template import TaskTemplate, TaskChain
from .task_template_manager import TaskTemplateManager

# Set up logging
logging.basicConfig(
    filename='game.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TaskManager:
    def __init__(self, templates_dir: str = "data/templates"):
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, Task] = {}
        self.failed_tasks: Dict[str, Task] = {}
        self.template_manager = TaskTemplateManager(templates_dir)
        
        logger.info("Task manager initialized")
    
    def update_tasks(
        self,
        time_passed: timedelta,
        season: str,
        weather: str
    ) -> None:
        """Update all active tasks."""
        completed_tasks = []
        
        for task_id, task in self.active_tasks.items():
            task.update_progress(time_passed, season, weather)
            
            if task.status == TaskStatus.COMPLETED:
                completed_tasks.append(task_id)
                self.completed_tasks[task_id] = task
                logger.info(f"Task completed: {task.name} ({task_id})")
                
                # Check if this completes a chain
                if task.chain_id:
                    chain = self.template_manager.task_chains.get(task.chain_id)
                    if chain:
                        # Check if all tasks in chain are completed
                        chain_completed = True
                        for chain_task_id in chain.tasks:
                            if chain_task_id not in self.completed_tasks:
                                chain_completed = False
                                break
                        
                        if chain_completed:
                            self.template_manager.mark_chain_completed(
                                chain.id,
                                datetime.now()
                            )
                            logger.info(f"Chain completed: {chain.name} ({chain.id})")
        
        # Remove completed tasks from active tasks
        for task_id in completed_tasks:
            del self.active_tasks[task_id]
    
    def get_available_tasks(
        self,
        current_time: datetime,
        available_resources: Dict[ResourceType, Tuple[float, float]],
        current_skills: Dict[str, float],
        season: str,
        weather: str,
        village_level: int,
        reputation: float
    ) -> List[Tuple[Task, str]]:
        """Get all tasks that can be started."""
        available_tasks = []
        completed_task_ids = set(self.completed_tasks.keys())
        
        # Get available chains
        available_chains = self.template_manager.get_available_chains(
            village_level=village_level,
            reputation=reputation,
            completed_tasks=completed_task_ids,
            season=season,
            weather=weather,
            current_time=current_time
        )
        
        # Get tasks from available chains
        for chain in available_chains:
            chain_tasks = self.template_manager.get_chain_tasks(
                chain_id=chain.id,
                village_level=village_level,
                completed_tasks=completed_task_ids
            )
            
            for template in chain_tasks:
                # Skip if task is already active or completed
                if template.id in self.active_tasks or template.id in self.completed_tasks:
                    continue
                
                # Generate task from template
                task = self.template_manager.generate_task(template, current_time)
                
                # Check if task can be started
                can_start, reason = task.can_start(
                    current_time=current_time,
                    available_resources=available_resources,
                    completed_task_ids=completed_task_ids,
                    current_skills=current_skills,
                    season=season,
                    weather=weather
                )
                
                if can_start:
                    available_tasks.append((task, "Ready to start"))
                elif not template.is_hidden:
                    available_tasks.append((task, reason))
        
        return available_tasks
    
    def start_task(
        self,
        task_id: str,
        current_time: datetime
    ) -> Optional[str]:
        """Start a task."""
        # Find task in available tasks
        available_tasks = [task for task, _ in self.get_available_tasks(
            current_time=current_time,
            available_resources={},  # These will be checked by the task itself
            current_skills={},
            season="",
            weather="",
            village_level=0,
            reputation=0.0
        )]
        
        task = None
        for available_task in available_tasks:
            if available_task.id == task_id:
                task = available_task
                break
        
        if not task:
            return "Task not found or not available"
        
        # Start the task
        task.status = TaskStatus.IN_PROGRESS
        task.start_time = current_time
        task.progress = 0.0
        
        self.active_tasks[task_id] = task
        logger.info(f"Started task: {task.name} ({task_id})")
        
        return None
    
    def fail_task(self, task_id: str) -> None:
        """Mark a task as failed."""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.status = TaskStatus.FAILED
            self.failed_tasks[task_id] = task
            del self.active_tasks[task_id]
            logger.info(f"Failed task: {task.name} ({task_id})")
    
    def cancel_task(self, task_id: str) -> None:
        """Cancel an active task."""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            del self.active_tasks[task_id]
            logger.info(f"Cancelled task: {task.name} ({task_id})")
    
    def claim_task_rewards(
        self,
        task_id: str
    ) -> Optional[Tuple[List[ResourceReward], Dict[str, float], float, float]]:
        """Claim rewards for a completed task."""
        task = self.completed_tasks.get(task_id)
        if not task or task.rewards_claimed:
            return None
        
        task.rewards_claimed = True
        return (
            task.resource_rewards,
            task.skill_rewards,
            task.reputation_reward,
            task.village_exp_reward
        )
    
    def save_state(self) -> dict:
        """Convert manager state to dictionary for saving."""
        return {
            "active_tasks": {
                task_id: task.to_dict()
                for task_id, task in self.active_tasks.items()
            },
            "completed_tasks": {
                task_id: task.to_dict()
                for task_id, task in self.completed_tasks.items()
            },
            "failed_tasks": {
                task_id: task.to_dict()
                for task_id, task in self.failed_tasks.items()
            },
            "template_manager": self.template_manager.to_dict()
        }
    
    def load_state(self, state: dict) -> None:
        """Load manager state from dictionary."""
        self.active_tasks = {
            task_id: Task.from_dict(task_data)
            for task_id, task_data in state.get("active_tasks", {}).items()
        }
        
        self.completed_tasks = {
            task_id: Task.from_dict(task_data)
            for task_id, task_data in state.get("completed_tasks", {}).items()
        }
        
        self.failed_tasks = {
            task_id: Task.from_dict(task_data)
            for task_id, task_data in state.get("failed_tasks", {}).items()
        }
        
        self.template_manager.load_state(state.get("template_manager", {}))
        
        logger.info("Loaded task manager state") 