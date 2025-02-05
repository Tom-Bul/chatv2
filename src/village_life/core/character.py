"""Character module for Village Life game."""

from dataclasses import dataclass, field
from typing import Dict, List
from enum import Enum, auto

class SkillType(Enum):
    """Skill types available in the game."""
    STRENGTH = auto()
    STAMINA = auto()
    KNOWLEDGE = auto()
    CRAFTING = auto()
    SOCIAL = auto()

@dataclass
class Character:
    """Represents a character in the game."""
    name: str
    stats: Dict[str, float] = field(default_factory=lambda: {
        "health": 100.0,
        "energy": 100.0,
        "happiness": 50.0
    })
    skills: Dict[SkillType, float] = field(default_factory=lambda: {
        skill: 0.0 for skill in SkillType
    })
    inventory: List[str] = field(default_factory=list)
    relationships: Dict[str, float] = field(default_factory=dict)
    
    def update_skill(self, skill: SkillType, value: float) -> None:
        """Update a skill value with diminishing returns."""
        current = self.skills[skill]
        # Harder to improve as skill gets higher
        improvement = value / (1 + current/50)
        self.skills[skill] = min(100, current + improvement)
    
    def update_stat(self, stat: str, value: float) -> None:
        """Update a stat value, keeping it within bounds."""
        if stat in self.stats:
            self.stats[stat] = max(0, min(100, self.stats[stat] + value))
    
    def get_skill_level(self, skill: SkillType) -> float:
        """Get the current level of a skill."""
        return self.skills.get(skill, 0.0)
    
    def get_stat(self, stat: str) -> float:
        """Get the current value of a stat."""
        return self.stats.get(stat, 0.0)
    
    def add_to_inventory(self, item: str) -> None:
        """Add an item to the inventory."""
        self.inventory.append(item)
    
    def remove_from_inventory(self, item: str) -> bool:
        """Remove an item from the inventory if it exists."""
        if item in self.inventory:
            self.inventory.remove(item)
            return True
        return False
    
    def update_relationship(self, npc_id: str, value: float) -> None:
        """Update relationship value with an NPC."""
        current = self.relationships.get(npc_id, 0.0)
        self.relationships[npc_id] = max(-100, min(100, current + value))
    
    def get_relationship(self, npc_id: str) -> float:
        """Get relationship value with an NPC."""
        return self.relationships.get(npc_id, 0.0) 