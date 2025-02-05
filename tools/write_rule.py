#!/usr/bin/env python3

import os
from pathlib import Path
import sys

def write_rule(filepath: str, description: str, globs: list[str], content: str) -> None:
    """Write a rule file with YAML frontmatter and content."""
    # Create directory if it doesn't exist
    Path(os.path.dirname(filepath)).mkdir(parents=True, exist_ok=True)
    
    # Format the file content with manual YAML formatting
    file_content = "---\n"
    file_content += f"description: {description}\n"
    # Format globs with single quotes around each item
    formatted_globs = "[" + ", ".join(f"'{g}'" for g in globs) + "]"
    file_content += f"globs: {formatted_globs}\n"
    file_content += "---\n\n"
    file_content += content
    
    # Write to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(file_content)
    print(f"Rule created successfully: {filepath}")

def write_ui_ux_rule():
    """Create the UI/UX requirements rule."""
    write_rule(
        filepath=".cursor/rules/ui-ux/requirements.mdc",
        description="UI/UX requirements and guidelines for the project",
        globs=[
            "src/ui/**/*.py",
            "src/**/*_ui.py",
            "src/**/*_view.py",
            "tests/ui/**/*.py"
        ],
        content="""# UI/UX Requirements

## Core Requirements

### Window Properties
- Minimum size: 1200x800 pixels
- Font: Courier New, 14pt
- Menu width: 80 characters
- Input field width: ≥70 characters

### Navigation
- Support both arrow keys and vim-style (h,j,k,l) navigation
- Space bar for action/confirmation
- Escape for cancel/back
- Tab for field navigation
- Enter for confirmation

### Visual Feedback
- Clear cursor indication in input fields
- Highlight current selection
- Visual feedback for all actions
- Consistent border styles
- Clear menu hierarchy

## Game Interface

### Main Display
- ASCII art for game visualization
- Clear separation of game areas
- Status indicators
- Resource counters
- Time display

### Menu System
- Hierarchical navigation
- Keyboard shortcuts
- Context-sensitive help
- Quick access to common actions
- Persistent state display

### Input Handling
1. Key Events:
   - Log all key codes for debugging
   - Handle special keys explicitly
   - Accept events to prevent propagation
   - Update display after key handling
   - Maintain focus after transitions

2. Focus Management:
   - Clear focus indicators
   - Logical tab order
   - Focus restoration after dialogs
   - No focus traps
   - Keyboard accessibility

## Best Practices

1. User Feedback:
   - Immediate response to actions
   - Clear error messages
   - Status updates
   - Progress indicators
   - Success confirmations

2. Error Prevention:
   - Confirm destructive actions
   - Validate input
   - Provide default values
   - Clear error recovery
   - Undo/redo support

3. Performance:
   - Smooth animations
   - Quick response times
   - No UI freezes
   - Efficient redraws
   - Background processing

4. Accessibility:
   - Keyboard navigation
   - High contrast
   - Clear text
   - Consistent layout
   - Error announcements

5. Testing:
   - UI component tests
   - Integration tests
   - User interaction tests
   - Focus management tests
   - Event handling tests"""
    )

def write_game_loop_rule():
    """Create the game loop performance rule."""
    write_rule(
        filepath=".cursor/rules/performance/game-loop.mdc",
        description="Performance guidelines and best practices for game loop implementation",
        globs=[
            "src/core/game.py",
            "src/core/loop.py",
            "src/core/time.py",
            "src/**/*_loop.py"
        ],
        content="""# Game Loop Performance Guidelines

## Core Principles

1. Fixed Time Step:
   - Target 60 Hz for game logic
   - Decouple rendering from updates
   - Use accumulator for time steps
   - Handle variable frame times
   - Maintain consistent game speed

2. State Management:
   - Separate state from rendering
   - Track previous and current states
   - Use interpolation for smooth visuals
   - Handle state transitions
   - Maintain state history

3. Performance Optimization:
   - Profile critical paths
   - Optimize hot loops
   - Minimize allocations
   - Use efficient data structures
   - Cache frequently used values

4. Resource Management:
   - Pool frequently created objects
   - Clean up unused resources
   - Monitor memory usage
   - Handle resource limits
   - Implement proper cleanup

## Implementation Guidelines

1. Threading and Concurrency:
   - Use async for I/O
   - Avoid blocking operations
   - Handle thread safety
   - Manage thread pools
   - Coordinate updates

2. Power Management:
   - Implement frame limiting
   - Sleep when inactive
   - Reduce update frequency
   - Handle background state
   - Monitor power usage

3. Debug and Profiling:
   - Add performance metrics
   - Log frame times
   - Track state changes
   - Monitor resource usage
   - Profile critical sections

4. Platform Specific:
   - Handle vsync
   - Manage refresh rates
   - Deal with sleep precision
   - Handle system events
   - Support power states"""
    )

