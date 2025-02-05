"""
Tests for the task management system.
"""

import unittest
from datetime import datetime, timedelta
from typing import Dict, List, Set, Tuple
from unittest.mock import Mock, patch

from src.core.task import (
    TaskType, TaskStatus, ResourceRequirement,
    ResourceReward, TaskPrerequisite, Task
)
from src.core.resource_manager import ResourceType
from src.core.modifiers import create_modifier

class TestTaskPrerequisite(unittest.TestCase):
    """Test the TaskPrerequisite class."""
    def setUp(self):
        self.prerequisite = TaskPrerequisite(
            task_id="test_task",
            skill_name="woodcutting",
            skill_level=5.0,
            building_type="sawmill",
            resource_type=ResourceType.WOOD,
            resource_quantity=10.0,
            resource_quality=0.8,
            season="SUMMER",
            weather_type="CLEAR",
            time_range=(8, 16),
            village_level=2
        )
    
    def test_prerequisite_creation(self):
        """Test creating task prerequisites."""
        self.assertEqual(self.prerequisite.task_id, "test_task")
        self.assertEqual(self.prerequisite.skill_name, "woodcutting")
        self.assertEqual(self.prerequisite.skill_level, 5.0)
        self.assertEqual(self.prerequisite.building_type, "sawmill")
        self.assertEqual(self.prerequisite.resource_type, ResourceType.WOOD)
        self.assertEqual(self.prerequisite.resource_quantity, 10.0)
        self.assertEqual(self.prerequisite.resource_quality, 0.8)
        self.assertEqual(self.prerequisite.season, "SUMMER")
        self.assertEqual(self.prerequisite.weather_type, "CLEAR")
        self.assertEqual(self.prerequisite.time_range, (8, 16))
        self.assertEqual(self.prerequisite.village_level, 2)
    
    def test_optional_fields(self):
        """Test creating prerequisites with optional fields."""
        prereq = TaskPrerequisite()
        self.assertIsNone(prereq.task_id)
        self.assertIsNone(prereq.skill_name)
        self.assertIsNone(prereq.skill_level)
        self.assertIsNone(prereq.building_type)
        self.assertIsNone(prereq.resource_type)
        self.assertIsNone(prereq.resource_quantity)
        self.assertIsNone(prereq.resource_quality)
        self.assertIsNone(prereq.season)
        self.assertIsNone(prereq.weather_type)
        self.assertIsNone(prereq.time_range)
        self.assertIsNone(prereq.village_level)

class TestResourceRequirement(unittest.TestCase):
    """Test the ResourceRequirement class."""
    def setUp(self):
        self.requirement = ResourceRequirement(
            type=ResourceType.WOOD,
            quantity=10.0,
            min_quality=0.8,
            consumed=True
        )
    
    def test_requirement_creation(self):
        """Test creating resource requirements."""
        self.assertEqual(self.requirement.type, ResourceType.WOOD)
        self.assertEqual(self.requirement.quantity, 10.0)
        self.assertEqual(self.requirement.min_quality, 0.8)
        self.assertTrue(self.requirement.consumed)
    
    def test_default_values(self):
        """Test default values for resource requirements."""
        req = ResourceRequirement(ResourceType.WOOD, 10.0)
        self.assertEqual(req.min_quality, 0.0)
        self.assertTrue(req.consumed)

class TestResourceReward(unittest.TestCase):
    """Test the ResourceReward class."""
    def setUp(self):
        self.reward = ResourceReward(
            type=ResourceType.WOOD,
            base_quantity=10.0,
            quality_multiplier=1.2,
            skill_multiplier=1.5,
            random_bonus=0.1
        )
    
    def test_reward_creation(self):
        """Test creating resource rewards."""
        self.assertEqual(self.reward.type, ResourceType.WOOD)
        self.assertEqual(self.reward.base_quantity, 10.0)
        self.assertEqual(self.reward.quality_multiplier, 1.2)
        self.assertEqual(self.reward.skill_multiplier, 1.5)
        self.assertEqual(self.reward.random_bonus, 0.1)
    
    def test_default_values(self):
        """Test default values for resource rewards."""
        reward = ResourceReward(ResourceType.WOOD, 10.0)
        self.assertEqual(reward.quality_multiplier, 1.0)
        self.assertEqual(reward.skill_multiplier, 1.0)
        self.assertEqual(reward.random_bonus, 0.0)

