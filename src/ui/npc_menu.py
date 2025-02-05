from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent, QFont

from src.core.game import Game
from src.ai import NPC, DialogueType

# Set up logging
logging.basicConfig(
    filename='game.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class MenuState:
    view: str = "list"  # list, conversation, schedule, relationships
    selected_npc: Optional[str] = None
    input_active: bool = False
    input_buffer: str = ""
    scroll_position: int = 0
    show_debug: bool = False

class NPCMenu(QWidget):
    """Menu for NPC interactions."""
    
    # Signals
    conversation_started = pyqtSignal(str)  # NPC ID
    conversation_ended = pyqtSignal(str)    # NPC ID
    
    def __init__(self, game: Game):
        super().__init__()
        self.game = game
        self.state = MenuState()
        
        # Initialize UI
        self.init_ui()
        
        # Ensure focus
        self.setFocus()
        logger.info("NPC menu initialized")
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Create ASCII display
        self.display = QTextEdit()
        self.display.setReadOnly(True)
        self.display.setFont(self.get_font())
        layout.addWidget(self.display)
        
        # Set focus policy
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Initial display update
        self.update_display()
    
    def get_font(self) -> QFont:
        """Get the font for the display."""
        font = QFont("Courier New", 14)
        font.setStyleHint(QFont.StyleHint.Monospace)
        return font
    
    def update_display(self):
        """Update the ASCII display."""
        lines = []
        
        # Title
        title = "Village NPCs"
        border = "═" * (len(title) + 4)
        lines.extend([
            f"╔{border}╗",
            f"║  {title}  ║",
            f"╚{border}╝",
            ""
        ])
        
        if self.state.view == "list":
            lines.extend(self.render_npc_list())
        elif self.state.view == "conversation":
            lines.extend(self.render_conversation())
        elif self.state.view == "schedule":
            lines.extend(self.render_schedule())
        elif self.state.view == "relationships":
            lines.extend(self.render_relationships())
        
        # Input area if in conversation
        if self.state.input_active:
            lines.extend([
                "",
                "╔═ Your response " + "═" * 55 + "╗",
                f"║ {self.state.input_buffer:<70} ║",
                "╚" + "═" * 72 + "╝"
            ])
        
        # Debug information
        if self.state.show_debug:
            lines.extend(self.render_debug_info())
        
        # Controls help
        lines.extend([
            "",
            "╔═ Controls " + "═" * 62 + "╗",
            "║ ↑/k: Move up    ↓/j: Move down    Enter: Select    Esc: Back    ║",
            "║ Tab: Switch view    D: Toggle debug    H: Help                   ║",
            "╚" + "═" * 72 + "╝"
        ])
        
        self.display.setText("\n".join(lines))
    
    def render_npc_list(self) -> List[str]:
        """Render the list of NPCs."""
        lines = []
        
        if not self.game.npcs:
            return ["No NPCs in the village yet."]
        
        for npc_id, npc in self.game.npcs.items():
            prefix = "► " if npc_id == self.state.selected_npc else "  "
            status = "Talking" if npc_id in self.game.active_conversations else "Available"
            
            # Get current activity
            current_time = datetime.now()
            activity = npc.get_current_activity(current_time)
            
            lines.extend([
                f"{prefix}{npc.name} - {npc.role.name}",
                f"   Status: {status}",
                f"   Activity: {activity}",
                f"   Skills: " + ", ".join(f"{k}: {v:.1f}" for k, v in 
                    sorted(npc.skills.items(), key=lambda x: x[1], reverse=True)[:3]),
                ""
            ])
        
        return lines
    
    def render_conversation(self) -> List[str]:
        """Render the conversation view."""
        if not self.state.selected_npc or self.state.selected_npc not in self.game.npcs:
            return ["No NPC selected for conversation."]
        
        npc = self.game.npcs[self.state.selected_npc]
        lines = [
            f"Conversation with {npc.name}",
            "═" * 72,
            ""
        ]
        
        # Get conversation history
        history = self.game.dialogue_manager.active_conversations.get(
            self.state.selected_npc, []
        )
        
        for response in history[-10:]:  # Show last 10 exchanges
            speaker = npc.name if response.npc_id == npc.id else "You"
            lines.extend([
                f"{speaker}:",
                *[f"  {line}" for line in response.text.split("\n")],
                ""
            ])
        
        return lines
    
    def render_schedule(self) -> List[str]:
        """Render the NPC's schedule."""
        if not self.state.selected_npc or self.state.selected_npc not in self.game.npcs:
            return ["No NPC selected to view schedule."]
        
        npc = self.game.npcs[self.state.selected_npc]
        lines = [
            f"{npc.name}'s Schedule",
            "═" * 72,
            "",
            "Daily Routine:",
            "─" * 72
        ]
        
        # Sort activities by hour
        for hour, activity in sorted(npc.schedule.daily_routine.items()):
            lines.append(f"{hour:02d}:00 - {activity}")
        
        lines.extend([
            "",
            "Weekly Events:",
            "─" * 72
        ])
        
        # Show weekly events
        for day, events in npc.schedule.weekly_events.items():
            lines.append(f"{day}:")
            for event in events:
                lines.append(f"  • {event}")
        
        return lines
    
    def render_relationships(self) -> List[str]:
        """Render the NPC's relationships."""
        if not self.state.selected_npc or self.state.selected_npc not in self.game.npcs:
            return ["No NPC selected to view relationships."]
        
        npc = self.game.npcs[self.state.selected_npc]
        lines = [
            f"{npc.name}'s Relationships",
            "═" * 72,
            ""
        ]
        
        if not npc.relationships:
            lines.append("No relationships developed yet.")
            return lines
        
        # Sort relationships by value
        sorted_relationships = sorted(
            npc.relationships.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        
        for other_id, value in sorted_relationships:
            if other_id in self.game.npcs:
                other_npc = self.game.npcs[other_id]
                relationship = "Friendly" if value > 30 else (
                    "Neutral" if -30 <= value <= 30 else "Hostile"
                )
                lines.append(f"{other_npc.name}: {relationship} ({value:+.1f})")
        
        return lines
    
    def render_debug_info(self) -> List[str]:
        """Render debug information."""
        if not self.state.selected_npc or self.state.selected_npc not in self.game.npcs:
            return []
        
        npc = self.game.npcs[self.state.selected_npc]
        lines = [
            "",
            "╔═ Debug Information " + "═" * 52 + "╗",
            f"║ NPC ID: {npc.id}",
            f"║ Memory Count: {len(npc.memories)}",
            f"║ Active Conversation: {self.state.selected_npc in self.game.active_conversations}",
            f"║ Current View: {self.state.view}",
            f"║ Input Active: {self.state.input_active}",
            "╚" + "═" * 72 + "╝"
        ]
        
        return lines
    
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events."""
        key = event.key()
        logger.debug(f"Key pressed in NPC menu: {key}")
        
        if self.state.input_active:
            self.handle_input_key(event)
        else:
            self.handle_navigation_key(event)
        
        # Update display
        self.update_display()
        
        # Maintain focus
        self.setFocus()
        
        # Accept the event
        event.accept()
    
    def handle_input_key(self, event: QKeyEvent) -> None:
        """Handle key events during text input."""
        key = event.key()
        
        if key == Qt.Key.Key_Return:
            # Send message
            if self.state.input_buffer:
                self.send_message()
        elif key == Qt.Key.Key_Escape:
            # Cancel input
            self.state.input_active = False
            self.state.input_buffer = ""
        elif key == Qt.Key.Key_Backspace:
            # Delete last character
            self.state.input_buffer = self.state.input_buffer[:-1]
        else:
            # Add character to input
            text = event.text()
            if text and len(self.state.input_buffer) < 70:
                self.state.input_buffer += text
    
    def handle_navigation_key(self, event: QKeyEvent) -> None:
        """Handle key events during menu navigation."""
        key = event.key()
        
        if key in (Qt.Key.Key_Up, Qt.Key.Key_K):
            # Move selection up
            if self.state.view == "list":
                npcs = list(self.game.npcs.keys())
                if npcs:
                    current_idx = npcs.index(self.state.selected_npc) if self.state.selected_npc else 0
                    self.state.selected_npc = npcs[(current_idx - 1) % len(npcs)]
        
        elif key in (Qt.Key.Key_Down, Qt.Key.Key_J):
            # Move selection down
            if self.state.view == "list":
                npcs = list(self.game.npcs.keys())
                if npcs:
                    current_idx = npcs.index(self.state.selected_npc) if self.state.selected_npc else 0
                    self.state.selected_npc = npcs[(current_idx + 1) % len(npcs)]
        
        elif key == Qt.Key.Key_Return:
            # Select current option
            if self.state.view == "list" and self.state.selected_npc:
                if self.state.selected_npc not in self.game.active_conversations:
                    self.start_conversation()
                else:
                    self.state.view = "conversation"
                    self.state.input_active = True
        
        elif key == Qt.Key.Key_Tab:
            # Switch view
            views = ["list", "conversation", "schedule", "relationships"]
            current_idx = views.index(self.state.view)
            self.state.view = views[(current_idx + 1) % len(views)]
        
        elif key == Qt.Key.Key_D:
            # Toggle debug information
            self.state.show_debug = not self.state.show_debug
        
        elif key == Qt.Key.Key_Escape:
            # Go back/close menu
            if self.state.view != "list":
                self.state.view = "list"
            elif self.state.selected_npc in self.game.active_conversations:
                self.end_conversation()
    
    async def start_conversation(self) -> None:
        """Start a conversation with the selected NPC."""
        if not self.state.selected_npc:
            return
        
        response = await self.game.start_conversation(self.state.selected_npc)
        if response:
            self.state.view = "conversation"
            self.state.input_active = True
            self.conversation_started.emit(self.state.selected_npc)
            logger.info(f"Started conversation with {self.state.selected_npc}")
    
    async def send_message(self) -> None:
        """Send the current input buffer as a message."""
        if not self.state.selected_npc or not self.state.input_buffer:
            return
        
        response = await self.game.continue_conversation(
            self.state.selected_npc,
            self.state.input_buffer
        )
        
        # Clear input buffer
        self.state.input_buffer = ""
        
        if response:
            logger.info(f"Sent message to {self.state.selected_npc}")
    
    async def end_conversation(self) -> None:
        """End the current conversation."""
        if not self.state.selected_npc:
            return
        
        response = await self.game.end_conversation(self.state.selected_npc)
        if response:
            self.state.input_active = False
            self.conversation_ended.emit(self.state.selected_npc)
            logger.info(f"Ended conversation with {self.state.selected_npc}") 