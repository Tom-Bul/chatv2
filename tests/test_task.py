import pytest
from datetime import datetime, timedelta
from src.core.task import (
    Task,
    TaskType,
    TaskStatus,
    ResourceRequirement,
    ResourceReward,
    TaskPrerequisite
)
from src.core.resource_manager import ResourceType

@pytest.fixture
def basic_task():
    """Create a basic task for testing."""
    return Task(
        id="test_task_1",
        name="Test Task",
        description="A test task",
        type=TaskType.CRAFTING,
        duration=timedelta(minutes=30)
    )

@pytest.fixture
def resource_task():
    """Create a task with resource requirements."""
    return Task(
        id="craft_tool",
        name="Craft Tool",
        description="Craft a basic tool",
        type=TaskType.CRAFTING,
        duration=timedelta(hours=1),
        required_resources=[
            ResourceRequirement(
                type=ResourceType.WOOD,
                quantity=5.0,
                min_quality=0.5
            ),
            ResourceRequirement(
                type=ResourceType.METAL,
                quantity=2.0,
                min_quality=0.7
            )
        ],
        required_tools=[
            ResourceRequirement(
                type=ResourceType.TOOLS,
                quantity=1.0,
                min_quality=0.6,
                consumed=False
            )
        ],
        resource_rewards=[
            ResourceReward(
                type=ResourceType.TOOLS,
                base_quantity=1.0,
                quality_multiplier=1.2,
                skill_multiplier=1.1,
                random_bonus=0.1
            )
        ],
        skill_requirements={"crafting": 20.0},
        skill_rewards={"crafting": 10.0},
        season_multipliers={"WINTER": 0.8, "SUMMER": 1.2},
        weather_multipliers={"rainy": 0.9, "sunny": 1.1}
    )

def test_task_initialization(basic_task):
    """Test basic task initialization."""
    assert basic_task.id == "test_task_1"
    assert basic_task.name == "Test Task"
    assert basic_task.type == TaskType.CRAFTING
    assert basic_task.status == TaskStatus.AVAILABLE
    assert basic_task.duration == timedelta(minutes=30)
    assert basic_task.progress == 0.0

def test_task_start(basic_task):
    """Test starting a task."""
    current_time = datetime.now()
    basic_task.start(current_time)
    
    assert basic_task.status == TaskStatus.IN_PROGRESS
    assert basic_task.started_at == current_time
    assert basic_task.progress == 0.0

def test_task_progress_update(basic_task):
    """Test task progress updates."""
    basic_task.start(datetime.now())
    
    # Update with half the duration
    basic_task.update_progress(
        timedelta(minutes=15),
        season="SUMMER",
        weather="sunny"
    )
    assert 0.45 <= basic_task.progress <= 0.55
    
    # Update to completion
    basic_task.update_progress(
        timedelta(minutes=15),
        season="SUMMER",
        weather="sunny"
    )
    assert basic_task.progress == 1.0
    assert basic_task.status == TaskStatus.COMPLETED

def test_resource_requirements(resource_task):
    """Test resource requirement checking."""
    current_time = datetime.now()
    available_resources = {
        ResourceType.WOOD: (10.0, 0.8),    # (quantity, quality)
        ResourceType.METAL: (5.0, 0.9),
        ResourceType.TOOLS: (2.0, 0.7)
    }
    completed_tasks = []
    current_skills = {"crafting": 25.0}
    
    # Test with sufficient resources
    can_start, reason = resource_task.can_start(
        current_time,
        available_resources,
        completed_tasks,
        current_skills,
        "SUMMER",
        "sunny"
    )
    assert can_start
    assert reason == ""
    
    # Test with insufficient quantity
    insufficient_resources = available_resources.copy()
    insufficient_resources[ResourceType.WOOD] = (2.0, 0.8)
    can_start, reason = resource_task.can_start(
        current_time,
        insufficient_resources,
        completed_tasks,
        current_skills,
        "SUMMER",
        "sunny"
    )
    assert not can_start
    assert "Not enough" in reason
    
    # Test with low quality
    low_quality_resources = available_resources.copy()
    low_quality_resources[ResourceType.METAL] = (5.0, 0.5)
    can_start, reason = resource_task.can_start(
        current_time,
        low_quality_resources,
        completed_tasks,
        current_skills,
        "SUMMER",
        "sunny"
    )
    assert not can_start
    assert "quality too low" in reason

def test_skill_requirements(resource_task):
    """Test skill requirement checking."""
    current_time = datetime.now()
    available_resources = {
        ResourceType.WOOD: (10.0, 0.8),
        ResourceType.METAL: (5.0, 0.9),
        ResourceType.TOOLS: (2.0, 0.7)
    }
    completed_tasks = []
    
    # Test with sufficient skills
    current_skills = {"crafting": 25.0}
    can_start, reason = resource_task.can_start(
        current_time,
        available_resources,
        completed_tasks,
        current_skills,
        "SUMMER",
        "sunny"
    )
    assert can_start
    
    # Test with insufficient skills
    current_skills = {"crafting": 15.0}
    can_start, reason = resource_task.can_start(
        current_time,
        available_resources,
        completed_tasks,
        current_skills,
        "SUMMER",
        "sunny"
    )
    assert not can_start
    assert "Insufficient crafting skill" in reason

def test_season_weather_effects(resource_task):
    """Test season and weather effects."""
    current_time = datetime.now()
    available_resources = {
        ResourceType.WOOD: (10.0, 0.8),
        ResourceType.METAL: (5.0, 0.9),
        ResourceType.TOOLS: (2.0, 0.7)
    }
    completed_tasks = []
    current_skills = {"crafting": 25.0}
    
    # Test favorable conditions
    can_start, _ = resource_task.can_start(
        current_time,
        available_resources,
        completed_tasks,
        current_skills,
        "SUMMER",
        "sunny"
    )
    assert can_start
    
    # Test unfavorable season
    can_start, reason = resource_task.can_start(
        current_time,
        available_resources,
        completed_tasks,
        current_skills,
        "WINTER",
        "sunny"
    )
    assert can_start  # Should still be possible, just slower

def test_task_rewards(resource_task):
    """Test reward calculations."""
    resource_task.status = TaskStatus.COMPLETED
    skill_levels = {"crafting": 50.0}
    
    # Calculate rewards
    resource_rewards, skill_rewards = resource_task.calculate_rewards(
        skill_levels,
        "SUMMER",
        "sunny"
    )
    
    # Check resource rewards
    assert len(resource_rewards) == 1
    res_type, quantity, quality = resource_rewards[0]
    assert res_type == ResourceType.TOOLS
    assert quantity > resource_task.resource_rewards[0].base_quantity  # Should be boosted
    assert 0.5 <= quality <= 1.0
    
    # Check skill rewards
    assert "crafting" in skill_rewards
    assert skill_rewards["crafting"] > 10.0  # Should be boosted by conditions

def test_task_serialization(resource_task):
    """Test task serialization and deserialization."""
    # Convert to dict
    task_dict = resource_task.to_dict()
    
    # Create new task from dict
    new_task = Task.from_dict(task_dict)
    
    # Compare properties
    assert new_task.id == resource_task.id
    assert new_task.name == resource_task.name
    assert new_task.type == resource_task.type
    assert new_task.status == resource_task.status
    assert len(new_task.required_resources) == len(resource_task.required_resources)
    assert len(new_task.resource_rewards) == len(resource_task.resource_rewards)
    assert new_task.skill_requirements == resource_task.skill_requirements
    assert new_task.season_multipliers == resource_task.season_multipliers 