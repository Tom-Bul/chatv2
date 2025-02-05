import pytest
from datetime import datetime, timedelta
from pathlib import Path

from src.core.game import Game, Task, TaskType, SkillType

@pytest.fixture
def test_save_dir(tmp_path):
    """Create a temporary save directory."""
    save_dir = tmp_path / "test_saves"
    save_dir.mkdir()
    return save_dir

@pytest.fixture
def game(test_save_dir):
    """Create a game instance with a test character."""
    game = Game(save_dir=test_save_dir)
    game.create_character("Test Player")
    return game

def test_game_initialization(game):
    """Test game initialization."""
    assert game.character
    assert game.character.name == "Test Player"
    assert game.active_tasks == []
    assert game.completed_tasks == []

def test_task_management(game):
    """Test task management."""
    # Create a test task
    task = Task(
        name="Test Task",
        description="A test task",
        type=TaskType.CHORE,
        duration=timedelta(minutes=30),
        requirements={},
        rewards={"STAMINA": 5.0}
    )
    
    # Add task
    game.add_task(task)
    assert len(game.active_tasks) == 1
    assert game.active_tasks[0].name == "Test Task"
    
    # Complete task
    game.complete_task(task)
    assert len(game.active_tasks) == 0
    assert len(game.completed_tasks) == 1
    assert game.character.skills[SkillType.STAMINA] > 0

def test_save_load_game(game, test_save_dir):
    """Test saving and loading game state."""
    # Add a task
    task = Task(
        name="Test Task",
        description="A test task",
        type=TaskType.CHORE,
        duration=timedelta(minutes=30),
        requirements={},
        rewards={"STAMINA": 5.0}
    )
    game.add_task(task)
    
    # Save game
    game.save_game("test_save")
    
    # Create new game instance
    new_game = Game(save_dir=test_save_dir)
    
    # Load save
    success = new_game.load_game("test_save")
    assert success
    
    # Verify state
    assert new_game.character.name == game.character.name
    assert len(new_game.active_tasks) == len(game.active_tasks)
    assert new_game.active_tasks[0].name == game.active_tasks[0].name

def test_game_time(game):
    """Test game time management."""
    # Test time update
    assert game.time.update() is True  # Should return True on first update
    
    # Test interpolation
    state1 = game.get_current_state()
    game.time.update()
    state2 = game.get_current_state()
    
    interpolated = game.get_interpolated_state()
    assert isinstance(interpolated, dict)
    assert "stats" in interpolated
    assert "skills" in interpolated 