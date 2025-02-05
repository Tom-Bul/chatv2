import sys
from pathlib import Path
import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))
from src.ui.game_window import GameWindow

@pytest.fixture
def app():
    """Create a Qt application."""
    return QApplication(sys.argv)

@pytest.fixture
def game_window(app):
    """Create the game window."""
    window = GameWindow()
    window.show()
    return window

def test_initial_state(game_window):
    """Test the initial state of the game window."""
    assert game_window.current_menu == "main"
    assert not game_window.is_inputting
    assert not game_window.show_help
    assert game_window.input_buffer == ""

def test_arrow_navigation(game_window):
    """Test menu navigation with arrow keys."""
    # Get initial selection
    initial_selected = game_window.menus["main"].get_selected()
    
    # Press down arrow
    QTest.keyClick(game_window, Qt.Key.Key_Down)
    after_down = game_window.menus["main"].get_selected()
    assert after_down != initial_selected
    
    # Press up arrow
    QTest.keyClick(game_window, Qt.Key.Key_Up)
    after_up = game_window.menus["main"].get_selected()
    assert after_up == initial_selected

def test_help_toggle(game_window):
    """Test help overlay toggling."""
    assert not game_window.show_help
    
    # Toggle help with H key
    QTest.keyClick(game_window, Qt.Key.Key_H)
    assert game_window.show_help
    
    # Toggle help off
    QTest.keyClick(game_window, Qt.Key.Key_H)
    assert not game_window.show_help

def test_character_creation(game_window):
    """Test character creation workflow."""
    # Navigate to New Game
    while game_window.menus["main"].get_selected() != "New Game":
        QTest.keyClick(game_window, Qt.Key.Key_Down)
    
    # Start new game
    QTest.keyClick(game_window, Qt.Key.Key_Return)
    assert game_window.current_menu == "character_creation"
    
    # Select Enter Name
    while game_window.menus["character_creation"].get_selected() != "Enter Name":
        QTest.keyClick(game_window, Qt.Key.Key_Down)
    
    # Enter name
    QTest.keyClick(game_window, Qt.Key.Key_Return)
    assert game_window.is_inputting
    
    # Type name
    test_name = "TestPlayer"
    for char in test_name:
        QTest.keyClick(game_window, Qt.Key.Key_A + ord(char.lower()) - ord('a'))
    
    # Confirm name
    QTest.keyClick(game_window, Qt.Key.Key_Return)
    assert game_window.game.character.name == test_name
    assert game_window.current_menu == "game"

def test_task_creation(game_window):
    """Test task creation workflow."""
    # First create a character
    test_character_creation(game_window)
    
    # Navigate to Tasks
    while game_window.menus["game"].get_selected() != "Tasks":
        QTest.keyClick(game_window, Qt.Key.Key_Down)
    QTest.keyClick(game_window, Qt.Key.Key_Return)
    
    # Select Add Task
    while game_window.menus["tasks"].get_selected() != "Add Task":
        QTest.keyClick(game_window, Qt.Key.Key_Down)
    QTest.keyClick(game_window, Qt.Key.Key_Return)
    
    # Enter task name
    while game_window.menus["task_creation"].get_selected() != "Enter Task Name":
        QTest.keyClick(game_window, Qt.Key.Key_Down)
    QTest.keyClick(game_window, Qt.Key.Key_Return)
    
    # Type task name
    test_task = "TestTask"
    for char in test_task:
        QTest.keyClick(game_window, Qt.Key.Key_A + ord(char.lower()) - ord('a'))
    QTest.keyClick(game_window, Qt.Key.Key_Return)
    
    # Cycle task type with Tab
    initial_type = game_window.new_task["type"]
    QTest.keyClick(game_window, Qt.Key.Key_Tab)
    assert game_window.new_task["type"] != initial_type
    
    # Set duration
    while game_window.menus["task_creation"].get_selected() != "Set Duration":
        QTest.keyClick(game_window, Qt.Key.Key_Down)
    QTest.keyClick(game_window, Qt.Key.Key_Return)
    
    # Type duration
    for char in "30":
        QTest.keyClick(game_window, Qt.Key.Key_0 + int(char))
    QTest.keyClick(game_window, Qt.Key.Key_Return)
    
    # Create task
    while game_window.menus["task_creation"].get_selected() != "Create Task":
        QTest.keyClick(game_window, Qt.Key.Key_Down)
    QTest.keyClick(game_window, Qt.Key.Key_Return)
    
    # Verify task was created
    assert len(game_window.game.active_tasks) == 1
    assert game_window.game.active_tasks[0].name == test_task

def test_escape_navigation(game_window):
    """Test menu navigation with escape key."""
    # Go to character creation
    while game_window.menus["main"].get_selected() != "New Game":
        QTest.keyClick(game_window, Qt.Key.Key_Down)
    QTest.keyClick(game_window, Qt.Key.Key_Return)
    assert game_window.current_menu == "character_creation"
    
    # Press escape to go back
    QTest.keyClick(game_window, Qt.Key.Key_Escape)
    assert game_window.current_menu == "main"

def test_vim_style_navigation(game_window):
    """Test vim-style navigation with J/K keys."""
    # Get initial selection
    initial_selected = game_window.menus["main"].get_selected()
    
    # Press J (down)
    QTest.keyClick(game_window, Qt.Key.Key_J)
    after_down = game_window.menus["main"].get_selected()
    assert after_down != initial_selected
    
    # Press K (up)
    QTest.keyClick(game_window, Qt.Key.Key_K)
    after_up = game_window.menus["main"].get_selected()
    assert after_up == initial_selected 