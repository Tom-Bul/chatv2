"""
Tests for the resource management system.
"""

import unittest
from datetime import datetime, timedelta
from typing import Dict, Tuple
from unittest.mock import Mock, patch

from src.core.resource_manager import (
    ResourceType, ResourceCategory, ResourceProperties,
    Resource, ResourceManager
)
from src.core.modifiers import create_modifier

class TestResourceProperties(unittest.TestCase):
    """Test the ResourceProperties class."""
    def setUp(self):
        self.properties = ResourceProperties(
            name="Test Resource",
            category=ResourceCategory.BASIC,
            base_value=10.0,
            decay_rate=0.1,
            quality_impact=0.5,
            stackable=True,
            max_stack=100,
            weight=1.0
        )
    
    def test_properties_creation(self):
        """Test creating resource properties."""
        self.assertEqual(self.properties.name, "Test Resource")
        self.assertEqual(self.properties.category, ResourceCategory.BASIC)
        self.assertEqual(self.properties.base_value, 10.0)
        self.assertEqual(self.properties.decay_rate, 0.1)
        self.assertEqual(self.properties.quality_impact, 0.5)
        self.assertTrue(self.properties.stackable)
        self.assertEqual(self.properties.max_stack, 100)
        self.assertEqual(self.properties.weight, 1.0)
    
    def test_value_calculation(self):
        """Test calculating resource value."""
        # Test base value
        value = self.properties.calculate_value(1.0, 0.5)
        self.assertEqual(value, 10.0)
        
        # Test quality impact
        value = self.properties.calculate_value(1.0, 1.0)
        self.assertEqual(value, 12.5)  # 10 + (10 * 0.5 * 0.5)
        
        # Test quantity scaling
        value = self.properties.calculate_value(2.0, 0.5)
        self.assertEqual(value, 20.0)

class TestResource(unittest.TestCase):
    """Test the Resource class."""
    def setUp(self):
        self.properties = ResourceProperties(
            name="Test Resource",
            category=ResourceCategory.BASIC,
            base_value=10.0,
            decay_rate=0.1,
            quality_impact=0.5,
            stackable=True,
            max_stack=100,
            weight=1.0
        )
        self.resource = Resource(
            resource_type=ResourceType.WOOD,
            properties=self.properties,
            quantity=10.0,
            quality=0.8
        )
    
    def test_resource_creation(self):
        """Test creating a resource."""
        self.assertEqual(self.resource.type, "WOOD")
        self.assertEqual(self.resource.quantity, 10.0)
        self.assertEqual(self.resource.quality, 0.8)
    
    def test_resource_modification(self):
        """Test modifying a resource."""
        modifier = create_modifier("multiply", strength=2.0)
        modified = self.resource.transform(modifier)
        
        self.assertEqual(modified.quantity, 10.0)  # Original resource unchanged
        self.assertEqual(self.resource.quantity, 10.0)
    
    def test_resource_combination(self):
        """Test combining resources."""
        other = Resource(
            resource_type=ResourceType.WOOD,
            properties=self.properties,
            quantity=5.0,
            quality=0.6
        )
        
        combined = self.resource.combine(other)
        
        # Test quantities
        self.assertEqual(combined.quantity, 15.0)
        
        # Test weighted average quality
        expected_quality = (10.0 * 0.8 + 5.0 * 0.6) / 15.0
        self.assertEqual(combined.quality, expected_quality)
        
        # Test combining different types
        other_type = Resource(
            resource_type=ResourceType.STONE,
            properties=self.properties,
            quantity=5.0,
            quality=0.6
        )
        with self.assertRaises(ValueError):
            self.resource.combine(other_type)
    
    def test_resource_splitting(self):
        """Test splitting resources."""
        split, remaining = self.resource.split(4.0)
        
        # Test quantities
        self.assertEqual(split.quantity, 4.0)
        self.assertEqual(remaining.quantity, 6.0)
        
        # Test qualities
        self.assertEqual(split.quality, 0.8)
        self.assertEqual(remaining.quality, 0.8)
        
        # Test invalid split
        with self.assertRaises(ValueError):
            self.resource.split(20.0)

