import pytest
from datetime import datetime, timedelta
from src.core.task_manager import TaskManager, TaskChain
from src.core.task import TaskType, TaskStatus, ResourceRequirement, ResourceReward
from src.core.resource_manager import ResourceType

@pytest.fixture
def task_manager():
    return TaskManager()

@pytest.fixture
def sample_skills():
    return {
        "gathering": 10.0,
        "crafting": 15.0,
        "building": 20.0
    }

@pytest.fixture
def sample_resources():
    return {
        ResourceType.WOOD: (100.0, 0.8),
        ResourceType.STONE: (50.0, 0.7),
        ResourceType.METAL: (20.0, 0.9),
        ResourceType.TOOLS: (5.0, 0.8),
        ResourceType.HERBS: (30.0, 0.6)
    }

def test_task_generation(task_manager, sample_skills, sample_resources):
    """Test task generation for different task types."""
    season = "SUMMER"
    
    # Test gathering task
    task = task_manager.generate_task(
        TaskType.GATHERING,
        sample_skills,
        sample_resources,
        season
    )
    assert task is not None
    assert task.type == TaskType.GATHERING
    assert task.duration.total_seconds() > 0
    assert len(task.resource_rewards) > 0
    
    # Test crafting task
    task = task_manager.generate_task(
        TaskType.CRAFTING,
        sample_skills,
        sample_resources,
        season
    )
    assert task is not None
    assert task.type == TaskType.CRAFTING
    assert len(task.required_resources) > 0
    assert len(task.required_tools) > 0
    
    # Test building task
    task = task_manager.generate_task(
        TaskType.BUILDING,
        sample_skills,
        sample_resources,
        season
    )
    assert task is not None
    assert task.type == TaskType.BUILDING
    assert len(task.required_resources) > 0
    assert len(task.skill_requirements) > 0

def test_task_chain_creation(task_manager, sample_skills, sample_resources):
    """Test creation of task chains."""
    chain = task_manager.create_task_chain(
        "Test Chain",
        "A test chain of tasks",
        [TaskType.GATHERING, TaskType.CRAFTING, TaskType.BUILDING],
        sample_skills,
        sample_resources,
        "SUMMER"
    )
    
    assert chain is not None
    assert len(chain.tasks) == 3
    assert chain.tasks[0].type == TaskType.GATHERING
    assert chain.tasks[1].type == TaskType.CRAFTING
    assert chain.tasks[2].type == TaskType.BUILDING
    
    # Check task prerequisites
    assert not chain.tasks[0].prerequisites
    assert chain.tasks[1].prerequisites == [chain.tasks[0].id]
    assert chain.tasks[2].prerequisites == [chain.tasks[1].id]
    
    # Check task manager state
    assert len(task_manager.active_tasks) == 3
    assert len(task_manager.task_chains) == 1

def test_task_updates(task_manager, sample_skills, sample_resources):
    """Test task progress updates."""
    chain = task_manager.create_task_chain(
        "Test Chain",
        "A test chain of tasks",
        [TaskType.GATHERING],
        sample_skills,
        sample_resources,
        "SUMMER"
    )
    
    task = chain.tasks[0]
    task.status = TaskStatus.IN_PROGRESS
    task.progress = 0.5
    
    # Update tasks
    time_passed = timedelta(minutes=30)
    task_manager.update_tasks(time_passed, "SUMMER", "CLEAR")
    
    # Check if task was completed
    if task.status == TaskStatus.COMPLETED:
        assert task.id in task_manager.completed_tasks
        assert task.id not in task_manager.active_tasks
    else:
        assert task.progress > 0.5

def test_available_tasks(task_manager, sample_skills, sample_resources):
    """Test getting available tasks."""
    chain = task_manager.create_task_chain(
        "Test Chain",
        "A test chain of tasks",
        [TaskType.GATHERING, TaskType.CRAFTING],
        sample_skills,
        sample_resources,
        "SUMMER"
    )
    
    current_time = datetime.now()
    available_tasks = task_manager.get_available_tasks(
        current_time,
        sample_resources,
        sample_skills,
        "SUMMER",
        "CLEAR"
    )
    
    assert len(available_tasks) == 2
    first_task, status = available_tasks[0]
    assert first_task.type == TaskType.GATHERING
    assert status in ["Ready to start", "Missing requirements"]

def test_task_chain_completion(task_manager, sample_skills, sample_resources):
    """Test task chain completion and unlocking."""
    # Create two chains
    chain1 = task_manager.create_task_chain(
        "Chain 1",
        "First chain",
        [TaskType.GATHERING],
        sample_skills,
        sample_resources,
        "SUMMER"
    )
    
    chain2 = task_manager.create_task_chain(
        "Chain 2",
        "Second chain",
        [TaskType.CRAFTING],
        sample_skills,
        sample_resources,
        "SUMMER"
    )
    
    # Link chains
    chain1.unlocked_chains.append(chain2.id)
    chain2.required_chains.append(chain1.id)
    
    # Complete first chain
    task = chain1.tasks[0]
    task.status = TaskStatus.COMPLETED
    task_manager.completed_tasks[task.id] = task
    task_manager.active_tasks.pop(task.id)
    
    # Update chains
    task_manager.update_task_chains()
    
    assert chain1.completed
    assert chain2.tasks[0].status == TaskStatus.AVAILABLE

def test_save_load_state(task_manager, sample_skills, sample_resources):
    """Test saving and loading task manager state."""
    # Create some tasks and chains
    chain = task_manager.create_task_chain(
        "Test Chain",
        "A test chain",
        [TaskType.GATHERING, TaskType.CRAFTING],
        sample_skills,
        sample_resources,
        "SUMMER"
    )
    
    # Complete first task
    task = chain.tasks[0]
    task.status = TaskStatus.COMPLETED
    task_manager.completed_tasks[task.id] = task
    task_manager.active_tasks.pop(task.id)
    
    # Save state
    state = task_manager.save_state()
    
    # Create new task manager and load state
    new_manager = TaskManager()
    new_manager.load_state(state)
    
    # Verify state
    assert len(new_manager.active_tasks) == len(task_manager.active_tasks)
    assert len(new_manager.completed_tasks) == len(task_manager.completed_tasks)
    assert len(new_manager.task_chains) == len(task_manager.task_chains)
    
    # Check task chain restoration
    new_chain = next(iter(new_manager.task_chains.values()))
    assert new_chain.name == chain.name
    assert len(new_chain.tasks) == len(chain.tasks)
    assert new_chain.tasks[0].status == TaskStatus.COMPLETED 