def write_systems_rule():
    """Create the system architecture rule."""
    write_rule(
        filepath=".cursor/rules/architecture/systems.mdc",
        description="System architecture and design patterns for the project",
        globs=[
            "src/core/**/*.py",
            "src/systems/**/*.py",
            "src/**/*_system.py"
        ],
        content="""# System Architecture

## Core Systems

1. Task System:
   - UUID-based task identification
   - Template-based generation
   - Skill-based requirements
   - Tool requirements
   - Seasonal effects
   - Progress tracking
   - State persistence

2. Weather System:
   - Enum-based weather types
   - Seasonal patterns
   - Smooth transitions
   - Intensity scaling
   - Effect application
   - State persistence
   - Event generation

3. Resource System:
   - Quality tracking
   - Quantity management
   - Storage limits
   - Decay rates
   - Seasonal effects
   - Value calculation
   - State persistence

## Design Patterns

1. Event System:
   - Publisher/Subscriber pattern
   - Event queuing
   - Priority handling
   - Error recovery
   - State tracking

2. Component System:
   - Entity composition
   - Component management
   - System updates
   - State synchronization
   - Resource cleanup

3. Factory System:
   - Object creation
   - Template management
   - Instance pooling
   - State initialization
   - Resource management

## Best Practices

1. System Integration:
   - Clear interfaces
   - Event-driven communication
   - State synchronization
   - Resource sharing
   - Error handling

2. State Management:
   - Immutable state
   - State history
   - Transaction support
   - Rollback capability
   - State validation

3. Performance:
   - Lazy initialization
   - Resource pooling
   - Batch processing
   - Cache optimization
   - Memory management"""
    )

def write_testing_rule():
    """Create the testing best practices rule."""
    write_rule(
        filepath=".cursor/rules/testing/best-practices.mdc",
        description="Testing guidelines and best practices for the project",
        globs=[
            "tests/**/*.py",
            "src/**/*_test.py",
            "pytest.ini",
            "conftest.py"
        ],
        content="""# Testing Best Practices

## Core Principles

1. Test Organization:
   - Follow pytest conventions
   - Keep test files focused
   - Use appropriate fixtures
   - Handle timing-sensitive tests
   - Update dependencies as needed

2. Test Types:
   - Unit tests for components
   - Integration tests for systems
   - UI tests with pytest-qt
   - Async tests with pytest-asyncio
   - Performance tests

3. Test Coverage:
   - Core abstractions: 100%
   - Modifier system: 100%
   - Resource system: 100%
   - Task system: 100%
   - Weather system: 100%
   - Integration tests: 80%
   - Performance tests: Critical paths

## Implementation Guidelines

1. Test Structure:
   - Use descriptive test names
   - Follow AAA pattern (Arrange, Act, Assert)
   - One assertion per test
   - Clear test documentation
   - Proper cleanup in fixtures

2. UI Testing:
   - Use QTest.qWait() for timing
   - Test focus management
   - Verify event handling
   - Check state transitions
   - Test keyboard navigation

3. Async Testing:
   - Use proper async fixtures
   - Test concurrent operations
   - Handle timeouts properly
   - Mock long-running operations
   - Test error conditions

4. Test Environment:
   - Clean test directory before/after
   - Use temporary files/directories
   - Mock external dependencies
   - Control random seeds
   - Isolate test state

## Best Practices

1. Test Maintenance:
   - Keep tests up to date
   - Refactor with implementation
   - Remove obsolete tests
   - Update test documentation
   - Review test coverage

2. Test Performance:
   - Optimize slow tests
   - Parallelize test execution
   - Cache test results
   - Profile test suite
   - Monitor test times

3. Test Quality:
   - Test edge cases
   - Verify error handling
   - Test boundary conditions
   - Check invalid inputs
   - Test cleanup code"""
    )

