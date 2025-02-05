import unittest
from datetime import timedelta
import json
from pathlib import Path
from typing import Dict, List, Tuple

from src.village_life.core.task import (
    TaskType,
    TaskStatus,
    ResourceRequirement,
    ResourceReward,
    TaskPrerequisite
)
from src.village_life.core.resource_types import ResourceType
from src.village_life.core.task_template import TaskTemplate, TaskChain
from src.village_life.core.task_template_manager import TaskTemplateManager

class TestTaskTemplateManager(unittest.TestCase):
    """Test the TaskTemplateManager class."""
    def setUp(self):
        # Create test data directory
        self.test_data_dir = Path("test_data")
        self.test_data_dir.mkdir(exist_ok=True)
        
        # Create test templates
        self.templates = {
            "scout_location": TaskTemplate(
                id="scout_location",
                name="Scout for Village Location",
                description="Find a suitable location for the village",
                type=TaskType.PLANNING,
                base_duration=timedelta(hours=1),
                chain_id="village_establishment_1",
                prerequisites=[],
                required_resources=[],
                required_tools=[],
                resource_rewards=[],
                skill_requirements={"planning": 1.0},
                skill_rewards={"planning": 0.1, "survival": 0.1},
                reputation_reward=5.0,
                village_exp_reward=10.0,
                valid_time_ranges=[(6, 18)],
                season_multipliers={"spring": 1.2},
                weather_requirements=["clear", "cloudy"]
            ),
            "clear_land": TaskTemplate(
                id="clear_land",
                name="Clear Land for Village",
                description="Clear trees and rocks from the chosen location",
                type=TaskType.GATHERING,
                base_duration=timedelta(hours=2),
                chain_id="village_establishment_1",
                prerequisites=[
                    TaskPrerequisite(task_id="scout_location")
                ],
                required_resources=[],
                required_tools=[
                    ResourceRequirement(ResourceType.AXE, 1.0, consumed=False)
                ],
                resource_rewards=[
                    ResourceReward(ResourceType.WOOD, 20.0),
                    ResourceReward(ResourceType.STONE, 10.0)
                ],
                skill_requirements={"gathering": 1.0},
                skill_rewards={"gathering": 0.2, "strength": 0.1},
                reputation_reward=10.0,
                village_exp_reward=20.0,
                valid_time_ranges=[(6, 18)],
                season_multipliers={"spring": 1.1},
                weather_requirements=["clear"]
            )
        }
        
        # Create test chains
        self.chains = {
            "village_establishment_1": TaskChain(
                id="village_establishment_1",
                name="Village Establishment: First Steps",
                description="Initial tasks to establish the village",
                tasks=["scout_location", "clear_land"],
                prerequisites=[],
                village_level_required=0,
                is_repeatable=False,
                season_availability=["spring", "summer"],
                weather_availability=["clear", "cloudy"],
                time_ranges=[(6, 18)],
                reputation_requirement=0.0
            )
        }
        
        # Write test data to files
        with open(self.test_data_dir / "task_templates.json", "w") as f:
            json.dump({
                id: template.to_dict()
                for id, template in self.templates.items()
            }, f, indent=2)
        
        with open(self.test_data_dir / "task_chains.json", "w") as f:
            json.dump({
                id: chain.to_dict()
                for id, chain in self.chains.items()
            }, f, indent=2)
        
        # Create task template manager
        self.manager = TaskTemplateManager(self.test_data_dir)
    
    def tearDown(self):
        # Clean up test data directory
        for file in self.test_data_dir.glob("*"):
            file.unlink()
        self.test_data_dir.rmdir()
    
    def test_load_templates(self):
        """Test loading task templates and chains."""
        # Check if templates are loaded
        self.assertEqual(len(self.manager.task_templates), len(self.templates))
        self.assertEqual(len(self.manager.task_chains), len(self.chains))
        
        # Check specific template
        scout_template = self.manager.task_templates["scout_location"]
        self.assertEqual(scout_template.name, "Scout for Village Location")
        self.assertEqual(scout_template.type, TaskType.PLANNING)
        self.assertEqual(scout_template.base_duration, timedelta(hours=1))
        
        # Check specific chain
        village_chain = self.manager.task_chains["village_establishment_1"]
        self.assertEqual(village_chain.name, "Village Establishment: First Steps")
        self.assertEqual(len(village_chain.tasks), 2)
        self.assertFalse(village_chain.is_repeatable)
    
    def test_get_available_tasks(self):
        """Test getting available tasks."""
        # Initial state - only scout_location should be available
        available_tasks = self.manager.get_available_tasks(
            completed_tasks=[],
            village_level=0,
            reputation=0.0,
            season="spring",
            weather="clear",
            time_of_day=12
        )
        
        self.assertEqual(len(available_tasks), 1)
        self.assertEqual(available_tasks[0].id, "scout_location")
        
        # After completing scout_location, clear_land should be available
        available_tasks = self.manager.get_available_tasks(
            completed_tasks=["scout_location"],
            village_level=0,
            reputation=0.0,
            season="spring",
            weather="clear",
            time_of_day=12
        )
        
        self.assertEqual(len(available_tasks), 1)
        self.assertEqual(available_tasks[0].id, "clear_land")
    
    def test_get_task_chain(self):
        """Test getting task chain by task ID."""
        # Get chain for scout_location
        chain = self.manager.get_task_chain("scout_location")
        self.assertIsNotNone(chain)
        self.assertEqual(chain.id, "village_establishment_1")
        
        # Get chain for clear_land
        chain = self.manager.get_task_chain("clear_land")
        self.assertIsNotNone(chain)
        self.assertEqual(chain.id, "village_establishment_1")
        
        # Get chain for non-existent task
        chain = self.manager.get_task_chain("non_existent")
        self.assertIsNone(chain)
    
    def test_get_next_tasks(self):
        """Test getting next tasks in chain."""
        # Get next tasks after scout_location
        next_tasks = self.manager.get_next_tasks("scout_location")
        self.assertEqual(len(next_tasks), 1)
        self.assertEqual(next_tasks[0].id, "clear_land")
        
        # Get next tasks after clear_land (end of chain)
        next_tasks = self.manager.get_next_tasks("clear_land")
        self.assertEqual(len(next_tasks), 0)
        
        # Get next tasks for non-existent task
        next_tasks = self.manager.get_next_tasks("non_existent")
        self.assertEqual(len(next_tasks), 0)

if __name__ == '__main__':
    unittest.main() 