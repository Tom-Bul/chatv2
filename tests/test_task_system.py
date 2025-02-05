"""
Tests for the task management system.
"""

import unittest
from datetime import datetime, timedelta
from typing import Dict, List, Set, Tuple
from unittest.mock import Mock, patch

from src.village_life.core.task import (
    Task,
    TaskType,
    TaskStatus,
    ResourceRequirement,
    ResourceReward,
    TaskPrerequisite
)
from src.village_life.core.resource_types import ResourceType
from src.village_life.core.task_manager import TaskManager
from src.village_life.core.task_template import TaskTemplate, TaskChain

class TestTaskSystem(unittest.TestCase):
    """Test the task system."""
    def setUp(self):
        self.task_manager = TaskManager()
        self.current_time = datetime.now()
        self.available_resources = {
            ResourceType.WOOD: (100.0, 0.8),
            ResourceType.STONE: (50.0, 0.7),
            ResourceType.METAL: (20.0, 0.9),
            ResourceType.TOOLS: (5.0, 0.8),
            ResourceType.AXE: (2.0, 0.7),
            ResourceType.HAMMER: (2.0, 0.8),
            ResourceType.SAW: (1.0, 0.9)
        }
        self.current_skills = {
            "gathering": 10.0,
            "crafting": 15.0,
            "construction": 20.0,
            "planning": 5.0,
            "survival": 8.0
        }
        self.completed_tasks = []
    
    def test_task_template_loading(self):
        """Test loading task templates."""
        # Check if templates are loaded
        self.assertTrue(len(self.task_manager.template_manager.task_templates) > 0)
        self.assertTrue(len(self.task_manager.template_manager.task_chains) > 0)
        
        # Check specific templates
        templates = self.task_manager.template_manager.task_templates
        self.assertIn("scout_location", templates)
        self.assertIn("clear_land", templates)
        self.assertIn("build_shelter", templates)
        
        # Check template properties
        scout_template = templates["scout_location"]
        self.assertEqual(scout_template.type, TaskType.PLANNING)
        self.assertEqual(scout_template.base_duration, timedelta(hours=1))
        self.assertEqual(scout_template.chain_id, "village_establishment_1")
    
    def test_task_chain_loading(self):
        """Test loading task chains."""
        # Check if chains are loaded
        chains = self.task_manager.template_manager.task_chains
        self.assertIn("village_establishment_1", chains)
        self.assertIn("metal_processing_1", chains)
        
        # Check chain properties
        village_chain = chains["village_establishment_1"]
        self.assertEqual(len(village_chain.tasks), 4)
        self.assertEqual(village_chain.village_level_required, 0)
        self.assertFalse(village_chain.is_repeatable)
    
    def test_available_tasks(self):
        """Test getting available tasks."""
        available_tasks = self.task_manager.get_available_tasks(
            self.current_time,
            self.available_resources,
            self.completed_tasks,
            self.current_skills,
            "spring",
            "clear",
            0  # village level
        )
        
        # Should have at least the scout_location task
        self.assertTrue(len(available_tasks) > 0)
        scout_task = next(
            (task for task in available_tasks if task["id"] == "scout_location"),
            None
        )
        self.assertIsNotNone(scout_task)
        self.assertTrue(scout_task["can_start"])
    
    def test_task_progression(self):
        """Test task progression through a chain."""
        # Start with scout_location
        success, reason = self.task_manager.start_task(
            "scout_location",
            self.current_time,
            self.available_resources,
            self.completed_tasks,
            self.current_skills,
            "spring",
            "clear"
        )
        self.assertTrue(success, reason)
        
        # Update task to completion
        task = self.task_manager.active_tasks["scout_location"]
        self.task_manager.update_tasks(timedelta(hours=2), "spring", "clear")
        
        # Task should be completed
        self.assertNotIn("scout_location", self.task_manager.active_tasks)
        self.assertIn("scout_location", self.task_manager.completed_tasks)
        
        # Clear land should now be available
        self.completed_tasks.append("scout_location")
        available_tasks = self.task_manager.get_available_tasks(
            self.current_time,
            self.available_resources,
            self.completed_tasks,
            self.current_skills,
            "spring",
            "clear",
            0
        )
        clear_task = next(
            (task for task in available_tasks if task["id"] == "clear_land"),
            None
        )
        self.assertIsNotNone(clear_task)
        self.assertTrue(clear_task["can_start"])
    
    def test_task_requirements(self):
        """Test task requirement checking."""
        # Try to start build_shelter without prerequisites
        success, reason = self.task_manager.start_task(
            "build_shelter",
            self.current_time,
            self.available_resources,
            self.completed_tasks,
            self.current_skills,
            "spring",
            "clear"
        )
        self.assertFalse(success)
        self.assertIn("not completed", reason)
        
        # Try with insufficient resources
        insufficient_resources = {
            ResourceType.WOOD: (5.0, 0.8),  # Not enough wood
            ResourceType.STONE: (5.0, 0.7),  # Not enough stone
            ResourceType.HAMMER: (1.0, 0.8),
            ResourceType.SAW: (1.0, 0.9)
        }
        self.completed_tasks.extend(["scout_location", "clear_land"])
        success, reason = self.task_manager.start_task(
            "build_shelter",
            self.current_time,
            insufficient_resources,
            self.completed_tasks,
            self.current_skills,
            "spring",
            "clear"
        )
        self.assertFalse(success)
        self.assertIn("Not enough", reason)
    
    def test_task_rewards(self):
        """Test task reward calculation."""
        # Start and complete clear_land task
        success, reason = self.task_manager.start_task(
            "clear_land",
            self.current_time,
            self.available_resources,
            ["scout_location"],
            self.current_skills,
            "spring",
            "clear"
        )
        self.assertTrue(success, reason)
        
        # Complete task
        task = self.task_manager.active_tasks["clear_land"]
        self.task_manager.update_tasks(timedelta(hours=3), "spring", "clear")
        
        # Check rewards
        task = self.task_manager.completed_tasks["clear_land"]
        rewards = task.claim_rewards(self.current_skills)
        resource_rewards, skill_rewards, reputation, village_exp = rewards
        
        # Should get wood and stone
        wood_reward = next(
            (r for r in resource_rewards if r[0] == ResourceType.WOOD),
            None
        )
        stone_reward = next(
            (r for r in resource_rewards if r[0] == ResourceType.STONE),
            None
        )
        self.assertIsNotNone(wood_reward)
        self.assertIsNotNone(stone_reward)
        self.assertGreater(wood_reward[1], 0)  # quantity
        self.assertGreater(stone_reward[1], 0)  # quantity
        
        # Should get skill rewards
        self.assertIn("gathering", skill_rewards)
        self.assertIn("strength", skill_rewards)
        self.assertGreater(skill_rewards["gathering"], 0)
        self.assertGreater(skill_rewards["strength"], 0)
        
        # Should get reputation and village exp
        self.assertGreater(reputation, 0)
        self.assertGreater(village_exp, 0)

if __name__ == '__main__':
    unittest.main() 