def write_project_status_rule():
    """Create the current project status rule."""
    write_rule(
        filepath=".cursor/rules/project-status/current-state.mdc",
        description="Current state and progress of the project",
        globs=[
            "**/*",
            ".cursor/rules/**/*.mdc"
        ],
        content="""# Project Status

## Development Phases

### Phase 1: Core Engine & Basic Systems
[X] Project Setup
[ ] Core Game Loop
  - Basic character creation
  - Time system (real-time tracking)
  - Save/Load functionality
  - Basic task system
[ ] Initial UI Framework
  - ASCII renderer
  - Basic HUD
  - Menu system
[ ] AI Integration
  - DeepSeek-r1:7b setup
  - Basic NPC generation
  - Simple dialogue system

### Phase 2: Character & Task Systems
[ ] Character System
  - Skills (stamina, knowledge, crafting, etc.)
  - Experience tracking
  - Level progression
  - Equipment system
[ ] Task System
  - Task categories (chores, learning, exercise)
  - Time tracking integration
  - Task-to-skill mapping
  - Quest generation
[ ] Basic Village Mechanics
  - Resource management
  - Simple building system
  - Initial NPC roles

### Phase 3: Village & NPC Development
[ ] Advanced NPC System
  - Personality generation
  - Story/background generation
  - Relationship system
  - Memory/context tracking
[ ] Village Evolution
  - Dynamic role assignment
  - Building progression
  - Resource chains
  - Community events
[ ] Advanced Quest System
  - Story-driven quests
  - NPC-specific quests
  - Village development quests

### Phase 4: Advanced Features & Polish
[ ] Advanced AI Features
  - Complex dialogue trees
  - Event generation
  - Dynamic story adaptation
[ ] Enhanced Village Systems
  - Economy simulation
  - Inter-NPC relationships
  - Village events
[ ] UI Polish
  - Enhanced ASCII art
  - Improved HUD
  - Sound effects (optional)

## Current Phase
- Core System Refactoring
  - Abstract base classes
  - Generic type constraints
  - Event-driven architecture
  - Plugin system foundation
  - Uniform interfaces

## Implementation Progress

1. Core Module Updates
   [X] Create abstract base classes
     - IResource
     - ITask
     - IWeather
     - ITimeManager
     - IGameState
   
   [X] Implement event system
     - EventBus
     - Event types
     - Observer pattern
     - Event handlers

   [X] Design plugin architecture
     - Plugin registry
     - Plugin loader
     - Extension points
     - Plugin interfaces

2. Resource System Enhancements
   [X] Resource transformation pipeline
   [X] Quality propagation system
   [X] Resource combination rules
   [X] Storage management
   [X] Resource events

3. Task System Improvements
   [X] Task composition system
   [X] Prerequisite chain handling
   [X] Task modification system
   [X] Task event propagation
   [X] Task result handling

4. Integration Updates
   [X] Weather effects system
   [X] Time influence system
   [X] Location management
   [X] State persistence
   [X] Cross-system events

## Next Steps
1. [X] Update resource_manager.py to use new abstractions
2. [X] Update task.py to use new abstractions
3. [X] Update weather_manager.py to use new abstractions
4. [X] Add tests for core abstractions
5. [X] Add tests for modifier system
6. [X] Add tests for resource system
7. [X] Add tests for task system
8. [ ] Add tests for weather system
9. [ ] Add integration tests

## Known Issues
1. Performance optimization needed for large resource collections
2. Weather transition smoothing needs improvement
3. Task chain visualization pending
4. Resource decay rate tuning required
5. Plugin hot-reload system incomplete"""
    )

