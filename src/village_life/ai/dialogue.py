from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum, auto
import json
import logging
from pathlib import Path

from .npc import NPC, NPCMemory
from .manager import AIManager

# Set up logging
logging.basicConfig(
    filename='game.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DialogueType(Enum):
    GREETING = auto()
    CASUAL = auto()
    QUEST = auto()
    TRADE = auto()
    TEACH = auto()
    GOSSIP = auto()
    FAREWELL = auto()

@dataclass
class DialogueContext:
    dialogue_type: DialogueType
    location: str
    time: datetime
    participants: List[str]  # NPC IDs
    previous_topics: List[str] = field(default_factory=list)
    mood: Dict[str, float] = field(default_factory=dict)  # NPC ID -> mood value
    important: bool = False
    quest_related: bool = False

@dataclass
class DialogueResponse:
    text: str
    npc_id: str
    timestamp: datetime
    context: DialogueContext
    relationship_changes: Dict[str, float] = field(default_factory=dict)
    memory_importance: float = 0.5

class DialogueManager:
    def __init__(self, ai_manager: AIManager):
        self.ai_manager = ai_manager
        self.active_conversations: Dict[str, List[DialogueResponse]] = {}
        self.conversation_history: List[DialogueResponse] = []
        self.max_history_per_conversation = 10
        self.max_total_history = 1000
        
        # Load conversation history
        self.load_history()
    
    def load_history(self) -> None:
        """Load conversation history from file."""
        history_file = Path("saves/dialogue_history.json")
        if not history_file.exists():
            return
            
        try:
            with open(history_file) as f:
                data = json.load(f)
                self.conversation_history = [
                    DialogueResponse(**item) for item in data
                ]
                logger.info(f"Loaded {len(self.conversation_history)} dialogue responses")
        except Exception as e:
            logger.error(f"Error loading dialogue history: {e}")
    
    def save_history(self) -> None:
        """Save conversation history to file."""
        history_file = Path("saves/dialogue_history.json")
        history_file.parent.mkdir(exist_ok=True)
        
        try:
            # Keep only the most recent conversations
            recent_history = self.conversation_history[-self.max_total_history:]
            
            with open(history_file, 'w') as f:
                json.dump([vars(r) for r in recent_history], f, indent=2)
            logger.info(f"Saved {len(recent_history)} dialogue responses")
        except Exception as e:
            logger.error(f"Error saving dialogue history: {e}")
    
    async def start_conversation(
        self,
        npc: NPC,
        dialogue_type: DialogueType,
        location: str,
        initial_context: Optional[Dict] = None
    ) -> DialogueResponse:
        """Start a new conversation with an NPC."""
        logger.info(f"Starting {dialogue_type.name} conversation with {npc.name}")
        
        # Create initial context
        context = DialogueContext(
            dialogue_type=dialogue_type,
            location=location,
            time=datetime.now(),
            participants=[npc.id],
            mood={npc.id: 0.0}  # Neutral mood
        )
        
        # Update context with additional information
        if initial_context:
            for key, value in initial_context.items():
                if hasattr(context, key):
                    setattr(context, key, value)
        
        # Generate initial response
        response = await self.generate_response(npc, context)
        
        # Start tracking conversation
        self.active_conversations[npc.id] = [response]
        
        return response
    
    async def continue_conversation(
        self,
        npc: NPC,
        player_input: str,
        additional_context: Optional[Dict] = None
    ) -> DialogueResponse:
        """Continue an existing conversation with an NPC."""
        if npc.id not in self.active_conversations:
            logger.warning(f"No active conversation with {npc.name}, starting new one")
            return await self.start_conversation(
                npc,
                DialogueType.CASUAL,
                "unknown",
                additional_context
            )
        
        # Get conversation history
        history = self.active_conversations[npc.id]
        last_context = history[-1].context
        
        # Update context
        context = DialogueContext(
            dialogue_type=last_context.dialogue_type,
            location=last_context.location,
            time=datetime.now(),
            participants=last_context.participants,
            previous_topics=last_context.previous_topics,
            mood=last_context.mood,
            important=last_context.important,
            quest_related=last_context.quest_related
        )
        
        # Update context with additional information
        if additional_context:
            for key, value in additional_context.items():
                if hasattr(context, key):
                    setattr(context, key, value)
        
        # Generate response
        response = await self.generate_response(
            npc,
            context,
            player_input=player_input,
            conversation_history=history[-5:]  # Last 5 exchanges
        )
        
        # Update conversation tracking
        history.append(response)
        if len(history) > self.max_history_per_conversation:
            history.pop(0)
        
        # Update global history
        self.conversation_history.append(response)
        if len(self.conversation_history) > self.max_total_history:
            self.conversation_history.pop(0)
        
        # Save history periodically
        if len(self.conversation_history) % 10 == 0:
            self.save_history()
        
        return response
    
    async def end_conversation(self, npc: NPC) -> Optional[DialogueResponse]:
        """End a conversation with an NPC."""
        if npc.id not in self.active_conversations:
            logger.warning(f"No active conversation with {npc.name} to end")
            return None
        
        # Generate farewell
        history = self.active_conversations[npc.id]
        last_context = history[-1].context
        
        farewell_context = DialogueContext(
            dialogue_type=DialogueType.FAREWELL,
            location=last_context.location,
            time=datetime.now(),
            participants=last_context.participants,
            previous_topics=last_context.previous_topics,
            mood=last_context.mood
        )
        
        response = await self.generate_response(
            npc,
            farewell_context,
            conversation_history=history[-3:]  # Last 3 exchanges
        )
        
        # Clean up
        del self.active_conversations[npc.id]
        self.conversation_history.append(response)
        self.save_history()
        
        return response
    
    async def generate_response(
        self,
        npc: NPC,
        context: DialogueContext,
        player_input: Optional[str] = None,
        conversation_history: Optional[List[DialogueResponse]] = None
    ) -> DialogueResponse:
        """Generate a dialogue response from an NPC."""
        # Prepare conversation context
        conv_context = {
            "type": context.dialogue_type.name,
            "location": context.location,
            "time": context.time.isoformat(),
            "mood": context.mood.get(npc.id, 0),
            "player_input": player_input,
            "history": [
                {
                    "text": r.text,
                    "speaker": r.npc_id,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in (conversation_history or [])
            ]
        }
        
        # Get NPC's response context
        npc_context = npc.get_response_context(conv_context)
        
        try:
            # Generate response using AI
            response_text = await self.ai_manager.generate_dialogue(
                npc.id,
                npc_context
            )
            
            # Create response object
            response = DialogueResponse(
                text=response_text,
                npc_id=npc.id,
                timestamp=datetime.now(),
                context=context
            )
            
            # Update NPC memory if important
            if context.important or context.quest_related:
                await self.ai_manager.update_npc_memory(
                    npc.id,
                    {
                        "type": "dialogue",
                        "content": response_text,
                        "context": vars(context),
                        "timestamp": response.timestamp.isoformat()
                    }
                )
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating dialogue response: {e}")
            # Fallback response
            return DialogueResponse(
                text="...",
                npc_id=npc.id,
                timestamp=datetime.now(),
                context=context
            ) 