import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime
from typing import Dict, List, Optional

from src.ai import (
    AIManager,
    NPC,
    NPCRole,
    NPCPersonality,
    NPCMemory,
    NPCSchedule
)

class MockAIManager(AIManager):
    """Mock AI manager for testing."""
    
    async def generate_npc(self, village_context: dict) -> dict:
        """Generate a test NPC."""
        npc_count = len(village_context.get('existing_npcs', []))
        return {
            "id": f"test_npc_{npc_count}",
            "name": f"Test NPC {npc_count}",
            "role": NPCRole.VILLAGER,
            "personality": NPCPersonality(
                openness=0.5,
                conscientiousness=0.5,
                extraversion=0.5,
                agreeableness=0.5,
                neuroticism=0.5
            ),
            "background": "A test NPC",
            "skills": {
                "farming": 50.0,
                "crafting": 30.0,
                "social": 40.0
            },
            "relationships": {},
            "schedule": NPCSchedule(
                daily_routine={
                    6: "wake up",
                    8: "start work",
                    12: "lunch",
                    13: "continue work",
                    17: "end work",
                    22: "sleep"
                },
                weekly_events={
                    "Monday": ["market day"],
                    "Wednesday": ["community meeting"],
                    "Sunday": ["rest day"]
                }
            )
        }
    
    async def generate_dialogue(
        self,
        npc_id: str,
        context: dict
    ) -> str:
        """Generate test dialogue."""
        return f"Hello! I'm {context.get('name', 'a test NPC')}."
    
    async def update_npc_memory(
        self,
        npc_id: str,
        event: dict
    ) -> None:
        """Update NPC memory with test data."""
        memory = NPCMemory(
            event_id=f"test_mem_{len(self.npc_memories.get(npc_id, []))}",
            timestamp=datetime.now(),
            event_type=event["type"],
            description=event["description"],
            emotional_response="neutral",
            facts_learned=[event["description"]],
            importance=0.5
        )
        
        if npc_id not in self.npc_memories:
            self.npc_memories[npc_id] = []
        self.npc_memories[npc_id].append(memory)
    
    async def get_npc_response(
        self,
        npc_id: str,
        prompt: str,
        context: Optional[dict] = None
    ) -> str:
        """Get test NPC response."""
        return "This is a test response."

@pytest.fixture
def mock_ai_manager():
    """Fixture to provide a mock AI manager."""
    return MockAIManager()

@pytest.fixture
def mock_deepseek():
    """Fixture to mock DeepSeek API calls."""
    with patch("deepseek.DeepSeek.generate") as mock:
        mock.return_value = AsyncMock(return_value={
            "choices": [{
                "text": "This is a test response."
            }]
        })
        yield mock 