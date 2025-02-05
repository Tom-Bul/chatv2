import pytest
import asyncio
from pathlib import Path
import json
import shutil
from datetime import datetime, timedelta

from src.core.game import Game, Character, SkillType
from src.ai import (
    AIManager,
    DialogueManager,
    NPC,
    NPCRole,
    NPCPersonality,
    NPCMemory,
    NPCSchedule,
    DialogueType
)
from .helpers import mock_ai_manager, mock_deepseek

@pytest.fixture
def test_save_dir(tmp_path):
    """Create a temporary save directory."""
    save_dir = tmp_path / "test_saves"
    save_dir.mkdir()
    return save_dir

@pytest.fixture
def game(test_save_dir, mock_ai_manager):
    """Create a game instance with a test character."""
    game = Game(save_dir=test_save_dir)
    game.ai_manager = mock_ai_manager  # Use mock AI manager
    game.create_character("Test Player")
    return game

@pytest.fixture
def ai_manager():
    """Create an AI manager instance."""
    return AIManager()

@pytest.fixture
def dialogue_manager(ai_manager):
    """Create a dialogue manager instance."""
    return DialogueManager(ai_manager)

@pytest.mark.asyncio
async def test_npc_generation(game):
    """Test NPC generation with village context."""
    # Generate initial NPCs
    await game.generate_initial_npcs(3)
    
    # Verify NPCs were created
    assert len(game.npcs) == 3
    
    for npc in game.npcs.values():
        # Check basic NPC properties
        assert isinstance(npc, NPC)
        assert npc.id
        assert npc.name
        assert isinstance(npc.role, NPCRole)
        assert isinstance(npc.personality, NPCPersonality)
        assert npc.background
        
        # Check skills
        assert npc.skills
        assert all(isinstance(v, float) for v in npc.skills.values())
        assert all(0 <= v <= 100 for v in npc.skills.values())
        
        # Check schedule
        assert isinstance(npc.schedule, NPCSchedule)
        assert npc.schedule.daily_routine
        assert npc.schedule.weekly_events

@pytest.mark.asyncio
async def test_save_load_system(game, test_save_dir):
    """Test saving and loading game state with NPCs."""
    # Generate NPCs and create some interactions
    await game.generate_initial_npcs(2)
    npc_ids = list(game.npcs.keys())
    
    # Start a conversation
    await game.start_conversation(npc_ids[0])
    await game.continue_conversation(npc_ids[0], "Hello!")
    
    # Save game
    game.save_game("test_save")
    
    # Create new game instance
    new_game = Game(save_dir=test_save_dir)
    new_game.ai_manager = game.ai_manager  # Use same mock AI manager
    
    # Load save
    success = new_game.load_game("test_save")
    assert success
    
    # Verify NPCs were restored
    assert len(new_game.npcs) == len(game.npcs)
    for npc_id, npc in game.npcs.items():
        assert npc_id in new_game.npcs
        new_npc = new_game.npcs[npc_id]
        
        # Check basic properties
        assert new_npc.name == npc.name
        assert new_npc.role == npc.role
        assert new_npc.background == npc.background
        
        # Check skills
        assert new_npc.skills == npc.skills
        
        # Check relationships
        assert new_npc.relationships == npc.relationships
        
        # Check schedule
        assert vars(new_npc.schedule) == vars(npc.schedule)

@pytest.mark.asyncio
async def test_npc_schedule(game):
    """Test NPC schedule and activity tracking."""
    # Generate an NPC
    await game.generate_initial_npcs(1)
    npc = list(game.npcs.values())[0]
    
    # Test different times
    test_times = [
        (6, "wake up"),
        (8, "start work"),
        (12, "lunch"),
        (13, "continue work"),
        (17, "end work"),
        (22, "sleep")
    ]
    
    for hour, expected_activity in test_times:
        time = datetime.now().replace(hour=hour)
        activity = npc.get_current_activity(time)
        assert activity == expected_activity
    
    # Test weekly events
    monday = datetime.now()
    while monday.strftime("%A") != "Monday":
        monday += timedelta(days=1)
    
    activity = npc.get_current_activity(monday)
    assert "market day" in activity.lower()

@pytest.mark.asyncio
async def test_dialogue_context(game):
    """Test dialogue context and response generation."""
    # Generate an NPC
    await game.generate_initial_npcs(1)
    npc_id = list(game.npcs.keys())[0]
    npc = game.npcs[npc_id]
    
    # Start conversation
    response1 = await game.start_conversation(npc_id)
    assert response1
    
    # Continue with context-relevant input
    response2 = await game.continue_conversation(
        npc_id,
        f"What do you do as a {npc.role.name.lower()}?"
    )
    assert response2
    
    # Check response relevance
    assert isinstance(response2, str)
    
    # Ask about schedule
    current_time = datetime.now()
    current_activity = npc.get_current_activity(current_time)
    response3 = await game.continue_conversation(
        npc_id,
        "What are you doing right now?"
    )
    assert response3
    assert isinstance(response3, str)

@pytest.mark.asyncio
async def test_error_handling(game):
    """Test error handling in AI interactions."""
    # Test invalid NPC ID
    response = await game.start_conversation("invalid_id")
    assert response is None
    
    # Generate an NPC
    await game.generate_initial_npcs(1)
    npc_id = list(game.npcs.keys())[0]
    
    # Test empty input
    response = await game.continue_conversation(npc_id, "")
    assert response is None
    
    # Test ending non-existent conversation
    response = await game.end_conversation("invalid_id")
    assert response is None
    
    # Test concurrent conversations
    await game.start_conversation(npc_id)
    response = await game.start_conversation(npc_id)
    assert response is None  # Should not allow second conversation 