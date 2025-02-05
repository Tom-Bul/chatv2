"""
Menu transition and effect system for Village Life.

This module provides classes for handling menu transitions and effects,
including fade and slide animations between different menu states.
"""

from enum import Enum, auto
import time
import math

class TransitionType(Enum):
    """Types of menu transitions."""
    FADE = auto()
    SLIDE_LEFT = auto()
    SLIDE_RIGHT = auto()
    SLIDE_UP = auto()
    SLIDE_DOWN = auto()

class MenuTransition:
    """Handles a single menu transition animation."""
    
    def __init__(self, from_menu: str, to_menu: str, type: TransitionType, duration: float = 0.3):
        """Initialize a menu transition.
        
        Args:
            from_menu: Source menu identifier
            to_menu: Target menu identifier
            type: Type of transition animation
            duration: Duration of transition in seconds
        """
        self.from_menu = from_menu
        self.to_menu = to_menu
        self.type = type
        self.duration = duration
        self.start_time = time.time()
        self.progress = 0.0
        self.is_complete = False
    
    def update(self):
        """Update transition progress."""
        elapsed = time.time() - self.start_time
        self.progress = min(elapsed / self.duration, 1.0)
        self.is_complete = self.progress >= 1.0

class MenuAnimator:
    """Manages menu transitions and animations."""
    
    def __init__(self):
        """Initialize the menu animator."""
        self.current_transition = None
        self.transition_map = self._build_transition_map()
    
    def _build_transition_map(self):
        """Build the map of transitions between menus."""
        transitions = {}
        
        # Define standard transitions for common menu flows
        menus = [
            "main",
            "character_creation",
            "game",
            "tasks",
            "task_creation",
            "feedback"
        ]
        
        # Build transition map
        for from_menu in menus:
            for to_menu in menus:
                if from_menu == to_menu:
                    continue
                    
                # Choose transition type based on menu relationship
                if to_menu == "main":
                    transitions[(from_menu, to_menu)] = TransitionType.FADE
                elif from_menu == "main":
                    transitions[(from_menu, to_menu)] = TransitionType.SLIDE_RIGHT
                else:
                    # Default to slide transitions based on menu order
                    from_idx = menus.index(from_menu)
                    to_idx = menus.index(to_menu)
                    if from_idx < to_idx:
                        transitions[(from_menu, to_menu)] = TransitionType.SLIDE_RIGHT
                    else:
                        transitions[(from_menu, to_menu)] = TransitionType.SLIDE_LEFT
        
        return transitions
    
    def start_transition(self, from_menu: str, to_menu: str):
        """Start a new menu transition.
        
        Args:
            from_menu: Source menu identifier
            to_menu: Target menu identifier
        """
        transition_type = self.transition_map.get(
            (from_menu, to_menu),
            TransitionType.FADE
        )
        self.current_transition = MenuTransition(
            from_menu=from_menu,
            to_menu=to_menu,
            type=transition_type
        )
    
    def update(self):
        """Update current transition state."""
        if self.current_transition:
            self.current_transition.update()
    
    def get_transition_offset(self) -> tuple[int, int]:
        """Get current transition offset for menu rendering.
        
        Returns:
            Tuple of (x_offset, y_offset) in characters
        """
        if not self.current_transition:
            return (0, 0)
            
        progress = self.current_transition.progress
        menu_width = 80  # Standard menu width in characters
        menu_height = 24  # Standard menu height in characters
        
        # Calculate offset based on transition type
        if self.current_transition.type == TransitionType.SLIDE_RIGHT:
            return (int((1.0 - progress) * menu_width), 0)
        elif self.current_transition.type == TransitionType.SLIDE_LEFT:
            return (int(-progress * menu_width), 0)
        elif self.current_transition.type == TransitionType.SLIDE_UP:
            return (0, int(-progress * menu_height))
        elif self.current_transition.type == TransitionType.SLIDE_DOWN:
            return (0, int((1.0 - progress) * menu_height))
        else:  # FADE
            return (0, 0)
    
    def get_transition_alpha(self) -> float:
        """Get current transition alpha value for menu rendering.
        
        Returns:
            Alpha value between 0.0 and 1.0
        """
        if not self.current_transition:
            return 1.0
            
        if self.current_transition.type == TransitionType.FADE:
            return 1.0 - self.current_transition.progress
        return 1.0

class MenuEffect:
    """Represents a single menu effect animation."""
    
    def __init__(self, duration: float = 0.5):
        """Initialize a menu effect.
        
        Args:
            duration: Duration of effect in seconds
        """
        self.duration = duration
        self.start_time = time.time()
        self.progress = 0.0
        self.is_complete = False
    
    def update(self):
        """Update effect progress."""
        elapsed = time.time() - self.start_time
        self.progress = min(elapsed / self.duration, 1.0)
        self.is_complete = self.progress >= 1.0

class MenuEffectManager:
    """Manages menu effects and animations."""
    
    def __init__(self):
        """Initialize the effect manager."""
        self.effects = {}  # Map of item_id to MenuEffect
    
    def add_effect(self, item_id: str):
        """Add a new effect for a menu item.
        
        Args:
            item_id: Identifier for the menu item
        """
        self.effects[item_id] = MenuEffect()
    
    def update(self):
        """Update all active effects."""
        # Update and remove completed effects
        completed = []
        for item_id, effect in self.effects.items():
            effect.update()
            if effect.is_complete:
                completed.append(item_id)
        
        for item_id in completed:
            del self.effects[item_id]
    
    def get_effect_offset(self, item_id: str) -> int:
        """Get current vertical offset for a menu item.
        
        Args:
            item_id: Identifier for the menu item
        
        Returns:
            Vertical offset in characters
        """
        if item_id not in self.effects:
            return 0
            
        effect = self.effects[item_id]
        # Simple bounce effect
        return int(math.sin(effect.progress * math.pi) * 2) 