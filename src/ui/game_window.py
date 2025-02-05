from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTextEdit
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QKeyEvent
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from core.game import Game, Task, TaskType
from .npc_menu import NPCMenu
from .menu_transitions import MenuAnimator, MenuEffectManager

class AsciiMenu:
    def __init__(self, items: List[str], width: int = 40):
        self.items = items
        self.width = width
        self.selected = 0
        
    def render(self, offset_x: int = 0, offset_y: int = 0, alpha: float = 1.0) -> str:
        """Render the menu as ASCII art with offset and alpha."""
        if not self.items:
            return "╔═══ Empty Menu ═══╗\n║     No items     ║\n╚═════════════════╝"
        
        lines = []
        # Top border
        lines.append(" " * offset_x + "╔" + "═" * (self.width - 2) + "╗")
        
        # Menu items
        for i, item in enumerate(self.items):
            prefix = "► " if i == self.selected else "  "
            text = f"{prefix}{item}"
            padding = " " * (self.width - len(text) - 2)
            lines.append(" " * offset_x + f"║{text}{padding}║")
        
        # Bottom border
        lines.append(" " * offset_x + "╚" + "═" * (self.width - 2) + "╝")
        
        # Apply vertical offset
        if offset_y > 0:
            lines = [""] * offset_y + lines
        elif offset_y < 0:
            lines = lines[-offset_y:]
        
        # Apply alpha (fade effect)
        if alpha < 1.0:
            opacity = int(alpha * 255)
            lines = [f"\033[38;2;{opacity};{opacity};{opacity}m{line}\033[0m" for line in lines]
        
        return "\n".join(lines)
    
    def move_up(self) -> None:
        """Move selection up, wrapping around to bottom if at top."""
        if self.items:  # Only move if there are items
            self.selected = (self.selected - 1) % len(self.items)
    
    def move_down(self) -> None:
        """Move selection down, wrapping around to top if at bottom."""
        if self.items:  # Only move if there are items
            self.selected = (self.selected + 1) % len(self.items)
    
    def get_selected(self) -> Optional[str]:
        """Get the currently selected item."""
        if not self.items:
            return None
        return self.items[self.selected]

class GameWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.game = Game()
        
        # Game state
        self.current_menu = "main"
        self.menus = {
            "main": AsciiMenu(["Feedback", "New Game", "Load Game", "Help", "Quit"], width=80),
            "character_creation": AsciiMenu(["Enter Name", "Start Game", "Back"], width=80),
            "game": AsciiMenu(["Character", "Tasks", "Save Game", "Help", "Feedback", "Back to Main"], width=80),
            "tasks": AsciiMenu(["Add Task", "View Tasks", "Complete Task", "Help", "Back"], width=80),
            "task_creation": AsciiMenu([
                "Enter Task Name",
                "Select Type",
                "Set Duration",
                "Create Task",
                "Help",
                "Back"
            ], width=80),
            "feedback": AsciiMenu(["Submit Feedback", "View Previous Feedback", "Back"], width=80),
            "npcs": AsciiMenu([
                "View NPCs",
                "Generate NPCs",
                "Help",
                "Back"
            ], width=80)
        }
        
        # Menu transitions and effects
        self.menu_animator = MenuAnimator()
        self.effect_manager = MenuEffectManager()
        
        # Navigation state
        self.arrow_keys_working = True  # Enable both arrow keys and vim-style navigation
        
        # Help text
        self.help_text = {
            "main": [
                "Main Menu Controls:",
                "↑/↓ - Navigate menu",
                "Enter - Select option",
                "Esc - Quit game"
            ],
            "character_creation": [
                "Character Creation Controls:",
                "↑/↓ - Navigate menu",
                "Enter - Select option",
                "When entering name:",
                "  Enter - Confirm name",
                "  Esc - Cancel input",
                "  Backspace - Delete character",
                "Esc - Back to main menu"
            ],
            "game": [
                "Game Controls:",
                "↑/↓ - Navigate menu",
                "Enter - Select option",
                "H - Toggle help",
                "Esc - Back to main menu"
            ],
            "tasks": [
                "Tasks Menu Controls:",
                "↑/↓ - Navigate menu",
                "Enter - Select option",
                "H - Toggle help",
                "Esc - Back to tasks menu"
            ],
            "task_creation": [
                "Task Creation Controls:",
                "↑/↓ - Navigate menu",
                "Enter - Select option",
                "Tab - Cycle task types",
                "When entering text:",
                "  Enter - Confirm input",
                "  Esc - Cancel input",
                "  Backspace - Delete character",
                "H - Toggle help",
                "Esc - Back to tasks menu"
            ],
            "feedback": [
                "Feedback Controls:",
                "↑/↓ - Navigate menu",
                "Enter - Select option",
                "When entering feedback:",
                "  Enter - Submit feedback",
                "  Esc - Cancel",
                "  Backspace - Delete character",
                "Esc - Back to previous menu"
            ]
        }
        
        # Show help overlay
        self.show_help = False
        
        # Input state
        self.is_inputting = False
        self.input_buffer = ""
        self.input_prompt = ""
        self.input_width = 70  # Wider input area
        self.cursor_visible = True  # For blinking cursor
        
        # Create cursor blink timer
        self.cursor_timer = QTimer()
        self.cursor_timer.timeout.connect(self.blink_cursor)
        self.cursor_timer.start(500)  # Blink every 500ms
        
        # Task creation state
        self.new_task = {
            "name": "",
            "type": TaskType.CHORE,
            "duration": None
        }
        
        # Feedback file
        self.feedback_file = Path("feedback.txt")
        
        # Create NPC menu widget
        self.npc_menu = NPCMenu(self.game)
        self.npc_menu.hide()
        
        # Connect signals
        self.npc_menu.conversation_started.connect(self.on_conversation_started)
        self.npc_menu.conversation_ended.connect(self.on_conversation_ended)
        
        # Initialize UI
        self.init_ui()
        
        # Update timer (60 FPS)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_game)
        self.timer.start(1000 // 60)  # 60 FPS
        
        # Create log file
        self.log_file = Path("game.log")
        self.log_to_file("Game started")
        
        # Ensure focus
        self.setFocus()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle('Village Life')
        self.setGeometry(100, 100, 1200, 800)  # Increased window size
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create ASCII display
        self.display = QTextEdit()
        self.display.setReadOnly(True)
        font = QFont("Courier New", 14)  # Increased font size
        self.display.setFont(font)
        layout.addWidget(self.display)
        
        # Ensure main window has focus
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()
        
        self.update_display()
    
    def update_game(self):
        """Update game state and display."""
        # Update game state (fixed time step)
        self.game.update()
        
        # Update menu transitions and effects
        self.menu_animator.update()
        self.effect_manager.update()
        
        # Update display (variable rendering)
        self.update_display()
    
    def update_display(self):
        """Update the display with current game state."""
        lines = []
        
        # Get current menu transition state
        offset_x, offset_y = self.menu_animator.get_transition_offset()
        alpha = self.menu_animator.get_transition_alpha()
        
        # Game state if in game
        state = self.game.get_current_state() if self.game.character else {}
        
        if state:
            # Time and weather info
            time_info = state.get("time", {})
            if time_info:
                lines.extend([
                    f"Date: {time_info['formatted']}",
                    f"Time: {'Day' if time_info['is_daytime'] else 'Night'}",
                    f"Season: {time_info['season']}",
                    ""
                ])
            
            # Resource information
            resource_info = state.get("resources")
            if resource_info:
                resource_border = "═" * 72
                lines.extend([
                    "╔═ Resources " + resource_border[11:] + "╗",
                    f"║ Storage: {resource_info['name']} ({resource_info['stored_weight']:.1f}/{resource_info['capacity']:.1f})" + " " * 20 + "║"
                ])
                
                # Group resources by category
                basic_resources = []
                advanced_resources = []
                special_resources = []
                
                for res_name, res_data in resource_info["resources"].items():
                    if not res_data:
                        continue
                        
                    line = f"{res_name.title()}: {res_data['quantity']:.1f}"
                    if res_data['quality'] < 1.0:
                        line += f" (Quality: {res_data['quality']:.1%})"
                    if res_data['perishable']:
                        line += " *"
                    
                    if res_name in ["FOOD", "WATER", "WOOD", "STONE"]:
                        basic_resources.append(line)
                    elif res_name in ["METAL", "CLOTH", "TOOLS"]:
                        advanced_resources.append(line)
                    else:
                        special_resources.append(line)
                
                # Display resources by category
                if basic_resources:
                    lines.extend([
                        "║ Basic Resources: " + " " * 54 + "║",
                        *[f"║   • {line:<67} ║" for line in basic_resources]
                    ])
                
                if advanced_resources:
                    lines.extend([
                        "║ Advanced Resources: " + " " * 51 + "║",
                        *[f"║   • {line:<67} ║" for line in advanced_resources]
                    ])
                
                if special_resources:
                    lines.extend([
                        "║ Special Resources: " + " " * 52 + "║",
                        *[f"║   • {line:<67} ║" for line in special_resources]
                    ])
                
                # Storage space indicator
                space_used = resource_info["stored_weight"] / resource_info["capacity"]
                space_bar = "█" * int(space_used * 20)
                space_bar = space_bar.ljust(20, "░")
                
                lines.extend([
                    "║ Storage Space: " + " " * 57 + "║",
                    f"║   [{space_bar}] {space_used:>6.1%} " + " " * 39 + "║",
                    "╚" + resource_border + "╝",
                    ""
                ])
        
        # Character info if in game
        if self.game.character and self.current_menu not in ["main", "character_creation"]:
            char = self.game.character
            interpolated = self.game.get_interpolated_state()
            
            # Use interpolated values if available
            stats = interpolated.get("stats", char.stats)
            skills = interpolated.get("skills", char.skills)
            
            lines.extend([
                "╔═══ Character ═══╗",
                f"║ Name: {char.name}",
                "║ Stats:",
                *[f"║   {k}: {v:.1f}" for k, v in stats.items()],
                "║ Skills:",
                *[f"║   {k.name}: {v:.1f}" for k, v in skills.items()],
                "╚" + "═" * 17 + "╝",
                ""
            ])
        
        # Task creation info
        if self.current_menu == "task_creation":
            lines.extend([
                "╔═══ New Task ═══╗",
                f"║ Name: {self.new_task['name']}",
                f"║ Type: {self.new_task['type'].name}",
                f"║ Duration: {self.new_task['duration'] or 'None'}",
                "╚" + "═" * 15 + "╝",
                ""
            ])
        
        # Active tasks if in tasks menu
        if self.current_menu == "tasks" and self.game.active_tasks:
            lines.extend([
                "╔═══ Active Tasks ═══╗",
                *[f"║ • {t.name} ({t.type.name})" for t in self.game.active_tasks],
                "╚" + "═" * 19 + "╝",
                ""
            ])
        
        # Current menu with transition effects
        menu = self.menus[self.current_menu]
        lines.append(menu.render(offset_x, offset_y, alpha))
        lines.append("")
        
        # Input area if inputting
        if self.is_inputting:
            input_border = "═" * (self.input_width + 4)
            cursor = "█" if self.cursor_visible else " "
            lines.extend([
                f"╔{input_border}╗",
                f"║ {self.input_prompt}",
                f"║ {self.input_buffer}{cursor}{'_' * (self.input_width - len(self.input_buffer))} ║",
                f"╚{input_border}╝"
            ])
        
        # Set the display text
        self.display.setText("\n".join(lines))
        
        # Ensure focus is maintained
        self.setFocus()
    
    def change_menu(self, new_menu: str) -> None:
        """Change to a new menu with transition."""
        if new_menu != self.current_menu:
            self.menu_animator.start_transition(self.current_menu, new_menu)
            self.current_menu = new_menu
            self.log_to_file(f"Changed menu to: {new_menu}")
            self.setFocus()  # Ensure focus is maintained
    
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle keyboard input."""
        key = event.key()
        
        # Handle input mode
        if self.is_inputting:
            if key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
                self.handle_input()
            elif key == Qt.Key.Key_Escape:
                self.is_inputting = False
                self.input_buffer = ""
            elif key == Qt.Key.Key_Backspace:
                self.input_buffer = self.input_buffer[:-1]
            else:
                text = event.text()
                if text and len(self.input_buffer) < self.input_width:
                    self.input_buffer += text
        else:
            # Handle navigation
            if key == Qt.Key.Key_Up or key == Qt.Key.Key_K:
                self.menus[self.current_menu].move_up()
                self.effect_manager.add_effect(f"{self.current_menu}_up")
                self.log_to_file(f"Menu '{self.current_menu}': moved up (selected: {self.menus[self.current_menu].get_selected()})")
            elif key == Qt.Key.Key_Down or key == Qt.Key.Key_J:
                self.menus[self.current_menu].move_down()
                self.effect_manager.add_effect(f"{self.current_menu}_down")
                self.log_to_file(f"Menu '{self.current_menu}': moved down (selected: {self.menus[self.current_menu].get_selected()})")
            elif key in [Qt.Key.Key_Return, Qt.Key.Key_Enter]:
                self.handle_menu_selection()
            elif key == Qt.Key.Key_H:
                self.show_help = not self.show_help
                self.log_to_file("Toggled help overlay")
            elif key == Qt.Key.Key_Tab and self.current_menu == "task_creation":
                types = list(TaskType)
                current_idx = types.index(self.new_task["type"])
                self.new_task["type"] = types[(current_idx + 1) % len(types)]
            elif key == Qt.Key.Key_Escape:
                self.handle_escape()
        
        # Handle menu options
        if self.current_menu == "npcs":
            selected = self.menus["npcs"].get_selected()
            if selected:
                self.handle_npc_menu(selected)
        
        # Always update display
        self.update_display()
    
    def handle_input(self):
        """Handle input submission."""
        if not self.input_buffer:
            self.is_inputting = False
            return
        
        if self.current_menu == "character_creation":
            self.game.create_character(self.input_buffer)
            self.log_to_file(f"Created character: {self.input_buffer}")
        elif self.current_menu == "task_creation":
            if self.input_prompt == "Enter task name:":
                self.new_task["name"] = self.input_buffer
                self.log_to_file(f"Set task name: {self.input_buffer}")
            elif self.input_prompt == "Enter duration (minutes):":
                try:
                    minutes = int(self.input_buffer)
                    self.new_task["duration"] = timedelta(minutes=minutes)
                    self.log_to_file(f"Set task duration: {minutes} minutes")
                except ValueError:
                    self.log_to_file("Invalid duration input")
        elif self.current_menu == "feedback":
            with open(self.feedback_file, "a") as f:
                f.write(f"{datetime.now()}: {self.input_buffer}\n")
            self.log_to_file("Feedback submitted")
            self.change_menu("main")
        
        self.is_inputting = False
        self.input_buffer = ""
        
        # Always ensure focus after input handling
        self.setFocus()
        self.update_display()
    
    def handle_menu_selection(self):
        """Handle menu item selection."""
        selected = self.menus[self.current_menu].get_selected()
        
        if selected == "Help":
            self.show_help = not self.show_help
            self.log_to_file("Toggled help overlay")
            return
        
        if selected == "Feedback":
            self.change_menu("feedback")
            self.log_to_file("Opened feedback menu")
            return
        
        if self.current_menu == "main":
            if selected == "New Game":
                self.change_menu("character_creation")
                self.log_to_file("Starting character creation")
            elif selected == "Load Game":
                if self.game.load_game():
                    self.change_menu("game")
                    self.log_to_file("Game loaded")
                else:
                    self.log_to_file("No save file found")
            elif selected == "Quit":
                self.close()
                return  # Return immediately after closing
        
        elif self.current_menu == "character_creation":
            if selected == "Enter Name":
                self.is_inputting = True
                self.input_prompt = "Enter character name:"
                self.input_buffer = ""
            elif selected == "Start Game":
                if self.game.character:
                    self.change_menu("game")
                    self.log_to_file("Game started")
            elif selected == "Back":
                self.change_menu("main")
        
        elif self.current_menu == "game":
            if selected == "Character":
                self.change_menu("character")
            elif selected == "Tasks":
                self.change_menu("tasks")
            elif selected == "Save Game":
                self.game.save_game()
                self.log_to_file("Game saved")
            elif selected == "Back to Main":
                self.change_menu("main")
        
        elif self.current_menu == "tasks":
            if selected == "Add Task":
                self.change_menu("task_creation")
                self.new_task = {
                    "name": "",
                    "type": TaskType.CHORE,
                    "duration": None
                }
            elif selected == "Complete Task":
                self.complete_task()
            elif selected == "Back":
                self.change_menu("game")
        
        elif self.current_menu == "task_creation":
            if selected == "Enter Task Name":
                self.is_inputting = True
                self.input_prompt = "Enter task name:"
                self.input_buffer = ""
            elif selected == "Select Type":
                # Cycle through task types
                types = list(TaskType)
                current_idx = types.index(self.new_task["type"])
                self.new_task["type"] = types[(current_idx + 1) % len(types)]
                self.log_to_file(f"Selected task type: {self.new_task['type'].name}")
            elif selected == "Set Duration":
                self.is_inputting = True
                self.input_prompt = "Enter duration (minutes):"
                self.input_buffer = ""
            elif selected == "Create Task":
                if self.new_task["name"]:
                    task = Task(
                        name=self.new_task["name"],
                        description=f"A {self.new_task['type'].name.lower()} task",
                        type=self.new_task["type"],
                        duration=self.new_task["duration"],
                        rewards={"STAMINA": 5.0, "CRAFTING": 2.0}
                    )
                    self.game.add_task(task)
                    self.log_to_file(f"Created task: {task.name}")
                    self.change_menu("tasks")
            elif selected == "Back":
                self.change_menu("tasks")
        
        elif self.current_menu == "feedback":
            if selected == "Submit Feedback":
                self.is_inputting = True
                self.input_prompt = "Enter your feedback:"
                self.input_buffer = ""
            elif selected == "View Previous Feedback":
                if self.feedback_file.exists():
                    with open(self.feedback_file) as f:
                        feedback = f.read()
                    self.display.setText(f"Previous Feedback:\n\n{feedback}\n\nPress any key to return...")
                    self.change_menu("main")
            elif selected == "Back":
                self.change_menu("main")
                self.log_to_file("Returned to main menu")
                self.setFocus()  # Ensure focus is maintained
        
        # Always ensure focus after menu changes
        self.setFocus()
        self.update_display()
    
    def handle_escape(self):
        """Handle escape key press."""
        if self.current_menu == "main":
            self.close()
        elif self.current_menu == "character_creation":
            self.change_menu("main")
        elif self.current_menu == "game":
            self.change_menu("main")
        elif self.current_menu == "tasks":
            self.change_menu("game")
        elif self.current_menu == "task_creation":
            self.change_menu("tasks")
        elif self.current_menu == "feedback":
            self.change_menu("main")
    
    def blink_cursor(self):
        """Toggle cursor visibility for blinking effect."""
        if self.is_inputting:
            self.cursor_visible = not self.cursor_visible
            self.update_display()
    
    def handle_npc_menu(self, option: str) -> None:
        """Handle NPC menu options."""
        if option == "View NPCs":
            self.show_npc_menu()
        elif option == "Generate NPCs":
            self.generate_npcs()
        elif option == "Help":
            self.show_help = not self.show_help
        elif option == "Back":
            self.change_menu("game")
    
    def show_npc_menu(self) -> None:
        """Show the NPC interaction menu."""
        self.display.hide()
        self.npc_menu.show()
        self.npc_menu.setFocus()
    
    async def generate_npcs(self) -> None:
        """Generate new NPCs for the village."""
        await self.game.generate_initial_npcs(3)
        self.show_message("Generated 3 new NPCs!")
    
    def on_conversation_started(self, npc_id: str) -> None:
        """Handle conversation start."""
        logger.info(f"Conversation started with NPC {npc_id}")
    
    def on_conversation_ended(self, npc_id: str) -> None:
        """Handle conversation end."""
        logger.info(f"Conversation ended with NPC {npc_id}")
    
    def log_to_file(self, message: str) -> None:
        """Log a message to the game log file."""
        with open(self.log_file, "a") as f:
            f.write(f"{datetime.now()}: {message}\n")

    def complete_task(self):
        """Complete the first active task."""
        if self.game.active_tasks:
            task = self.game.active_tasks[0]
            self.game.complete_task(task)
            self.log_to_file(f"Completed task: {task.name}")

    def show_message(self, message: str) -> None:
        """Show a message to the user."""
        # This method is called when a task is completed or a message is needed to be shown
        # It's implemented here to match the original code, but it's not used in the new implementation
        print(message)  # Using print instead of a proper GUI notification

    def _draw_game_screen(self) -> None:
        """Draw the main game screen."""
        state = self.game.get_current_state()
        
        # Draw time and weather info
        if "time" in state and "weather" in state:
            time_info = state["time"]
            weather_info = state["weather"]
            
            info_lines = [
                f"Date: {time_info['formatted_date']}",
                f"Time: {'Day' if time_info['is_daytime'] else 'Night'}",
                f"Season: {time_info['season']}",
                f"Day Progress: {self._create_progress_bar(time_info['day_progress'])}",
                f"Season Progress: {self._create_progress_bar(time_info['season_progress'])}",
                "---",
                f"Weather: {weather_info['type']} ({weather_info['intensity']})",
                "Effects:"
            ]
            
            # Add weather effects with color coding
            for effect, value in weather_info["effects"].items():
                value_float = float(value.rstrip('x'))
                if value_float < 1.0:
                    color = "\033[91m"  # Red for penalties
                elif value_float > 1.0:
                    color = "\033[93m"  # Yellow for increased difficulty
                else:
                    color = "\033[92m"  # Green for normal
                info_lines.append(f"  {effect}: {color}{value}\033[0m")
            
            self._draw_box(info_lines, 0, 0, 40, len(info_lines) + 2)
            weather_box_height = len(info_lines) + 2
        else:
            weather_box_height = 0
        
        # Draw resource info
        if "resources" in state:
            resources = state["resources"]
            resource_lines = [
                "=== Resources ===",
                f"Storage: {self._create_progress_bar(resources['storage_used'] / resources['storage_capacity'])}"
            ]
            for category in ["basic", "advanced", "special"]:
                if category in resources:
                    resource_lines.append(f"--- {category.title()} ---")
                    for res in resources[category]:
                        resource_lines.append(
                            f"{res['name']}: {res['quantity']:.1f} "
                            f"(Quality: {res['quality']:.1f})"
                        )
            self._draw_box(resource_lines, 0, weather_box_height, 40, len(resource_lines) + 2)
            resource_box_height = len(resource_lines) + 2
        else:
            resource_box_height = 0
        
        # Draw character info
        if "character" in state:
            char = state["character"]
            skill_lines = ["=== Skills ==="]
            for skill, level in char["skills"].items():
                skill_lines.append(f"{skill.title()}: {level:.1f}")
            self._draw_box(
                skill_lines,
                0,
                weather_box_height + resource_box_height,
                40,
                len(skill_lines) + 2
            )
        
        # Draw task info
        if "tasks" in state:
            tasks = state["tasks"]
            task_x = 41
            
            # Available tasks
            available_lines = ["=== Available Tasks ==="]
            for task in tasks["available"]:
                status_color = "\033[92m" if task["status"] == "Ready to start" else "\033[93m"
                available_lines.extend([
                    f"{status_color}{task['name']}\033[0m",
                    f"Type: {task['type']}",
                    f"Duration: {task['duration']}",
                    f"Status: {task['status']}",
                    "---"
                ])
            self._draw_box(available_lines, task_x, 0, 80, len(available_lines) + 2)
            
            # Active tasks
            active_lines = ["=== Active Tasks ==="]
            for task in tasks["active"]:
                active_lines.extend([
                    task["name"],
                    f"Progress: {self._create_progress_bar(task['progress'])}",
                    f"Time Remaining: {task['time_remaining']}",
                    "---"
                ])
            self._draw_box(active_lines, task_x, len(available_lines) + 2, 80, len(active_lines) + 2)
            
            # Completed tasks with pending rewards
            if tasks["completed"]:
                completed_lines = ["=== Completed Tasks - Rewards Available ==="]
                for task in tasks["completed"]:
                    completed_lines.extend([
                        f"\033[92m{task['name']}\033[0m",
                        "Rewards ready to claim!",
                        "---"
                    ])
                self._draw_box(
                    completed_lines,
                    task_x,
                    len(available_lines) + len(active_lines) + 4,
                    80,
                    len(completed_lines) + 2
                )
            
            # Task chains
            if tasks["chains"]:
                chain_lines = ["=== Task Chains ==="]
                for chain in tasks["chains"]:
                    chain_lines.extend([
                        f"\033[1m{chain['name']}\033[0m",
                        chain["description"],
                        "Tasks:"
                    ])
                    for task in chain["tasks"]:
                        status_color = {
                            "LOCKED": "\033[90m",
                            "AVAILABLE": "\033[93m",
                            "IN_PROGRESS": "\033[94m",
                            "COMPLETED": "\033[92m"
                        }.get(task["status"], "\033[0m")
                        progress = f" [{self._create_progress_bar(task['progress'])}]" if task["status"] == "IN_PROGRESS" else ""
                        chain_lines.append(f"  {status_color}{task['name']} - {task['status']}{progress}\033[0m")
                    chain_lines.append("---")
                self._draw_box(
                    chain_lines,
                    task_x,
                    len(available_lines) + len(active_lines) + len(completed_lines) + 6,
                    80,
                    len(chain_lines) + 2
                )
        
        # Draw selected task details
        if state["selected_task"]:
            task_id = state["selected_task"]
            task = None
            
            # Find task in available or active tasks
            for t in tasks["available"]:
                if t["id"] == task_id:
                    task = t
                    break
            if not task:
                for t in tasks["active"]:
                    if t["id"] == task_id:
                        task = t
                        break
            
            if task:
                detail_lines = [
                    "=== Selected Task Details ===",
                    f"Name: {task['name']}",
                    f"Type: {task['type']}",
                    f"Duration: {task['duration']}",
                    "Description:",
                    task["description"]
                ]
                
                if "progress" in task:
                    detail_lines.extend([
                        "Progress:",
                        self._create_progress_bar(task["progress"]),
                        f"Time Remaining: {task['time_remaining']}"
                    ])
                
                # Add weather effects for task
                if "weather" in state:
                    weather_info = state["weather"]
                    detail_lines.extend([
                        "Weather Effects:",
                        f"  Speed: {weather_info['effects']['Task Speed']}",
                        f"  Resource Rate: {weather_info['effects']['Resource Rate']}",
                        f"  Tool Wear: {weather_info['effects']['Tool Wear']}"
                    ])
                
                self._draw_box(
                    detail_lines,
                    task_x + 81,
                    0,
                    40,
                    len(detail_lines) + 2
                )
    
    def _create_progress_bar(self, progress: float, width: int = 20) -> str:
        """Create a progress bar string."""
        filled = int(progress * width)
        return f"[{'=' * filled}{' ' * (width - filled)}]"
    
    def _handle_task_input(self, key: int) -> None:
        """Handle task-related keyboard input."""
        if not self.game.character:
            return
        
        state = self.game.get_current_state()
        if "tasks" not in state:
            return
        
        tasks = state["tasks"]
        
        # Navigation keys
        if key == Qt.Key.Key_Up:
            self._select_previous_task(tasks)
        elif key == Qt.Key.Key_Down:
            self._select_next_task(tasks)
        elif key == Qt.Key.Key_Return:
            self._start_selected_task()
        elif key == Qt.Key.Key_Escape:
            self._cancel_selected_task()
        elif key == Qt.Key.Key_Space:
            self._claim_task_rewards()
    
    def _select_previous_task(self, tasks: dict) -> None:
        """Select the previous task in the list."""
        all_tasks = (
            tasks["available"] +
            tasks["active"] +
            tasks["completed"]
        )
        if not all_tasks:
            return
        
        current_index = -1
        for i, task in enumerate(all_tasks):
            if task["id"] == self.game.selected_task:
                current_index = i
                break
        
        if current_index == -1:
            self.game.selected_task = all_tasks[0]["id"]
        else:
            self.game.selected_task = all_tasks[
                (current_index - 1) % len(all_tasks)
            ]["id"]
    
    def _select_next_task(self, tasks: dict) -> None:
        """Select the next task in the list."""
        all_tasks = (
            tasks["available"] +
            tasks["active"] +
            tasks["completed"]
        )
        if not all_tasks:
            return
        
        current_index = -1
        for i, task in enumerate(all_tasks):
            if task["id"] == self.game.selected_task:
                current_index = i
                break
        
        if current_index == -1:
            self.game.selected_task = all_tasks[0]["id"]
        else:
            self.game.selected_task = all_tasks[
                (current_index + 1) % len(all_tasks)
            ]["id"]
    
    def _start_selected_task(self) -> None:
        """Start the selected task."""
        if not self.game.selected_task:
            return
        
        if self.game.start_task(self.game.selected_task):
            self.show_message("Task started!")
        else:
            self.show_message("Cannot start task. Check requirements.")
    
    def _cancel_selected_task(self) -> None:
        """Cancel the selected task."""
        if not self.game.selected_task:
            return
        
        if self.game.cancel_task(self.game.selected_task):
            self.show_message("Task cancelled.")
        else:
            self.show_message("Cannot cancel task.")
    
    def _claim_task_rewards(self) -> None:
        """Claim rewards for the selected completed task."""
        if not self.game.selected_task:
            return
        
        if self.game.claim_task_rewards(self.game.selected_task):
            self.show_message("Rewards claimed!")
        else:
            self.show_message("No rewards to claim.") 