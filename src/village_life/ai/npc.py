from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum, auto

class NPCRole(Enum):
    VILLAGER = auto()
    FARMER = auto()
    MERCHANT = auto()
    CRAFTSMAN = auto()
    GUARD = auto()
    HEALER = auto()
    TEACHER = auto()
    LEADER = auto()

@dataclass
class NPCPersonality:
    openness: float = 0.5  # 0-1, curiosity and creativity
    conscientiousness: float = 0.5  # 0-1, organization and responsibility
    extraversion: float = 0.5  # 0-1, sociability and energy
    agreeableness: float = 0.5  # 0-1, cooperation and compassion
    neuroticism: float = 0.5  # 0-1, emotional stability (inverse)

@dataclass
class NPCMemory:
    event_id: str
    timestamp: datetime
    event_type: str
    description: str
    emotional_response: str
    facts_learned: List[str]
    importance: float = 0.5  # 0-1, how important this memory is

@dataclass
class NPCSchedule:
    daily_routine: Dict[int, str] = field(default_factory=dict)  # hour -> activity
    weekly_events: Dict[str, List[str]] = field(default_factory=dict)  # day -> events

@dataclass
class NPC:
    id: str
    name: str
    role: NPCRole
    personality: NPCPersonality
    background: str
    skills: Dict[str, float] = field(default_factory=dict)
    relationships: Dict[str, float] = field(default_factory=dict)  # NPC ID -> relationship value
    schedule: NPCSchedule = field(default_factory=NPCSchedule)
    memories: List[NPCMemory] = field(default_factory=list)
    
    def get_current_activity(self, time: datetime) -> str:
        """Get the NPC's current activity based on time."""
        # Check weekly events first
        day = time.strftime("%A")
        if day in self.schedule.weekly_events:
            for event in self.schedule.weekly_events[day]:
                return f"Attending {event}"
        
        # Check daily routine
        hour = time.hour
        if hour in self.schedule.daily_routine:
            return self.schedule.daily_routine[hour]
        
        # Default activity
        return "resting"
    
    def get_response_context(self, conversation_context: dict) -> dict:
        """Get context for generating responses."""
        return {
            "name": self.name,
            "role": self.role.name,
            "personality": vars(self.personality),
            "background": self.background,
            "skills": self.skills,
            "current_activity": self.get_current_activity(datetime.now()),
            "conversation": conversation_context
        }
    
    def update_relationship(self, other_id: str, value: float) -> None:
        """Update relationship with another NPC."""
        current = self.relationships.get(other_id, 0.0)
        # Apply diminishing returns
        if value > 0:
            change = value / (1 + max(0, current) / 50)
        else:
            change = value / (1 + max(0, -current) / 50)
        self.relationships[other_id] = max(-100, min(100, current + change))
    
    def get_relevant_memories(
        self,
        context: str,
        limit: int = 5,
        min_importance: float = 0.3
    ) -> List[NPCMemory]:
        """Get memories relevant to the current context."""
        # TODO: Implement semantic search
        relevant = [
            mem for mem in self.memories
            if mem.importance >= min_importance
            and any(fact.lower() in context.lower() for fact in mem.facts_learned)
        ]
        return sorted(
            relevant,
            key=lambda m: (m.importance, m.timestamp),
            reverse=True
        )[:limit] 