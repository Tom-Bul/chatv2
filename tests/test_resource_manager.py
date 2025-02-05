import pytest
from datetime import datetime, timedelta
from src.core.resource_manager import (
    ResourceManager,
    ResourceType,
    ResourceCategory,
    ResourceProperties,
    ResourceStack
)

@pytest.fixture
def resource_manager():
    """Create a ResourceManager instance for testing."""
    return ResourceManager()

def test_resource_properties():
    """Test resource property definitions."""
    manager = ResourceManager()
    
    # Check all resource types have properties
    for res_type in ResourceType:
        assert res_type in manager.properties
        props = manager.properties[res_type]
        assert isinstance(props, ResourceProperties)
        assert props.name
        assert isinstance(props.category, ResourceCategory)
        assert props.base_value > 0
        assert 0 <= props.decay_rate <= 1
        assert props.weight > 0

def test_add_resources():
    """Test adding resources to storage."""
    manager = ResourceManager()
    
    # Add basic resources
    assert manager.add_resource(ResourceType.FOOD, 10.0)
    assert manager.add_resource(ResourceType.WATER, 20.0)
    
    # Check storage
    assert ResourceType.FOOD in manager.storage
    assert ResourceType.WATER in manager.storage
    
    # Check quantities
    food_stack = manager.storage[ResourceType.FOOD]
    assert food_stack.quantity == 10.0
    assert food_stack.quality == 1.0
    
    water_stack = manager.storage[ResourceType.WATER]
    assert water_stack.quantity == 20.0
    assert water_stack.quality == 1.0

def test_storage_capacity():
    """Test storage capacity limits."""
    manager = ResourceManager()
    
    # Try to add more than capacity
    huge_amount = manager.storage_capacity / manager.properties[ResourceType.STONE].weight + 1
    assert not manager.add_resource(ResourceType.STONE, huge_amount)
    
    # Add up to capacity
    safe_amount = manager.storage_capacity / manager.properties[ResourceType.STONE].weight - 1
    assert manager.add_resource(ResourceType.STONE, safe_amount)

def test_remove_resources():
    """Test removing resources from storage."""
    manager = ResourceManager()
    
    # Add resources
    manager.add_resource(ResourceType.WOOD, 50.0)
    
    # Remove some
    success, quantity, quality = manager.remove_resource(ResourceType.WOOD, 20.0)
    assert success
    assert quantity == 20.0
    assert quality == 1.0
    
    # Check remaining
    wood_stack = manager.storage[ResourceType.WOOD]
    assert wood_stack.quantity == 30.0
    
    # Try to remove too much
    success, quantity, quality = manager.remove_resource(ResourceType.WOOD, 40.0)
    assert not success
    assert wood_stack.quantity == 30.0

def test_resource_decay():
    """Test resource decay over time."""
    manager = ResourceManager()
    
    # Add perishable resource
    manager.add_resource(ResourceType.FOOD, 100.0)
    
    # Simulate time passing
    one_day = timedelta(days=1)
    decay_rate = manager.properties[ResourceType.FOOD].decay_rate
    expected_loss = decay_rate * 1  # 1 day
    
    manager.update(one_day, {})
    
    # Check decayed amount
    food_stack = manager.storage[ResourceType.FOOD]
    assert food_stack.quantity == pytest.approx(100.0 - expected_loss, rel=1e-5)

def test_resource_quality():
    """Test resource quality calculations."""
    manager = ResourceManager()
    
    # Add resources with different qualities
    manager.add_resource(ResourceType.METAL, 10.0, quality=1.0)
    manager.add_resource(ResourceType.METAL, 10.0, quality=0.5)
    
    # Check average quality
    metal_stack = manager.storage[ResourceType.METAL]
    assert metal_stack.quantity == 20.0
    assert metal_stack.quality == 0.75  # (10*1.0 + 10*0.5) / 20

def test_resource_info():
    """Test resource information retrieval."""
    manager = ResourceManager()
    
    # Add resource
    manager.add_resource(ResourceType.CLOTH, 15.0, quality=0.8)
    
    # Get info
    info = manager.get_resource_info(ResourceType.CLOTH)
    assert info
    assert info["name"] == "Cloth"
    assert info["quantity"] == 15.0
    assert info["quality"] == 0.8
    assert info["value"] == pytest.approx(manager.properties[ResourceType.CLOTH].calculate_value(15.0, 0.8))
    assert info["weight"] == manager.properties[ResourceType.CLOTH].weight * 15.0

def test_storage_info():
    """Test storage information retrieval."""
    manager = ResourceManager()
    
    # Add various resources
    manager.add_resource(ResourceType.WOOD, 30.0)
    manager.add_resource(ResourceType.STONE, 20.0)
    
    # Get storage info
    info = manager.get_storage_info()
    assert info
    assert len(info["resources"]) == 2
    assert "WOOD" in info["resources"]
    assert "STONE" in info["resources"]
    assert info["stored_weight"] > 0
    assert info["free_space"] == info["capacity"] - info["stored_weight"]

def test_save_load_state():
    """Test saving and loading resource state."""
    manager = ResourceManager()
    
    # Set up some resources
    manager.add_resource(ResourceType.FOOD, 25.0, quality=0.9)
    manager.add_resource(ResourceType.TOOLS, 5.0, quality=1.0)
    
    # Save state
    state = manager.save_state()
    
    # Create new manager and load state
    new_manager = ResourceManager()
    new_manager.load_state(state)
    
    # Verify state was restored
    for res_type in manager.storage:
        assert res_type in new_manager.storage
        old_stack = manager.storage[res_type]
        new_stack = new_manager.storage[res_type]
        assert old_stack.quantity == new_stack.quantity
        assert old_stack.quality == new_stack.quality 