class TestTask(unittest.TestCase):
    """Test the Task class."""
    def setUp(self):
        self.task = Task(
            name="Test Task",
            description="A test task",
            task_type=TaskType.GATHERING,
            duration=timedelta(hours=1),
            prerequisites=[
                TaskPrerequisite(skill_name="woodcutting", skill_level=1.0)
            ],
            required_resources=[
                ResourceRequirement(ResourceType.WOOD, 5.0)
            ],
            required_tools=[
                ResourceRequirement(ResourceType.TOOLS, 1.0, consumed=False)
            ],
            resource_rewards=[
                ResourceReward(ResourceType.WOOD, 10.0)
            ],
            skill_requirements={"woodcutting": 1.0},
            skill_rewards={"woodcutting": 0.1},
            reputation_reward=5.0,
            village_exp_reward=10.0,
            valid_time_ranges=[(8, 16)],
            season_multipliers={"SUMMER": 1.2},
            weather_requirements=["CLEAR"]
        )
    
    def test_task_creation(self):
        """Test creating a task."""
        self.assertEqual(self.task._name, "Test Task")
        self.assertEqual(self.task._description, "A test task")
        self.assertEqual(self.task._type, TaskType.GATHERING)
        self.assertEqual(self.task._duration, timedelta(hours=1))
        self.assertEqual(len(self.task._prerequisites), 1)
        self.assertEqual(len(self.task._required_resources), 1)
        self.assertEqual(len(self.task._required_tools), 1)
        self.assertEqual(len(self.task._resource_rewards), 1)
        self.assertEqual(self.task._skill_requirements["woodcutting"], 1.0)
        self.assertEqual(self.task._skill_rewards["woodcutting"], 0.1)
        self.assertEqual(self.task._reputation_reward, 5.0)
        self.assertEqual(self.task._village_exp_reward, 10.0)
        self.assertEqual(self.task._valid_time_ranges, [(8, 16)])
        self.assertEqual(self.task._season_multipliers["SUMMER"], 1.2)
        self.assertEqual(self.task._weather_requirements, ["CLEAR"])
    
    def test_task_status(self):
        """Test task status management."""
        self.assertEqual(self.task.status, TaskStatus.AVAILABLE.name)
        
        # Start task
        current_time = datetime.now()
        self.task.start(current_time)
        self.assertEqual(self.task.status, TaskStatus.IN_PROGRESS.name)
        self.assertEqual(self.task.progress, 0.0)
        
        # Update progress
        self.task.update(1800.0)  # 30 minutes
        self.assertEqual(self.task.progress, 0.5)
        
        # Complete task
        self.task.update(1800.0)  # Another 30 minutes
        self.assertEqual(self.task.status, TaskStatus.COMPLETED.name)
        self.assertEqual(self.task.progress, 1.0)
    
    def test_task_prerequisites(self):
        """Test checking task prerequisites."""
        current_time = datetime(2024, 1, 1, 12, 0)  # Noon
        available_resources = {
            ResourceType.WOOD: (10.0, 1.0),
            ResourceType.TOOLS: (1.0, 1.0)
        }
        completed_tasks = {"previous_task"}
        current_skills = {"woodcutting": 2.0}
        season = "SUMMER"
        weather = "CLEAR"
        
        # Test valid conditions
        can_start, message = self.task.can_start(
            current_time,
            available_resources,
            completed_tasks,
            current_skills,
            season,
            weather
        )
        self.assertTrue(can_start)
        
        # Test invalid time
        invalid_time = datetime(2024, 1, 1, 20, 0)  # 8 PM
        can_start, message = self.task.can_start(
            invalid_time,
            available_resources,
            completed_tasks,
            current_skills,
            season,
            weather
        )
        self.assertFalse(can_start)
        
        # Test insufficient resources
        insufficient_resources = {
            ResourceType.WOOD: (1.0, 1.0),
            ResourceType.TOOLS: (1.0, 1.0)
        }
        can_start, message = self.task.can_start(
            current_time,
            insufficient_resources,
            completed_tasks,
            current_skills,
            season,
            weather
        )
        self.assertFalse(can_start)
        
        # Test insufficient skills
        insufficient_skills = {"woodcutting": 0.5}
        can_start, message = self.task.can_start(
            current_time,
            available_resources,
            completed_tasks,
            insufficient_skills,
            season,
            weather
        )
        self.assertFalse(can_start)
        
        # Test wrong weather
        can_start, message = self.task.can_start(
            current_time,
            available_resources,
            completed_tasks,
            current_skills,
            season,
            "RAINY"
        )
        self.assertFalse(can_start)
    
    def test_task_modification(self):
        """Test modifying task properties."""
        modifier = create_modifier("multiply", strength=2.0)
        modified = self.task.apply_modifier(modifier)
        
        self.assertEqual(modified._duration, self.task._duration)  # Duration unchanged
        self.assertEqual(modified.progress, self.task.progress)  # Progress unchanged
    
    def test_task_failure(self):
        """Test task failure handling."""
        self.task.start(datetime.now())
        self.task.update(900.0)  # 15 minutes
        
        self.task.fail("Test failure")
        self.assertEqual(self.task.status, TaskStatus.FAILED.name)
        
        # Cannot fail already failed task
        with self.assertRaises(ValueError):
            self.task.fail("Another failure")
    
    def test_task_serialization(self):
        """Test task serialization."""
        # Convert to dict
        data = self.task.to_dict()
        
        # Create new task from dict
        new_task = Task.from_dict(data)
        
        # Compare properties
        self.assertEqual(new_task._name, self.task._name)
        self.assertEqual(new_task._type, self.task._type)
        self.assertEqual(new_task._duration, self.task._duration)
        self.assertEqual(len(new_task._prerequisites), len(self.task._prerequisites))
        self.assertEqual(len(new_task._required_resources), len(self.task._required_resources))
        self.assertEqual(len(new_task._resource_rewards), len(self.task._resource_rewards))
        self.assertEqual(new_task._skill_requirements, self.task._skill_requirements)
        self.assertEqual(new_task._skill_rewards, self.task._skill_rewards)
        self.assertEqual(new_task._status, self.task._status)
        self.assertEqual(new_task.progress, self.task.progress)

if __name__ == '__main__':
    unittest.main() 