class TestResourceManager(unittest.TestCase):
    """Test the ResourceManager class."""
    def setUp(self):
        self.manager = ResourceManager()
    
    def test_add_resource(self):
        """Test adding resources."""
        # Test basic addition
        success = self.manager.add_resource(ResourceType.WOOD, 10.0, 0.8)
        self.assertTrue(success)
        
        info = self.manager.get_resource_info(ResourceType.WOOD)
        self.assertEqual(info["quantity"], 10.0)
        self.assertEqual(info["quality"], 0.8)
        
        # Test adding to existing stack
        success = self.manager.add_resource(ResourceType.WOOD, 5.0, 0.6)
        self.assertTrue(success)
        
        info = self.manager.get_resource_info(ResourceType.WOOD)
        self.assertEqual(info["quantity"], 15.0)
        expected_quality = (10.0 * 0.8 + 5.0 * 0.6) / 15.0
        self.assertEqual(info["quality"], expected_quality)
        
        # Test invalid addition
        success = self.manager.add_resource(ResourceType.WOOD, -1.0)
        self.assertFalse(success)
    
    def test_remove_resource(self):
        """Test removing resources."""
        # Add initial resources
        self.manager.add_resource(ResourceType.WOOD, 10.0, 0.8)
        
        # Test valid removal
        success, quantity, quality = self.manager.remove_resource(ResourceType.WOOD, 4.0)
        self.assertTrue(success)
        self.assertEqual(quantity, 4.0)
        self.assertEqual(quality, 0.8)
        
        info = self.manager.get_resource_info(ResourceType.WOOD)
        self.assertEqual(info["quantity"], 6.0)
        
        # Test removing too much
        success, quantity, quality = self.manager.remove_resource(ResourceType.WOOD, 10.0)
        self.assertFalse(success)
        
        # Test removing from non-existent resource
        success, quantity, quality = self.manager.remove_resource(ResourceType.STONE, 1.0)
        self.assertFalse(success)
    
    def test_update(self):
        """Test resource update logic."""
        # Add some resources
        self.manager.add_resource(ResourceType.HERBS, 10.0, 1.0)  # Has decay
        self.manager.add_resource(ResourceType.STONE, 10.0, 1.0)  # No decay
        
        # Update with time passed
        time_passed = timedelta(days=1)
        season_effects = {"HERBS": 1.2}  # Increased decay for herbs
        
        self.manager.update(time_passed, season_effects)
        
        # Check decay
        herbs_info = self.manager.get_resource_info(ResourceType.HERBS)
        self.assertLess(herbs_info["quantity"], 10.0)
        
        stone_info = self.manager.get_resource_info(ResourceType.STONE)
        self.assertEqual(stone_info["quantity"], 10.0)
    
    def test_storage_info(self):
        """Test getting storage information."""
        # Add some resources
        self.manager.add_resource(ResourceType.WOOD, 10.0, 0.8)
        self.manager.add_resource(ResourceType.STONE, 5.0, 0.9)
        
        info = self.manager.get_storage_info()
        
        self.assertIn("capacity", info)
        self.assertIn("total_weight", info)
        self.assertIn("resources", info)
        
        # Check total weight calculation
        wood_weight = 10.0 * self.manager._properties[ResourceType.WOOD].weight
        stone_weight = 5.0 * self.manager._properties[ResourceType.STONE].weight
        self.assertEqual(info["total_weight"], wood_weight + stone_weight)
    
    def test_save_load_state(self):
        """Test saving and loading state."""
        # Set up initial state
        self.manager.add_resource(ResourceType.WOOD, 10.0, 0.8)
        self.manager.add_resource(ResourceType.STONE, 5.0, 0.9)
        
        # Save state
        state = self.manager.save_state()
        
        # Create new manager and load state
        new_manager = ResourceManager()
        new_manager.load_state(state)
        
        # Compare states
        original_info = self.manager.get_storage_info()
        loaded_info = new_manager.get_storage_info()
        
        self.assertEqual(original_info["capacity"], loaded_info["capacity"])
        self.assertEqual(original_info["total_weight"], loaded_info["total_weight"])
        self.assertEqual(len(original_info["resources"]), len(loaded_info["resources"]))

if __name__ == '__main__':
    unittest.main() 