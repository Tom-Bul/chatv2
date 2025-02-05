#!/usr/bin/env python3

import os

def write_rule_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)

def fix_all_rules():
    # Game Loop Performance Guidelines
    game_loop_content = '''---
description: Game loop and performance optimization guidelines
globs: ["src/**/*.py"]
---
# Game Loop Performance Guidelines

## Core Requirements
- Use fixed time step for game logic (e.g. 60 Hz)
- Separate rendering from state updates
- Implement interpolation for smooth visuals
- Track previous and current states for interpolation
- Use accumulator pattern for time step management
- Maintain consistent game speed across different hardware
- Add power management with frame rate control

## State Management
- Track previous and current states
- Implement state interpolation
- Log state changes for debugging
- Use efficient data structures
- Minimize object creation
- Profile critical sections
- Cache frequently accessed data

## Performance Optimization
- Use efficient data structures
- Minimize object creation
- Profile critical sections
- Cache frequently accessed data
- Batch similar operations
- Optimize memory usage
- Use appropriate algorithms
- Implement object pooling
- Reduce garbage collection
- Profile and optimize hot paths

## Power Management
- Implement frame rate limiting
- Use adaptive update rates
- Monitor resource usage
- Implement power-saving modes
- Balance performance and battery life
- Track system resources
- Optimize background tasks
- Handle system sleep/wake
- Monitor thermal state
- Implement power profiles

## Best Practices
- Profile before optimizing
- Document performance requirements
- Test on target hardware
- Monitor memory usage
- Track frame times
- Log performance metrics
- Use appropriate tools
- Document optimizations
- Test edge cases
- Maintain optimization history
'''

    # Tools Documentation
    tools_content = '''---
description: Documentation of available tools and their usage
globs: ["tools/**/*"]
---
# Tools

Note all the tools are in python. So in the case you need to do batch processing, you can always consult the python files and write your own script.

## LLM

You always have an LLM at your side to help you with the task. For simple tasks, you could invoke the LLM by running the following command:
```
venv/bin/python ./tools/llm_api.py --prompt "What is the capital of France?" --provider "deepseek"
```

The LLM API uses DeepSeek model:
- Local LLM (model: deepseek-r1:7b)

But usually it's a better idea to check the content of the file and use the APIs in the `tools/llm_api.py` file to invoke the LLM if needed.

## Web browser

You could use the `tools/web_scraper.py` file to scrape the web.
```
venv/bin/python ./tools/web_scraper.py --max-concurrent 3 URL1 URL2 URL3
```
This will output the content of the web pages.

## Search engine

You could use the `tools/search_engine.py` file to search the web.
```
venv/bin/python ./tools/search_engine.py "your search keywords"
```
This will output the search results in the following format:
```
URL: https://example.com
Title: This is the title of the search result
Snippet: This is a snippet of the search result
```
If needed, you can further use the `web_scraper.py` file to scrape the web page content.

## Development Tools
- Python virtual environment (./venv)
- Git for version control
- GitHub for collaboration
- pytest for testing
- black for code formatting
- mypy for type checking
- pylint for linting
- Coverage.py for test coverage

## Build Tools
- setuptools for packaging
- wheel for distribution
- pip for package management
- venv for virtual environments
- make for build automation

## Testing Tools
- pytest for unit testing
- pytest-cov for coverage
- pytest-mock for mocking
- pytest-asyncio for async tests
- QTest for Qt testing

## Documentation Tools
- Sphinx for documentation
- autodoc for API docs
- napoleon for Google style
- markdown for README
- doctest for examples

## Debugging Tools
- pdb for debugging
- logging for tracing
- traceback for errors
- profile for performance
- memory_profiler for memory

## Code Quality Tools
- black for formatting
- mypy for types
- pylint for style
- flake8 for PEP8
- bandit for security

## Deployment Tools
- docker for containers
- docker-compose for orchestration
- systemd for services
- supervisor for process control
- nginx for serving

## Monitoring Tools
- logging for events
- statsd for metrics
- prometheus for monitoring
- grafana for visualization
- sentry for errors
'''

    # Lessons Learned
    lessons_content = '''---
description: Lessons learned from user feedback and system experience
globs: ["**/*"]
---
# Lessons

## User Specified Lessons

- You have a python venv in ./venv. Use it.
- Include info useful for debugging in the program output.
- Read the file before you try to edit it.
- Due to Cursor's limit, when you use `git` and `gh` and need to submit a multiline commit message, first write the message in a file, and then use `git commit -F <filename>` or similar command to commit. And then remove the file. Include "[Cursor] " in the commit message and PR title.
- Always check feedback log after user closed an app.
- If you cannot fix something after 2-3 tries try to find a new approach. Add temporary logs to the code to help you debug. act as a real senior developer would, they would do same thing over and over again until they find a solution.
- When cannot find an easy solution to a problem, use available tools (search_engine.py, web_scraper.py, etc.) to find solutions before making changes.
- Check logs and feedback after any user interaction, especially after closing the app.
- Use only local DeepSeek model (Qwen/Qwen2.5-32B-Instruct-AWQ) for all AI interactions.

## Debugging Best Practices

- When encountering difficult bugs, especially with libraries or frameworks:
  1. Use the search_engine.py tool to find similar issues and solutions
  2. Look for recent version compatibility issues (e.g., pytest 8.0 with pytest-asyncio)
  3. Check GitHub issues and Stack Overflow for the exact error message
  4. Try solutions from most recent discussions first
  5. Document the solution in the lessons for future reference

- For test-related issues:
  1. Start with proper directory structure (follow framework conventions)
  2. Keep test files focused and well-organized
  3. Use appropriate fixtures and markers
  4. Handle timing-sensitive tests carefully (e.g., using QTest.qWait instead of time.sleep)
  5. Update dependencies when needed (e.g., upgrading pytest-asyncio to fix collection issues)

## Cursor learned

- For search results, ensure proper handling of different character encodings (UTF-8) for international queries
- Add debug information to stderr while keeping the main output clean in stdout for better pipeline integration
- When using seaborn styles in matplotlib, use 'seaborn-v0_8' instead of 'seaborn' as the style name due to recent seaborn version changes
- Be transparent about execution limitations - don't pretend to have results that weren't actually obtained
- When handling key events in PyQt6:
  - Always check the key code in logs before implementing key handling
  - Handle special keys (like space) explicitly rather than relying on text()
  - Accept the event to prevent propagation
  - Update display after key handling
  - Separate navigation keys (arrows) from alternative keys (vim-style)
  - Maintain focus after menu changes and dialog closures
  - Always call setFocus() after input handling and menu navigation
  - Return immediately after closing the application

## Project Specific
- Using local DeepSeek model (Qwen/Qwen2.5-32B-Instruct-AWQ) for all AI interactions
- Need to consider Mac-specific UI requirements
- Must handle persistent state for game progress
- Key handling in game:
  - Space bar needs explicit handling (key code 32)
  - Arrow keys and J/K keys should work independently
  - Log all key events with codes for debugging
  - Accept events to prevent propagation
  - On macOS, enable both arrow keys and vim-style navigation by default
  - Don't use conditional checks that could prevent arrow keys from working
  - Maintain focus after menu transitions
- UI requirements:
  - Minimum input width: 70 characters
  - Window size: 1200x800
  - Font: Courier New, 14pt
  - Menu width: 80 characters
  - Clear visual feedback for navigation
  - Text cursor indicator in input fields

## Resource System Design
- Use enums for resource types and categories
- Implement weighted average quality when combining resources
- Track resource decay based on real time
- Apply season effects to decay rates
- Use dataclasses for clean data structures
- Implement proper weight-based storage limits
- Log all resource operations for debugging
- Save/load complete resource state
- Calculate values based on quality and quantity
- Group resources by category for UI display
- Handle resource removal gracefully
- Track resource quality separately from quantity
- Use type hints consistently
- Implement proper error handling and logging
- Use Optional types for nullable returns
- Keep resource properties immutable
- Implement proper cleanup of empty stacks
'''

    # Content Management Rules
    content_management = '''---
description: Core content management rules and principles
globs: ["**/*"]
---
# Content Management Rules

1. Content Preservation:
   - Never delete or modify existing rules without explicit confirmation
   - Preserve historical context and lessons learned
   - Keep track of rule modifications with timestamps
   - Archive outdated rules instead of deleting them
   - Mark rules as deprecated rather than removing them

2. Context-Based Organization:
   - Rules are organized into specific contexts for better accessibility
   - Each context represents a different aspect of the project
   - Contexts can be activated or deactivated based on current task
   - Multiple contexts can be active simultaneously
   - New contexts can be created as needed

3. Available Contexts:
   - Core Rules: Fundamental guidelines and principles
   - Project Status: Current state and progress
   - Development Stack: Technical requirements and versions
   - Architecture: System design and patterns
   - Testing: Quality assurance and validation
   - UI/UX: Interface and user experience
   - Performance: Optimization and efficiency
   - Documentation: Code and project documentation
   - Deployment: Release and distribution
   - Maintenance: Updates and bug fixes

4. Context Management:
   - Review active contexts at the start of each task
   - Load only relevant contexts for current work
   - Update context status when switching tasks
   - Document context dependencies
   - Track context-specific progress

5. Rule Organization:
   - Use consistent file naming
   - Follow directory structure
   - Include YAML frontmatter
   - Use markdown formatting
   - Add descriptive comments
   - Keep rules focused
   - Link related rules
   - Version control rules
   - Track rule history
   - Document dependencies

6. Rule Maintenance:
   - Regular review schedule
   - Update outdated content
   - Remove duplicates
   - Fix broken links
   - Add missing context
   - Improve clarity
   - Track changes
   - Test rule validity
   - Update references
   - Archive old versions

7. Documentation:
   - Clear descriptions
   - Usage examples
   - Code snippets
   - Error handling
   - Best practices
   - Common pitfalls
   - Related rules
   - Version history
   - Contributors
   - References

8. Version Control:
   - Use Git for tracking
   - Meaningful commits
   - Clear messages
   - Branch strategy
   - Review process
   - Merge guidelines
   - Conflict resolution
   - Release notes
   - Tags and versions
   - Backup strategy
'''

    # Write all rules
    write_rule_file('.cursor/rules/performance/game-loop.mdc', game_loop_content)
    write_rule_file('.cursor/rules/core/tools.mdc', tools_content)
    write_rule_file('.cursor/rules/core/lessons.mdc', lessons_content)
    write_rule_file('.cursor/rules/core/content-management.mdc', content_management)

if __name__ == '__main__':
    fix_all_rules() 