def write_game_design_rule():
    """Create the game design rule."""
    write_rule(
        filepath=".cursor/rules/design/game-design.mdc",
        description="Core gameplay concepts and design requirements",
        globs=[
            "src/**/*.py",
            "docs/**/*.md",
            "design/**/*.md"
        ],
        content="""# Game Design

## Project Vision
A text-based ASCII game and productivity tool for Mac that combines real-life task tracking with village building and character progression. The game uses local AI (Ollama with DeepSeek-r1:7b) for dynamic NPC interactions and story generation.

## Core Gameplay Requirements

1. Task System:
   - Mixed approach: self-reporting + time tracking
   - Categories: chores, cleaning, cooking, learning, exercises
   - Tasks integrated naturally into story and quests
   - Real-world activities reflect in-game progress

2. Progression System:
   - Long-term gameplay focus
   - Realistic development timelines
   - RuneScape-like skill progression mixed with RPG elements
   - Skills tied to real activities (e.g., exercise improves stamina)
   - Equipment/items earned through task completion

3. Village Development:
   - Natural, organic growth
   - Realistic population scaling (e.g., 3 villagers = cottage phase)
   - Dynamic role evolution based on village size
   - Collaborative building between player and NPCs
   - Survival focus in early stages

4. NPC System:
   - Using DeepSeek-r1:7b for AI interactions
   - Focus on story and personality generation
   - Natural role development
   - Random events influence development
   - Organic relationship building

## User Preferences
- Natural progression and development
- Realistic timelines
- Organic role evolution
- Focus on story and personality
- Mixed task tracking approach
- Long-term engagement design

## Core Systems

1. Time System:
   - Real-world time tracking
   - Game time progression
   - Configurable time scale
   - Event scheduling
   - Time-based effects

2. Character System:
   - Skill progression
   - Inventory management
   - Relationship tracking
   - Task completion history
   - Achievement system

3. Task System:
   - Category-based organization
   - Difficulty scaling
   - Reward calculation
   - Progress tracking
   - Quest integration

4. Village System:
   - Population management
   - Resource distribution
   - Building progression
   - Event generation
   - Development tracking

5. NPC System:
   - Personality traits
   - Story generation
   - Role assignment
   - Daily routines
   - Relationship development"""
    )

def write_architecture_principles_rule():
    """Create the architecture principles rule."""
    write_rule(
        filepath=".cursor/rules/architecture/principles.mdc",
        description="Core architectural principles and design philosophy",
        globs=[
            "src/**/*.py",
            "tests/**/*.py",
            "docs/architecture/**/*"
        ],
        content="""# Architecture Principles

## Core Philosophy

Design for Maximum Modularity and Interconnection:
- Every system should be able to interact with other systems
- Use interfaces and abstract classes for flexibility
- Avoid hard-coded relationships between components
- Design systems to be extensible without modifying existing code
- Use event systems for inter-component communication

## Design Principles

1. Component Design:
   - Make components composable and reusable
   - Implement generic type parameters where beneficial
   - Use dependency injection for loose coupling
   - Design data structures that can be easily extended
   - Create flexible serialization systems

2. System Architecture:
   - Allow for dynamic loading of new content
   - Support modding through plugin architecture
   - Use observer pattern for system interactions
   - Implement component-based architecture
   - Design for emergent gameplay

3. State Management:
   - Make systems stateless where possible
   - Use strategy pattern for interchangeable behaviors
   - Support runtime configuration of relationships
   - Design for testability and simulation
   - Create uniform interfaces for similar concepts

## System Interactions

Examples:
- Resources should work with any crafting system
- Weather should affect all outdoor activities
- Skills should be applicable to multiple task types
- Tools should be usable in creative ways
- Buildings should interact with multiple systems
- NPCs should respond to any event type
- Seasons should affect all relevant systems
- Quality should propagate through transformations
- Time should influence all appropriate systems
- Location should matter for all activities

## Implementation Guidelines

1. Code Organization:
   - Use abstract base classes for core concepts
   - Implement generic type constraints
   - Design flexible data structures
   - Create uniform interfaces
   - Use event-driven architecture

2. Design Patterns:
   - Implement visitor pattern for interactions
   - Design plugin system for extensions
   - Use factory pattern for object creation
   - Implement command pattern for actions
   - Create decorator pattern for modifications

3. Best Practices:
   - Follow SOLID principles
   - Use dependency injection
   - Implement event-driven design
   - Create clear interfaces
   - Support extensibility"""
    )

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Creating all rules...")
        write_ui_ux_rule()
        write_game_loop_rule()
        write_systems_rule()
        write_testing_rule()
        write_project_status_rule()
        write_game_design_rule()
        write_architecture_principles_rule()
    else:
        rule_name = sys.argv[1]
        if rule_name == "ui-ux":
            write_ui_ux_rule()
        elif rule_name == "game-loop":
            write_game_loop_rule()
        elif rule_name == "systems":
            write_systems_rule()
        elif rule_name == "testing":
            write_testing_rule()
        elif rule_name == "project-status":
            write_project_status_rule()
        elif rule_name == "game-design":
            write_game_design_rule()
        elif rule_name == "architecture-principles":
            write_architecture_principles_rule()
        else:
            print(f"Unknown rule: {rule_name}")
            print("Available rules: ui-ux, game-loop, systems, testing, project-status, game-design, architecture-principles")
            sys.exit(1) 