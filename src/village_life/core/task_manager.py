from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
import logging
import json
from pathlib import Path
import uuid

from .task import Task, TaskType, TaskStatus, ResourceRequirement, ResourceReward
from .resource_types import ResourceType
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
    
    def start_task(
        self,
        task_id: str,
        current_time: datetime,
        available_resources: Dict[ResourceType, Tuple[float, float]],
        completed_tasks: List[str],
        current_skills: Dict[str, float],
        current_season: str,
        current_weather: str
    ) -> Tuple[bool, str]:
        """Start a task if possible."""
        if task_id in self.active_tasks:
            return False, "Task already active"
        
        # Get task template
        template = self.template_manager.task_templates.get(task_id)
        if not template:
            return False, "Invalid task ID"
        
        # Create task instance
        task = self.template_manager.generate_task(template, current_time)
        
        # Check if task can be started
        can_start, reason = task.can_start(
            current_time,
            available_resources,
            completed_tasks,
            current_skills,
            current_season,
            current_weather
        )
        
        if not can_start:
            return False, reason
        
        # Start task
        task.start(current_time)
        self.active_tasks[task_id] = task
        logger.info(f"Started task: {task.name} ({task_id})")
        
        return True, ""
    
    def fail_task(self, task_id: str, reason: str) -> bool:
        """Mark a task as failed."""
        if task_id not in self.active_tasks:
            return False
        
        task = self.active_tasks[task_id]
        task.status = TaskStatus.FAILED
        self.failed_tasks[task_id] = task
        del self.active_tasks[task_id]
        
        logger.info(f"Failed task: {task.name} ({task_id}) - {reason}")
        return True
    
    def get_available_tasks(
        self,
        current_time: datetime,
        available_resources: Dict[ResourceType, Tuple[float, float]],
        completed_tasks: List[str],
        current_skills: Dict[str, float],
        current_season: str,
        current_weather: str,
        village_level: int
    ) -> List[dict]:
        """Get list of available tasks."""
        available_tasks = []
        
        for template in self.template_manager.task_templates.values():
            # Skip hidden tasks
            if template.is_hidden:
                continue
            
            # Skip tasks in active chains that aren't next
            if template.chain_id:
                chain = self.template_manager.task_chains.get(template.chain_id)
                if chain:
                    # Check if chain is available
                    if chain.village_level_required > village_level:
                        continue
                    
                    # Check if chain prerequisites are met
                    chain_prereqs_met = True
                    for prereq_chain_id in chain.prerequisites:
                        if prereq_chain_id not in self.template_manager.completed_chains:
                            chain_prereqs_met = False
                            break
                    
                    if not chain_prereqs_met:
                        continue
                    
                    # Check if this is the next task in chain
                    chain_position = 0
                    for chain_task_id in chain.tasks:
                        if chain_task_id == template.id:
                            break
                        chain_position += 1
                        if chain_task_id not in completed_tasks:
                            # Found an uncompleted task before this one
                            continue
            
            # Check if task can be started
            task = self.template_manager.generate_task(template, current_time)
            can_start, reason = task.can_start(
                current_time,
                available_resources,
                completed_tasks,
                current_skills,
                current_season,
                current_weather
            )
            
            available_tasks.append({
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "type": template.type.name,
                "duration": template.base_duration,
                "can_start": can_start,
                "reason": reason if not can_start else None,
                "chain_id": template.chain_id,
                "position_in_chain": template.position_in_chain
            })
        
        return available_tasks
    
    def get_task_info(self, task_id: str) -> Optional[dict]:
        """Get detailed information about a task."""
        # Check active tasks
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            return {
                "id": task_id,
                "name": task.name,
                "description": task.description,
                "type": task.type.name,
                "status": task.status.name,
                "progress": task.progress,
                "start_time": task.start_time,
                "chain_id": task.chain_id,
                "rewards_claimed": task.rewards_claimed
            }
        
        # Check completed tasks
        if task_id in self.completed_tasks:
            task = self.completed_tasks[task_id]
            return {
                "id": task_id,
                "name": task.name,
                "description": task.description,
                "type": task.type.name,
                "status": task.status.name,
                "progress": task.progress,
                "start_time": task.start_time,
                "chain_id": task.chain_id,
                "rewards_claimed": task.rewards_claimed
            }
        
        # Check failed tasks
        if task_id in self.failed_tasks:
            task = self.failed_tasks[task_id]
            return {
                "id": task_id,
                "name": task.name,
                "description": task.description,
                "type": task.type.name,
                "status": task.status.name,
                "progress": task.progress,
                "start_time": task.start_time,
                "chain_id": task.chain_id,
                "rewards_claimed": task.rewards_claimed
            }
        
        return None
    
    def get_task_status(self) -> dict:
        """Get status of all tasks."""
        return {
            "active": [
                {
                    "id": task_id,
                    "name": task.name,
                    "type": task.type.name,
                    "progress": task.progress,
                    "start_time": task.start_time
                }
                for task_id, task in self.active_tasks.items()
            ],
            "completed": [
                {
                    "id": task_id,
                    "name": task.name,
                    "type": task.type.name,
                    "rewards_claimed": task.rewards_claimed
                }
                for task_id, task in self.completed_tasks.items()
            ],
            "failed": [
                {
                    "id": task_id,
                    "name": task.name,
                    "type": task.type.name
                }
                for task_id, task in self.failed_tasks.items()
            ]
        }
    
    def save_state(self) -> dict:
        """Save task manager state."""
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
    
    def load_state(self, data: dict) -> None:
        """Load task manager state."""
        # Load tasks
        self.active_tasks = {
            task_id: Task.from_dict(task_data)
            for task_id, task_data in data.get("active_tasks", {}).items()
        }
        
        self.completed_tasks = {
            task_id: Task.from_dict(task_data)
            for task_id, task_data in data.get("completed_tasks", {}).items()
        }
        
        self.failed_tasks = {
            task_id: Task.from_dict(task_data)
            for task_id, task_data in data.get("failed_tasks", {}).items()
        }
        
        # Load template manager state
        if "template_manager" in data:
            self.template_manager.load_state(data["template_manager"])
        
        logger.info("Loaded task manager state") 