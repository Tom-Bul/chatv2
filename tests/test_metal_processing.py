import unittest
from datetime import datetime, timedelta
import os
import shutil
import json

from src.core.task_template import TaskTemplate, TaskChain
from src.core.task_template_manager import TaskTemplateManager
from src.core.task import TaskType, TaskStatus, ResourceRequirement, ResourceReward
from src.core.resource_manager import ResourceType, ResourceManager

class TestMetalProcessing(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.test_dir = "test_templates"
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Copy task templates and chains
        with open("data/templates/task_chains.json", "r") as f:
            self.chains_data = json.load(f)
        with open("data/templates/task_templates.json", "r") as f:
            self.templates_data = json.load(f)
        
        # Save test data
        with open(os.path.join(self.test_dir, "task_chains.json"), "w") as f:
            json.dump(self.chains_data, f)
        with open(os.path.join(self.test_dir, "task_templates.json"), "w") as f:
            json.dump(self.templates_data, f)
        
        self.template_manager = TaskTemplateManager(self.test_dir)
        self.resource_manager = ResourceManager()
        
        # Add required resources and tools
        self.resource_manager.add_resource(ResourceType.METAL, 100.0, 0.5)
        self.resource_manager.add_resource(ResourceType.REFINED_METAL, 50.0, 0.5)
        self.resource_manager.add_resource(ResourceType.WOOD, 100.0, 0.5)
        self.resource_manager.add_resource(ResourceType.REFINED_WOOD, 50.0, 0.5)
        self.resource_manager.add_resource(ResourceType.CUT_STONE, 50.0, 0.5)
        self.resource_manager.add_resource(ResourceType.PICKAXE, 2.0, 0.5)
        self.resource_manager.add_resource(ResourceType.HAMMER, 2.0, 0.5)
        self.resource_manager.add_resource(ResourceType.SAW, 2.0, 0.5)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)
    
    def test_chain_prerequisites(self):
        """Test metal processing chain prerequisites."""
        chain = next(
            chain for chain in self.chains_data
            if chain["id"] == "metal_processing_1"
        )
        
        self.assertEqual(len(chain["prerequisites"]), 3)
        self.assertIn("resource_production_1", chain["prerequisites"])
        self.assertIn("tool_crafting_1", chain["prerequisites"])
        self.assertIn("stone_processing_1", chain["prerequisites"])
        self.assertEqual(chain["village_level_required"], 2)
        self.assertEqual(chain["reputation_required"], 30.0)
    
    def test_task_progression(self):
        """Test metal processing task progression."""
        # Get chain tasks
        chain_tasks = self.template_manager.get_chain_tasks(
            chain_id="metal_processing_1",
            village_level=2,
            completed_tasks=set()
        )
        
        self.assertEqual(len(chain_tasks), 4)
        task_ids = [task.id for task in chain_tasks]
        self.assertEqual(task_ids, [
            "ore_mining",
            "ore_sorting",
            "ore_smelting",
            "build_forge"
        ])
        
        # Check task prerequisites
        ore_mining = next(t for t in chain_tasks if t.id == "ore_mining")
        self.assertEqual(len(ore_mining.prerequisites), 0)
        
        ore_sorting = next(t for t in chain_tasks if t.id == "ore_sorting")
        self.assertEqual(len(ore_sorting.prerequisites), 1)
        self.assertEqual(ore_sorting.prerequisites[0].task_id, "ore_mining")
        
        ore_smelting = next(t for t in chain_tasks if t.id == "ore_smelting")
        self.assertEqual(len(ore_smelting.prerequisites), 1)
        self.assertEqual(ore_smelting.prerequisites[0].task_id, "ore_sorting")
        
        build_forge = next(t for t in chain_tasks if t.id == "build_forge")
        self.assertEqual(len(build_forge.prerequisites), 1)
        self.assertEqual(build_forge.prerequisites[0].task_id, "ore_smelting")
        self.assertEqual(build_forge.prerequisites[0].completions_required, 2)
    
    def test_resource_requirements(self):
        """Test metal processing resource requirements."""
        chain_tasks = self.template_manager.get_chain_tasks(
            chain_id="metal_processing_1",
            village_level=2,
            completed_tasks=set()
        )
        
        # Ore mining requirements (no resources required)
        ore_mining = next(t for t in chain_tasks if t.id == "ore_mining")
        self.assertEqual(len(ore_mining.required_resources), 0)
        
        # Ore sorting requirements
        ore_sorting = next(t for t in chain_tasks if t.id == "ore_sorting")
        self.assertEqual(len(ore_sorting.required_resources), 1)
        self.assertEqual(ore_sorting.required_resources[0].type, ResourceType.METAL)
        self.assertEqual(ore_sorting.required_resources[0].quantity, 25.0)
        self.assertEqual(ore_sorting.required_resources[0].min_quality, 0.4)
        
        # Ore smelting requirements
        ore_smelting = next(t for t in chain_tasks if t.id == "ore_smelting")
        self.assertEqual(len(ore_smelting.required_resources), 2)
        metal_req = next(r for r in ore_smelting.required_resources if r.type == ResourceType.REFINED_METAL)
        wood_req = next(r for r in ore_smelting.required_resources if r.type == ResourceType.WOOD)
        self.assertEqual(metal_req.quantity, 20.0)
        self.assertEqual(metal_req.min_quality, 0.5)
        self.assertEqual(wood_req.quantity, 30.0)
        self.assertEqual(wood_req.min_quality, 0.3)
        
        # Build forge requirements
        build_forge = next(t for t in chain_tasks if t.id == "build_forge")
        self.assertEqual(len(build_forge.required_resources), 3)
        metal_req = next(r for r in build_forge.required_resources if r.type == ResourceType.REFINED_METAL)
        stone_req = next(r for r in build_forge.required_resources if r.type == ResourceType.CUT_STONE)
        wood_req = next(r for r in build_forge.required_resources if r.type == ResourceType.REFINED_WOOD)
        self.assertEqual(metal_req.quantity, 30.0)
        self.assertEqual(metal_req.min_quality, 0.5)
        self.assertEqual(stone_req.quantity, 40.0)
        self.assertEqual(stone_req.min_quality, 0.4)
        self.assertEqual(wood_req.quantity, 25.0)
        self.assertEqual(wood_req.min_quality, 0.4)
    
    def test_tool_requirements(self):
        """Test metal processing tool requirements."""
        chain_tasks = self.template_manager.get_chain_tasks(
            chain_id="metal_processing_1",
            village_level=2,
            completed_tasks=set()
        )
        
        # Ore mining tools
        ore_mining = next(t for t in chain_tasks if t.id == "ore_mining")
        self.assertEqual(len(ore_mining.required_tools), 1)
        self.assertEqual(ore_mining.required_tools[0].type, ResourceType.PICKAXE)
        self.assertEqual(ore_mining.required_tools[0].min_quality, 0.4)
        
        # Ore sorting tools (none required)
        ore_sorting = next(t for t in chain_tasks if t.id == "ore_sorting")
        self.assertEqual(len(ore_sorting.required_tools), 0)
        
        # Ore smelting tools
        ore_smelting = next(t for t in chain_tasks if t.id == "ore_smelting")
        self.assertEqual(len(ore_smelting.required_tools), 1)
        self.assertEqual(ore_smelting.required_tools[0].type, ResourceType.HAMMER)
        self.assertEqual(ore_smelting.required_tools[0].min_quality, 0.4)
        
        # Build forge tools
        build_forge = next(t for t in chain_tasks if t.id == "build_forge")
        self.assertEqual(len(build_forge.required_tools), 2)
        hammer = next(t for t in build_forge.required_tools if t.type == ResourceType.HAMMER)
        saw = next(t for t in build_forge.required_tools if t.type == ResourceType.SAW)
        self.assertEqual(hammer.min_quality, 0.5)
        self.assertEqual(saw.min_quality, 0.4)
    
    def test_skill_requirements(self):
        """Test metal processing skill requirements."""
        chain_tasks = self.template_manager.get_chain_tasks(
            chain_id="metal_processing_1",
            village_level=2,
            completed_tasks=set()
        )
        
        # Ore mining skills
        ore_mining = next(t for t in chain_tasks if t.id == "ore_mining")
        self.assertEqual(ore_mining.skill_requirements["mining"], 10.0)
        self.assertEqual(ore_mining.skill_requirements["strength"], 15.0)
        
        # Ore sorting skills
        ore_sorting = next(t for t in chain_tasks if t.id == "ore_sorting")
        self.assertEqual(ore_sorting.skill_requirements["crafting"], 12.0)
        self.assertEqual(ore_sorting.skill_requirements["mining"], 8.0)
        
        # Ore smelting skills
        ore_smelting = next(t for t in chain_tasks if t.id == "ore_smelting")
        self.assertEqual(ore_smelting.skill_requirements["crafting"], 15.0)
        self.assertEqual(ore_smelting.skill_requirements["smithing"], 10.0)
        
        # Build forge skills
        build_forge = next(t for t in chain_tasks if t.id == "build_forge")
        self.assertEqual(build_forge.skill_requirements["construction"], 20.0)
        self.assertEqual(build_forge.skill_requirements["smithing"], 15.0)
    
    def test_task_rewards(self):
        """Test metal processing task rewards."""
        chain_tasks = self.template_manager.get_chain_tasks(
            chain_id="metal_processing_1",
            village_level=2,
            completed_tasks=set()
        )
        
        # Ore mining rewards
        ore_mining = next(t for t in chain_tasks if t.id == "ore_mining")
        self.assertEqual(len(ore_mining.resource_rewards), 1)
        self.assertEqual(ore_mining.resource_rewards[0].type, ResourceType.METAL)
        self.assertEqual(ore_mining.resource_rewards[0].base_quantity, 30.0)
        self.assertEqual(ore_mining.skill_rewards["mining"], 25.0)
        self.assertEqual(ore_mining.skill_rewards["strength"], 20.0)
        
        # Ore sorting rewards
        ore_sorting = next(t for t in chain_tasks if t.id == "ore_sorting")
        self.assertEqual(len(ore_sorting.resource_rewards), 1)
        self.assertEqual(ore_sorting.resource_rewards[0].type, ResourceType.REFINED_METAL)
        self.assertEqual(ore_sorting.resource_rewards[0].base_quantity, 20.0)
        self.assertEqual(ore_sorting.skill_rewards["crafting"], 20.0)
        self.assertEqual(ore_sorting.skill_rewards["mining"], 10.0)
        
        # Ore smelting rewards
        ore_smelting = next(t for t in chain_tasks if t.id == "ore_smelting")
        self.assertEqual(len(ore_smelting.resource_rewards), 1)
        self.assertEqual(ore_smelting.resource_rewards[0].type, ResourceType.REFINED_METAL)
        self.assertEqual(ore_smelting.resource_rewards[0].base_quantity, 15.0)
        self.assertEqual(ore_smelting.skill_rewards["crafting"], 30.0)
        self.assertEqual(ore_smelting.skill_rewards["smithing"], 25.0)
        
        # Build forge rewards
        build_forge = next(t for t in chain_tasks if t.id == "build_forge")
        self.assertEqual(len(build_forge.resource_rewards), 0)
        self.assertEqual(build_forge.skill_rewards["construction"], 40.0)
        self.assertEqual(build_forge.skill_rewards["smithing"], 30.0)
        self.assertEqual(build_forge.skill_rewards["crafting"], 20.0)
    
    def test_seasonal_effects(self):
        """Test metal processing seasonal effects."""
        chain_tasks = self.template_manager.get_chain_tasks(
            chain_id="metal_processing_1",
            village_level=2,
            completed_tasks=set()
        )
        
        # Ore mining seasons
        ore_mining = next(t for t in chain_tasks if t.id == "ore_mining")
        self.assertEqual(ore_mining.season_multipliers["spring"], 1.0)
        self.assertEqual(ore_mining.season_multipliers["summer"], 1.0)
        self.assertEqual(ore_mining.season_multipliers["autumn"], 1.0)
        self.assertEqual(ore_mining.season_multipliers["winter"], 0.8)
        
        # Ore sorting seasons
        ore_sorting = next(t for t in chain_tasks if t.id == "ore_sorting")
        self.assertEqual(ore_sorting.season_multipliers["spring"], 1.0)
        self.assertEqual(ore_sorting.season_multipliers["summer"], 1.0)
        self.assertEqual(ore_sorting.season_multipliers["autumn"], 1.0)
        self.assertEqual(ore_sorting.season_multipliers["winter"], 0.9)
        
        # Ore smelting seasons
        ore_smelting = next(t for t in chain_tasks if t.id == "ore_smelting")
        self.assertEqual(ore_smelting.season_multipliers["spring"], 1.0)
        self.assertEqual(ore_smelting.season_multipliers["summer"], 1.2)
        self.assertEqual(ore_smelting.season_multipliers["autumn"], 1.0)
        self.assertEqual(ore_smelting.season_multipliers["winter"], 0.7)
        
        # Build forge seasons
        build_forge = next(t for t in chain_tasks if t.id == "build_forge")
        self.assertEqual(build_forge.season_multipliers["spring"], 1.2)
        self.assertEqual(build_forge.season_multipliers["summer"], 1.0)
        self.assertEqual(build_forge.season_multipliers["autumn"], 1.0)
        self.assertEqual(build_forge.season_multipliers["winter"], 0.6)
    
    def test_weather_requirements(self):
        """Test metal processing weather requirements."""
        chain_tasks = self.template_manager.get_chain_tasks(
            chain_id="metal_processing_1",
            village_level=2,
            completed_tasks=set()
        )
        
        # Ore mining weather
        ore_mining = next(t for t in chain_tasks if t.id == "ore_mining")
        self.assertIn("clear", ore_mining.weather_requirements)
        self.assertIn("cloudy", ore_mining.weather_requirements)
        self.assertIn("partly_cloudy", ore_mining.weather_requirements)
        
        # Ore sorting weather
        ore_sorting = next(t for t in chain_tasks if t.id == "ore_sorting")
        self.assertIn("clear", ore_sorting.weather_requirements)
        self.assertIn("partly_cloudy", ore_sorting.weather_requirements)
        self.assertIn("cloudy", ore_sorting.weather_requirements)
        
        # Ore smelting weather
        ore_smelting = next(t for t in chain_tasks if t.id == "ore_smelting")
        self.assertIn("clear", ore_smelting.weather_requirements)
        self.assertIn("partly_cloudy", ore_smelting.weather_requirements)
        self.assertNotIn("cloudy", ore_smelting.weather_requirements)
        
        # Build forge weather
        build_forge = next(t for t in chain_tasks if t.id == "build_forge")
        self.assertIn("clear", build_forge.weather_requirements)
        self.assertIn("partly_cloudy", build_forge.weather_requirements)
        self.assertNotIn("cloudy", build_forge.weather_requirements)

    def test_alternative_resources(self):
        """Test that alternative resources can be used in metal processing."""
        chain_tasks = self.template_manager.get_chain_tasks(
            chain_id="metal_processing_1",
            village_level=2,
            completed_tasks=set()
        )
        
        # Test ore smelting alternatives
        ore_smelting = next(t for t in chain_tasks if t.id == "ore_smelting")
        fuel_req = next(r for r in ore_smelting.required_resources if r.type == ResourceType.WOOD)
        self.assertTrue(hasattr(fuel_req, 'alternative_types'))
        self.assertIn('COAL', fuel_req.alternative_types)
        self.assertIn('CHARCOAL', fuel_req.alternative_types)
        
        # Test tool alternatives
        hammer_req = next(t for t in ore_smelting.required_tools if t.type == ResourceType.HAMMER)
        self.assertTrue(hasattr(hammer_req, 'alternative_types'))
        self.assertIn('MALLET', hammer_req.alternative_types)
        self.assertIn('SMITHING_HAMMER', hammer_req.alternative_types)
    
    def test_quality_contributions(self):
        """Test that quality is properly calculated from multiple sources."""
        chain_tasks = self.template_manager.get_chain_tasks(
            chain_id="metal_processing_1",
            village_level=2,
            completed_tasks=set()
        )
        
        ore_smelting = next(t for t in chain_tasks if t.id == "ore_smelting")
        
        # Test resource quality contributions
        metal_req = next(r for r in ore_smelting.required_resources if r.type == ResourceType.REFINED_METAL)
        self.assertTrue(metal_req.affects_output_quality)
        self.assertEqual(metal_req.quality_contribution, 0.6)
        
        # Test tool quality contributions
        hammer_req = next(t for t in ore_smelting.required_tools if t.type == ResourceType.HAMMER)
        self.assertTrue(hammer_req.affects_output_quality)
        self.assertEqual(hammer_req.quality_contribution, 0.3)
        
        # Test quality factors
        self.assertEqual(ore_smelting.quality_factors["tool_quality"], 0.3)
        self.assertEqual(ore_smelting.quality_factors["skill_level"], 0.3)
        self.assertEqual(ore_smelting.quality_factors["resource_quality"], 0.3)
        self.assertEqual(ore_smelting.quality_factors["weather_bonus"], 0.1)
    
    def test_byproducts_generation(self):
        """Test that byproducts are properly configured."""
        chain_tasks = self.template_manager.get_chain_tasks(
            chain_id="metal_processing_1",
            village_level=2,
            completed_tasks=set()
        )
        
        ore_smelting = next(t for t in chain_tasks if t.id == "ore_smelting")
        main_reward = ore_smelting.resource_rewards[0]
        
        self.assertTrue(hasattr(main_reward, 'byproducts'))
        self.assertEqual(len(main_reward.byproducts), 2)
        
        slag = next(b for b in main_reward.byproducts if b["type"] == "SLAG")
        self.assertEqual(slag["base_quantity"], 5.0)
        self.assertEqual(slag["chance"], 0.8)
        
        ash = next(b for b in main_reward.byproducts if b["type"] == "ASH")
        self.assertEqual(ash["base_quantity"], 2.0)
        self.assertEqual(ash["chance"], 1.0)
    
    def test_environmental_effects(self):
        """Test environmental effects on task execution."""
        chain_tasks = self.template_manager.get_chain_tasks(
            chain_id="metal_processing_1",
            village_level=2,
            completed_tasks=set()
        )
        
        ore_smelting = next(t for t in chain_tasks if t.id == "ore_smelting")
        
        # Test weather effects
        self.assertEqual(ore_smelting.weather_effects["clear"]["efficiency"], 1.0)
        self.assertEqual(ore_smelting.weather_effects["rain"]["efficiency"], 0.8)
        self.assertEqual(ore_smelting.weather_effects["storm"]["efficiency"], 0.6)
        self.assertTrue(ore_smelting.weather_effects["rain"]["requires_shelter"])
        
        # Test location requirements
        self.assertIn("FORGE", ore_smelting.location_requirements["primary"])
        self.assertIn("SMITHY", ore_smelting.location_requirements["primary"])
        self.assertIn("WORKSHOP", ore_smelting.location_requirements["alternative"])
        self.assertEqual(ore_smelting.location_requirements["efficiency_penalty"], 0.5)
    
    def test_failure_conditions(self):
        """Test task failure conditions."""
        chain_tasks = self.template_manager.get_chain_tasks(
            chain_id="metal_processing_1",
            village_level=2,
            completed_tasks=set()
        )
        
        ore_smelting = next(t for t in chain_tasks if t.id == "ore_smelting")
        
        self.assertEqual(ore_smelting.failure_conditions["max_temperature"], 1200)
        self.assertEqual(ore_smelting.failure_conditions["min_temperature"], 800)
        self.assertTrue(ore_smelting.failure_conditions["required_ventilation"])
        self.assertEqual(ore_smelting.failure_conditions["maximum_moisture"], 0.7)
    
    def test_event_system(self):
        """Test task event triggers."""
        chain_tasks = self.template_manager.get_chain_tasks(
            chain_id="metal_processing_1",
            village_level=2,
            completed_tasks=set()
        )
        
        ore_smelting = next(t for t in chain_tasks if t.id == "ore_smelting")
        
        self.assertIn("FORGE_FIRE_LIT", ore_smelting.event_triggers["on_start"])
        self.assertIn("SMOKE_PRODUCED", ore_smelting.event_triggers["on_start"])
        self.assertIn("METAL_PROCESSED", ore_smelting.event_triggers["on_complete"])
        self.assertIn("SKILL_INCREASED", ore_smelting.event_triggers["on_complete"])
        self.assertIn("RESOURCES_WASTED", ore_smelting.event_triggers["on_failure"])
        self.assertIn("TOOL_DAMAGED", ore_smelting.event_triggers["on_failure"])
    
    def test_skill_system(self):
        """Test enhanced skill system."""
        chain_tasks = self.template_manager.get_chain_tasks(
            chain_id="metal_processing_1",
            village_level=2,
            completed_tasks=set()
        )
        
        ore_smelting = next(t for t in chain_tasks if t.id == "ore_smelting")
        
        # Test crafting skill configuration
        crafting = ore_smelting.skill_requirements["crafting"]
        self.assertEqual(crafting["level"], 15.0)
        self.assertEqual(crafting["contribution"], 0.4)
        self.assertIn("metalworking", crafting["alternative_skills"])
        self.assertIn("blacksmithing", crafting["alternative_skills"])
        
        # Test skill rewards
        crafting_reward = ore_smelting.skill_rewards["crafting"]
        self.assertEqual(crafting_reward["base_exp"], 30.0)
        self.assertTrue(crafting_reward["quality_multiplier"])
        self.assertEqual(crafting_reward["failure_exp"], 5.0)
    
    def test_time_system(self):
        """Test enhanced time system."""
        chain_tasks = self.template_manager.get_chain_tasks(
            chain_id="metal_processing_1",
            village_level=2,
            completed_tasks=set()
        )
        
        ore_smelting = next(t for t in chain_tasks if t.id == "ore_smelting")
        
        # Test day time range
        day_range = ore_smelting.valid_time_ranges[0]
        self.assertEqual(day_range["start_hour"], 6)
        self.assertEqual(day_range["end_hour"], 20)
        self.assertEqual(day_range["efficiency_multiplier"], 1.0)
        
        # Test night time range
        night_range = ore_smelting.valid_time_ranges[1]
        self.assertEqual(night_range["start_hour"], 20)
        self.assertEqual(night_range["end_hour"], 6)
        self.assertEqual(night_range["efficiency_multiplier"], 0.8)
        self.assertTrue(night_range["requires_light_source"])

if __name__ == '__main__':
    unittest.main() 