"""Tests for menu transitions and effects."""

import pytest
from datetime import datetime
import time
from PyQt6.QtTest import QTest
from src.ui.menu_transitions import (
    TransitionType,
    MenuTransition,
    MenuAnimator,
    MenuEffect,
    MenuEffectManager
)

@pytest.fixture
def animator():
    """Create a MenuAnimator instance."""
    return MenuAnimator()

@pytest.fixture
def effect_manager():
    """Create a MenuEffectManager instance."""
    return MenuEffectManager()

def test_transition_types():
    """Test all transition types are properly defined."""
    assert len(TransitionType) == 5
    assert TransitionType.FADE in TransitionType
    assert TransitionType.SLIDE_LEFT in TransitionType
    assert TransitionType.SLIDE_RIGHT in TransitionType
    assert TransitionType.SLIDE_UP in TransitionType
    assert TransitionType.SLIDE_DOWN in TransitionType

def test_menu_transition_progress(qapp):
    """Test menu transition progress calculation."""
    transition = MenuTransition(
        from_menu="main",
        to_menu="game",
        type=TransitionType.SLIDE_RIGHT,
        duration=0.1  # Short duration for testing
    )
    
    # Initial state
    assert transition.progress == 0.0
    assert not transition.is_complete
    
    # Update after some time
    QTest.qWait(50)  # Wait for half duration (50ms)
    transition.update()
    assert transition.progress > 0.0
    assert transition.progress < 1.0
    
    # Update after full duration
    QTest.qWait(100)  # Wait for full duration (100ms)
    transition.update()
    assert transition.progress == 1.0
    assert transition.is_complete

def test_menu_animator_transitions(qapp, animator):
    """Test menu animator transition management."""
    # Initial state
    assert animator.current_transition is None
    
    # Start transition
    animator.start_transition("main", "game")
    assert animator.current_transition is not None
    assert animator.current_transition.from_menu == "main"
    assert animator.current_transition.to_menu == "game"
    
    # Get transition offset
    offset_x, offset_y = animator.get_transition_offset()
    assert isinstance(offset_x, int)
    assert isinstance(offset_y, int)
    
    # Get transition alpha
    alpha = animator.get_transition_alpha()
    assert isinstance(alpha, float)
    assert 0.0 <= alpha <= 1.0

def test_menu_effect(qapp):
    """Test menu effect behavior."""
    effect = MenuEffect(duration=0.1)  # Short duration for testing
    
    # Initial state
    assert effect.progress == 0.0
    assert not effect.is_complete
    
    # Update after some time
    QTest.qWait(50)  # Wait for half duration (50ms)
    effect.update()
    assert effect.progress > 0.0
    assert effect.progress < 1.0
    
    # Update after full duration
    QTest.qWait(100)  # Wait for full duration (100ms)
    effect.update()
    assert effect.progress == 1.0
    assert effect.is_complete

def test_menu_effect_manager(qapp, effect_manager):
    """Test menu effect manager functionality."""
    # Initial state
    assert len(effect_manager.effects) == 0
    
    # Add effect
    effect_manager.add_effect("test_item")
    assert len(effect_manager.effects) == 1
    assert "test_item" in effect_manager.effects
    
    # Get effect offset
    offset = effect_manager.get_effect_offset("test_item")
    assert isinstance(offset, int)
    
    # Update effects multiple times to ensure completion
    for _ in range(5):  # Update multiple times to ensure effect completes
        QTest.qWait(100)  # Wait between updates
        effect_manager.update()
    
    # Effect should be removed after completion
    assert len(effect_manager.effects) == 0

def test_transition_map(qapp, animator):
    """Test transition map completeness."""
    # Test all menu transitions are defined
    menus = [
        "main",
        "character_creation",
        "game",
        "tasks",
        "task_creation",
        "feedback"
    ]
    
    for from_menu in menus:
        for to_menu in menus:
            if from_menu != to_menu:
                transition_type = animator.transition_map.get(
                    (from_menu, to_menu)
                )
                assert transition_type is not None, f"Missing transition: {from_menu} -> {to_menu}"

def test_transition_offsets(qapp, animator):
    """Test transition offset calculations."""
    # Test each transition type
    for transition_type in TransitionType:
        animator.current_transition = MenuTransition(
            from_menu="test",
            to_menu="test2",
            type=transition_type,
            duration=0.1
        )
        
        # Test at different progress points
        for progress in [0.0, 0.25, 0.5, 0.75, 1.0]:
            animator.current_transition.progress = progress
            offset_x, offset_y = animator.get_transition_offset()
            
            # Verify offset values are reasonable
            assert isinstance(offset_x, int)
            assert isinstance(offset_y, int)
            assert abs(offset_x) <= 80  # Max menu width
            assert abs(offset_y) <= 24  # Max menu height 