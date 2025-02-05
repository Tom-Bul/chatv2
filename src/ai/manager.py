import logging
from typing import Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path
import asyncio

from .npc import NPC, NPCRole, NPCPersonality, NPCMemory, NPCSchedule

# Set up logging
logging.basicConfig(
    filename='game.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AIManager:
    """Manages AI interactions and NPC generation."""
    
    def __init__(self):
        self.npc_memories: Dict[str, List[NPCMemory]] = {}
        self.memory_file = Path("saves/memories.json")
        self.load_memories()
    
    def load_memories(self) -> None:
        """Load NPC memories from file."""
        if not self.memory_file.exists():
            return
            
        try:
            with open(self.memory_file) as f:
                data = json.load(f)
                for npc_id, memories in data.items():
                    self.npc_memories[npc_id] = [
                        NPCMemory(**mem) for mem in memories
                    ]
            logger.info(f"Loaded memories for {len(self.npc_memories)} NPCs")
        except Exception as e:
            logger.error(f"Error loading memories: {e}")
    
    def save_memories(self) -> None:
        """Save NPC memories to file."""
        self.memory_file.parent.mkdir(exist_ok=True)
        
        try:
            data = {
                npc_id: [vars(mem) for mem in memories]
                for npc_id, memories in self.npc_memories.items()
            }
            with open(self.memory_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info("Saved NPC memories")
        except Exception as e:
            logger.error(f"Error saving memories: {e}")
    
    async def generate_npc(self, village_context: dict) -> dict:
        """Generate a new NPC based on village context."""
        try:
            # TODO: Replace with actual AI call
            # For now, return a test NPC
            npc_data = {
                "id": f"npc_{len(village_context.get('existing_npcs', []))}",
                "name": f"Test NPC {len(village_context.get('existing_npcs', []))}",
                "role": NPCRole.VILLAGER,
                "personality": NPCPersonality(
                    openness=0.5,
                    conscientiousness=0.5,
                    extraversion=0.5,
                    agreeableness=0.5,
                    neuroticism=0.5
                ),
                "background": "A simple villager",
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
            logger.info(f"Generated NPC: {npc_data['name']}")
            return npc_data
            
        except Exception as e:
            logger.error(f"Error generating NPC: {e}")
            raise
    
    async def generate_dialogue(
        self,
        npc_id: str,
        context: dict
    ) -> str:
        """Generate dialogue response for an NPC."""
        try:
            # TODO: Replace with actual AI call
            # For now, return a test response
            response = f"Hello! I'm {context.get('name', 'a villager')}."
            logger.info(f"Generated dialogue for NPC {npc_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error generating dialogue: {e}")
            raise
    
    async def update_npc_memory(
        self,
        npc_id: str,
        event: dict
    ) -> None:
        """Update an NPC's memory with a new event."""
        try:
            # Create memory
            memory = NPCMemory(
                event_id=f"mem_{len(self.npc_memories.get(npc_id, []))}",
                timestamp=datetime.now(),
                event_type=event["type"],
                description=event["description"],
                emotional_response="neutral",  # TODO: Generate with AI
                facts_learned=[event["description"]],  # TODO: Extract with AI
                importance=0.5  # TODO: Calculate with AI
            )
            
            # Add to memories
            if npc_id not in self.npc_memories:
                self.npc_memories[npc_id] = []
            self.npc_memories[npc_id].append(memory)
            
            # Save periodically
            if len(self.npc_memories[npc_id]) % 10 == 0:
                self.save_memories()
                
            logger.info(f"Updated memory for NPC {npc_id}")
            
        except Exception as e:
            logger.error(f"Error updating memory: {e}")
            raise
    
    async def get_npc_response(
        self,
        npc_id: str,
        prompt: str,
        context: Optional[dict] = None
    ) -> str:
        """Get a response from an NPC based on prompt and context."""
        try:
            # TODO: Replace with actual AI call
            # For now, return a test response
            response = f"I understand. Let me think about that..."
            logger.info(f"Generated response for NPC {npc_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error getting NPC response: {e}")
            raise 