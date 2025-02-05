import unittest
from datetime import timedelta
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

class TestTaskTemplate(unittest.TestCase):
    """Test the TaskTemplate class."""
    def setUp(self):
        self.template = TaskTemplate(
            id="test_template",
            name="Test Task",
            description="A test task template",
            type=TaskType.GATHERING,
            base_duration=timedelta(hours=1),
            chain_id="test_chain",
            prerequisites=[
                TaskPrerequisite(task_id="previous_task")
            ],
            required_resources=[
                ResourceRequirement(ResourceType.WOOD, 5.0)
            ],
            required_tools=[
                ResourceRequirement(ResourceType.AXE, 1.0, consumed=False)
            ],
            resource_rewards=[
                ResourceReward(ResourceType.WOOD, 10.0)
            ],
            skill_requirements={"gathering": 1.0},
            skill_rewards={"gathering": 0.1},
            reputation_reward=5.0,
            village_exp_reward=10.0,
            valid_time_ranges=[(8, 16)],
            season_multipliers={"spring": 1.2},
            weather_requirements=["clear"]
        )
    
    def test_template_creation(self):
        """Test creating a task template."""
        self.assertEqual(self.template.id, "test_template")
        self.assertEqual(self.template.name, "Test Task")
        self.assertEqual(self.template.description, "A test task template")
        self.assertEqual(self.template.type, TaskType.GATHERING)
        self.assertEqual(self.template.base_duration, timedelta(hours=1))
        self.assertEqual(self.template.chain_id, "test_chain")
        self.assertEqual(len(self.template.prerequisites), 1)
        self.assertEqual(len(self.template.required_resources), 1)
        self.assertEqual(len(self.template.required_tools), 1)
        self.assertEqual(len(self.template.resource_rewards), 1)
        self.assertEqual(self.template.skill_requirements["gathering"], 1.0)
        self.assertEqual(self.template.skill_rewards["gathering"], 0.1)
        self.assertEqual(self.template.reputation_reward, 5.0)
        self.assertEqual(self.template.village_exp_reward, 10.0)
        self.assertEqual(self.template.valid_time_ranges, [(8, 16)])
        self.assertEqual(self.template.season_multipliers["spring"], 1.2)
        self.assertEqual(self.template.weather_requirements, ["clear"])
    
    def test_template_serialization(self):
        """Test task template serialization."""
        # Convert to dict
        data = self.template.to_dict()
        
        # Create new template from dict
        new_template = TaskTemplate.from_dict(data)
        
        # Compare properties
        self.assertEqual(new_template.id, self.template.id)
        self.assertEqual(new_template.name, self.template.name)
        self.assertEqual(new_template.type, self.template.type)
        self.assertEqual(new_template.base_duration, self.template.base_duration)
        self.assertEqual(len(new_template.prerequisites), len(self.template.prerequisites))
        self.assertEqual(len(new_template.required_resources), len(self.template.required_resources))
        self.assertEqual(len(new_template.resource_rewards), len(self.template.resource_rewards))
        self.assertEqual(new_template.skill_requirements, self.template.skill_requirements)
        self.assertEqual(new_template.skill_rewards, self.template.skill_rewards)

class TestTaskChain(unittest.TestCase):
    """Test the TaskChain class."""
    def setUp(self):
        self.chain = TaskChain(
            id="test_chain",
            name="Test Chain",
            description="A test task chain",
            tasks=["task1", "task2", "task3"],
            prerequisites=[
                TaskPrerequisite(task_id="previous_chain")
            ],
            village_level_required=1,
            is_repeatable=True,
            season_availability=["spring", "summer"],
            weather_availability=["clear", "cloudy"],
            time_ranges=[(6, 18)],
            reputation_requirement=10.0
        )
    
    def test_chain_creation(self):
        """Test creating a task chain."""
        self.assertEqual(self.chain.id, "test_chain")
        self.assertEqual(self.chain.name, "Test Chain")
        self.assertEqual(self.chain.description, "A test task chain")
        self.assertEqual(len(self.chain.tasks), 3)
        self.assertEqual(len(self.chain.prerequisites), 1)
        self.assertEqual(self.chain.village_level_required, 1)
        self.assertTrue(self.chain.is_repeatable)
        self.assertEqual(self.chain.season_availability, ["spring", "summer"])
        self.assertEqual(self.chain.weather_availability, ["clear", "cloudy"])
        self.assertEqual(self.chain.time_ranges, [(6, 18)])
        self.assertEqual(self.chain.reputation_requirement, 10.0)
    
    def test_chain_serialization(self):
        """Test task chain serialization."""
        # Convert to dict
        data = self.chain.to_dict()
        
        # Create new chain from dict
        new_chain = TaskChain.from_dict(data)
        
        # Compare properties
        self.assertEqual(new_chain.id, self.chain.id)
        self.assertEqual(new_chain.name, self.chain.name)
        self.assertEqual(new_chain.description, self.chain.description)
        self.assertEqual(new_chain.tasks, self.chain.tasks)
        self.assertEqual(len(new_chain.prerequisites), len(self.chain.prerequisites))
        self.assertEqual(new_chain.village_level_required, self.chain.village_level_required)
        self.assertEqual(new_chain.is_repeatable, self.chain.is_repeatable)
        self.assertEqual(new_chain.season_availability, self.chain.season_availability)
        self.assertEqual(new_chain.weather_availability, self.chain.weather_availability)
        self.assertEqual(new_chain.time_ranges, self.chain.time_ranges)
        self.assertEqual(new_chain.reputation_requirement, self.chain.reputation_requirement)

if __name__ == '__main__':
    unittest.main() 