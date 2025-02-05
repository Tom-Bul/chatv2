import sys
from pathlib import Path
import pytest
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication
from datetime import timedelta

from village_life.ui.game_window import GameWindow, AsciiMenu
from village_life.core.task import TaskType

@pytest.fixture(scope="session")
def app():
    """Create a Qt application for the entire test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    app.quit()

@pytest.fixture
def game_window(app, qtbot):
    """Create the game window with proper cleanup."""
    window = GameWindow()
    window.show()
    qtbot.addWidget(window)
    
    # Ensure window is ready
    qtbot.waitExposed(window)
    
    yield window
    
    # Clean up
    window.close()
    qtbot.wait(100)

def test_initial_state(game_window):
    """Test the initial state of the game window."""
    assert game_window.current_menu == "main"
    assert not game_window.is_inputting
    assert not game_window.show_help
    assert game_window.input_buffer == ""

def test_menu_navigation(game_window, qtbot):
    """Test basic menu navigation."""
    # Test down navigation
    initial_selected = game_window.menus["main"].get_selected()
    qtbot.keyClick(game_window, Qt.Key.Key_Down)
    qtbot.wait(100)
    after_down = game_window.menus["main"].get_selected()
    assert after_down != initial_selected
    
    # Test up navigation
    qtbot.keyClick(game_window, Qt.Key.Key_Up)
    qtbot.wait(100)
    after_up = game_window.menus["main"].get_selected()
    assert after_up == initial_selected

def test_help_toggle(game_window, qtbot):
    """Test help overlay toggling."""
    assert not game_window.show_help
    
    # Toggle help on
    qtbot.keyClick(game_window, Qt.Key.Key_H)
    qtbot.wait(100)
    assert game_window.show_help
    
    # Toggle help off
    qtbot.keyClick(game_window, Qt.Key.Key_H)
    qtbot.wait(100)
    assert not game_window.show_help

def test_menu_transitions(game_window, qtbot):
    """Test menu transitions."""
    # Test direct menu changes
    game_window.current_menu = "main"
    game_window.change_menu("character_creation")
    qtbot.wait(100)
    assert game_window.current_menu == "character_creation"
    
    game_window.change_menu("main")
    qtbot.wait(100)
    assert game_window.current_menu == "main"

def test_menu_state_persistence(game_window, qtbot):
    """Test menu state persistence."""
    # Navigate to feedback menu
    game_window.current_menu = "main"
    game_window.change_menu("feedback")
    qtbot.wait(100)
    
    # Select an option
    initial_selection = game_window.menus["feedback"].get_selected()
    game_window.menus["feedback"].move_down()
    new_selection = game_window.menus["feedback"].get_selected()
    assert new_selection != initial_selection
    
    # Return to main menu and back
    game_window.change_menu("main")
    qtbot.wait(100)
    assert game_window.current_menu == "main"
    
    # Go back to feedback menu
    game_window.change_menu("feedback")
    qtbot.wait(100)
    
    # Verify selection was preserved
    assert game_window.menus["feedback"].get_selected() == new_selection

def test_invalid_menu_handling(game_window):
    """Test handling of invalid menu states."""
    # Store original menu
    original_menu = game_window.current_menu
    
    # Try to access non-existent menu
    with pytest.raises(KeyError):
        game_window.menus["nonexistent"]
    
    # Try to transition to invalid menu
    game_window.change_menu("invalid_menu")
    assert game_window.current_menu == original_menu

def test_menu_rendering(game_window):
    """Test menu rendering."""
    # Test main menu rendering
    game_window.current_menu = "main"
    rendered = game_window.menus["main"].render()
    assert "New Game" in rendered
    assert "Load Game" in rendered
    assert "Quit" in rendered
    
    # Test menu with selection
    game_window.menus["main"].selected = 1
    rendered = game_window.menus["main"].render()
    assert "►" in rendered
    
    # Test empty menu
    empty_menu = AsciiMenu([])
    rendered = empty_menu.render()
    assert "Empty Menu" in rendered
    assert "No items" in rendered

def test_input_handling(game_window, qtbot):
    """Test input handling in various contexts."""
    # Test character name input
    game_window.current_menu = "character_creation"
    game_window.is_inputting = True
    game_window.input_prompt = "Enter character name:"
    
    # Type name
    qtbot.keyClicks(game_window, "TestChar")
    qtbot.wait(100)
    assert game_window.input_buffer == "TestChar"
    
    # Submit name
    qtbot.keyClick(game_window, Qt.Key.Key_Return)
    qtbot.wait(100)
    assert game_window.game.character is not None
    assert game_window.game.character.name == "TestChar"

def test_task_management(game_window, qtbot):
    """Test task creation and management."""
    # Setup character
    game_window.game.create_character("TestChar")
    game_window.current_menu = "task_creation"
    
    # Test task name input
    game_window.is_inputting = True
    game_window.input_prompt = "Enter task name:"
    qtbot.keyClicks(game_window, "Test Task")
    qtbot.keyClick(game_window, Qt.Key.Key_Return)
    qtbot.wait(100)
    assert game_window.new_task["name"] == "Test Task"
    
    # Test task type cycling
    initial_type = game_window.new_task["type"]
    qtbot.keyClick(game_window, Qt.Key.Key_Tab)
    qtbot.wait(100)
    assert game_window.new_task["type"] != initial_type

def test_game_state_management(game_window, qtbot, tmp_path):
    """Test game state management."""
    # Setup temporary save file
    game_window.game.save_file = tmp_path / "test_save.json"
    
    # Create and save character
    game_window.game.create_character("TestChar")
    game_window.current_menu = "game"
    
    # Test save game
    save_menu = game_window.menus["game"]
    while save_menu.get_selected() != "Save Game":
        save_menu.move_down()
    qtbot.keyClick(game_window, Qt.Key.Key_Return)
    qtbot.wait(100)
    assert game_window.game.save_file.exists()

def test_display_updates(game_window, qtbot):
    """Test display updates with game state changes."""
    initial_text = game_window.display.toPlainText()
    
    # Change menu
    game_window.change_menu("character_creation")
    qtbot.wait(100)
    new_text = game_window.display.toPlainText()
    assert new_text != initial_text
    
    # Toggle help
    game_window.show_help = True
    game_window.current_menu = "main"
    game_window.update_display()
    help_text = game_window.display.toPlainText()
    assert any(text in help_text for text in ["Controls:", "Navigation:", "Keys:"])

def test_effect_manager(game_window, qtbot):
    """Test menu effect manager integration."""
    # Test menu change effect
    initial_effects = len(game_window.effect_manager._effects)
    game_window.change_menu("character_creation")
    qtbot.wait(100)
    assert len(game_window.effect_manager._effects) > initial_effects

def test_cursor_blinking(game_window, qtbot):
    """Test cursor blinking in input mode."""
    game_window.is_inputting = True
    initial_cursor = game_window.cursor_visible
    
    # Wait for cursor blink
    qtbot.wait(600)  # Cursor blinks every 500ms
    assert game_window.cursor_visible != initial_cursor 

def test_game_loading(game_window, qtbot, tmp_path):
    """Test game loading functionality."""
    # Setup save file
    save_file = tmp_path / "test_save.json"
    game_window.game.save_file = save_file
    
    # Create and save initial game state
    game_window.game.create_character("TestChar")
    game_window.game.save_game()
    
    # Reset game state
    game_window.game.character = None
    assert game_window.game.character is None
    
    # Test loading
    game_window.current_menu = "main"
    load_menu = game_window.menus["main"]
    while load_menu.get_selected() != "Load Game":
        load_menu.move_down()
    qtbot.keyClick(game_window, Qt.Key.Key_Return)
    qtbot.wait(100)
    
    assert game_window.game.character is not None
    assert game_window.game.character.name == "TestChar"

def test_task_completion_and_rewards(game_window, qtbot):
    """Test task completion and reward system."""
    # Setup character and task
    game_window.game.create_character("TestChar")
    game_window.current_menu = "task_creation"
    
    # Create task
    game_window.is_inputting = True
    game_window.input_prompt = "Enter task name:"
    qtbot.keyClicks(game_window, "Test Task")
    qtbot.keyClick(game_window, Qt.Key.Key_Return)
    qtbot.wait(100)
    
    # Set duration
    game_window.input_prompt = "Enter duration (minutes):"
    qtbot.keyClicks(game_window, "5")
    qtbot.keyClick(game_window, Qt.Key.Key_Return)
    qtbot.wait(100)
    
    # Create task
    create_menu = game_window.menus["task_creation"]
    while create_menu.get_selected() != "Create Task":
        create_menu.move_down()
    qtbot.keyClick(game_window, Qt.Key.Key_Return)
    qtbot.wait(100)
    
    # Verify task was created
    assert len(game_window.game.active_tasks) == 1
    
    # Complete task
    game_window.complete_task()
    qtbot.wait(100)
    
    # Verify task completion
    assert len(game_window.game.active_tasks) == 0

def test_npc_interactions(game_window, qtbot):
    """Test NPC menu and interactions."""
    # Setup game state
    game_window.game.create_character("TestChar")
    game_window.current_menu = "game"
    
    # Navigate to NPC menu
    game_window.change_menu("npcs")
    qtbot.wait(100)
    assert game_window.current_menu == "npcs"
    
    # Test NPC menu options
    npc_menu = game_window.menus["npcs"]
    assert "View NPCs" in npc_menu.items
    assert "Generate NPCs" in npc_menu.items
    
    # Test NPC view
    while npc_menu.get_selected() != "View NPCs":
        npc_menu.move_down()
    qtbot.keyClick(game_window, Qt.Key.Key_Return)
    qtbot.wait(100)
    
    # Verify NPC menu is shown
    assert game_window.npc_menu.isVisible()

def test_resource_management(game_window, qtbot):
    """Test resource management system."""
    # Setup game state
    game_window.game.create_character("TestChar")
    
    # Get initial resource state
    initial_state = game_window.game.get_current_state()
    initial_resources = initial_state.get("resources", {})
    
    # Create gathering task
    game_window.current_menu = "task_creation"
    game_window.new_task = {
        "name": "Gather Resources",
        "type": TaskType.GATHERING,
        "duration": timedelta(minutes=5)
    }
    
    # Complete task to generate resources
    game_window.handle_menu_selection()
    game_window.complete_task()
    qtbot.wait(100)
    
    # Verify resources were added
    new_state = game_window.game.get_current_state()
    new_resources = new_state.get("resources", {})
    assert new_resources != initial_resources

def test_time_management(game_window, qtbot):
    """Test time management system."""
    # Setup game state
    game_window.game.create_character("TestChar")
    
    # Get initial time state
    initial_state = game_window.game.get_current_state()
    initial_time = initial_state.get("time", {})
    
    # Create task with duration
    game_window.current_menu = "task_creation"
    game_window.new_task = {
        "name": "Time Test",
        "type": TaskType.CRAFTING,
        "duration": timedelta(minutes=30)
    }
    
    # Complete task to advance time
    game_window.handle_menu_selection()
    game_window.complete_task()
    qtbot.wait(100)
    
    # Verify time advanced
    new_state = game_window.game.get_current_state()
    new_time = new_state.get("time", {})
    assert new_time != initial_time

def test_weather_effects(game_window, qtbot):
    """Test weather system and its effects."""
    # Setup game state with character
    game_window.game.create_character("TestChar")
    
    # Get initial weather state
    initial_state = game_window.game.get_current_state()
    initial_weather = initial_state.get("weather", {"type": "CLEAR", "intensity": 1.0})
    
    # Update game multiple times to trigger weather change
    for _ in range(100):  # Increase updates to ensure weather change
        game_window.update_game()
        qtbot.wait(10)
    
    # Verify weather state changed
    new_state = game_window.game.get_current_state()
    new_weather = new_state.get("weather", {"type": "CLEAR", "intensity": 1.0})
    assert new_weather.get("type") != initial_weather.get("type") or \
           new_weather.get("intensity") != initial_weather.get("intensity")

def test_error_handling(game_window, qtbot):
    """Test error handling scenarios."""
    # Test invalid task creation
    game_window.current_menu = "task_creation"
    game_window.new_task = {
        "name": "",  # Invalid empty name
        "type": TaskType.GATHERING,
        "duration": None
    }
    
    # Attempt to create invalid task
    create_menu = game_window.menus["task_creation"]
    while create_menu.get_selected() != "Create Task":
        create_menu.move_down()
    qtbot.keyClick(game_window, Qt.Key.Key_Return)
    qtbot.wait(100)
    
    # Verify task was not created
    assert len(game_window.game.active_tasks) == 0
    
    # Test invalid menu navigation
    game_window.change_menu("nonexistent_menu")
    assert game_window.current_menu != "nonexistent_menu"
    
    # Test invalid character actions
    game_window.game.character = None
    game_window.complete_task()  # Should not raise exception
    
    # Test invalid input handling
    game_window.is_inputting = True
    game_window.input_prompt = "Enter duration (minutes):"
    qtbot.keyClicks(game_window, "invalid")
    qtbot.keyClick(game_window, Qt.Key.Key_Return)
    qtbot.wait(100)
    assert game_window.new_task["duration"] is None

def test_ui_responsiveness(game_window, qtbot):
    """Test UI responsiveness during long operations."""
    # Setup game state
    game_window.game.create_character("TestChar")
    
    # Create long running task
    game_window.current_menu = "task_creation"
    game_window.new_task = {
        "name": "Long Task",
        "type": TaskType.CRAFTING,
        "duration": timedelta(hours=1)
    }
    
    # Start task
    game_window.handle_menu_selection()
    qtbot.wait(100)
    
    # Verify UI is still responsive
    initial_menu = game_window.current_menu
    game_window.change_menu("main")
    qtbot.wait(100)
    assert game_window.current_menu == "main"
    
    # Test display updates during task
    initial_display = game_window.display.toPlainText()
    game_window.update_game()
    qtbot.wait(100)
    new_display = game_window.display.toPlainText()
    assert new_display != initial_display 