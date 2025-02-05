#!/usr/bin/env python3
import os
import shutil
from pathlib import Path

def ensure_dir(path):
    """Create directory if it doesn't exist."""
    Path(path).mkdir(parents=True, exist_ok=True)

def create_rule_file(path, content, description, globs=None):
    """Create a rule file with proper frontmatter."""
    frontmatter = "---\n"
    frontmatter += f'description: "{description}"\n'
    if globs:
        frontmatter += f"globs: {globs}\n"
    frontmatter += "---\n\n"
    
    with open(path, 'w') as f:
        f.write(frontmatter + content)

def organize_rules():
    """Organize rules into proper directory structure."""
    # Setup directories
    rules_dir = Path('.cursor/rules')
    ensure_dir(rules_dir)
    for subdir in ['core', 'testing', 'ui-ux', 'performance', 'architecture', 'design', 'dev-stack', 'project-status']:
        ensure_dir(rules_dir / subdir)
    
    # Read backup file
    with open('.cursorrules.backup', 'r') as f:
        backup_content = f.read()
    
    # Extract sections and create rule files
    sections = {
        'content-management': {
            'path': rules_dir / 'core/content-management.mdc',
            'description': 'Content management guidelines and rules',
            'globs': None,
            'content': ''  # Extract content management section
        },
        'tools': {
            'path': rules_dir / 'core/tools.mdc',
            'description': 'Available tools and their usage',
            'globs': ['tools/**/*.py'],
            'content': ''  # Extract tools section
        },
        'lessons': {
            'path': rules_dir / 'core/lessons.mdc',
            'description': 'Lessons learned and best practices',
            'globs': None,
            'content': ''  # Extract lessons section
        },
        # Add more sections as needed
    }
    
    # Create rule files
    for section, info in sections.items():
        create_rule_file(
            info['path'],
            info['content'],
            info['description'],
            info['globs']
        )
    
    # Keep .cursorrules as index
    if not os.path.exists('.cursorrules.original'):
        shutil.copy('.cursorrules', '.cursorrules.original')
    
    # Archive backup
    if os.path.exists('.cursorrules.backup'):
        archive_dir = rules_dir / 'archive'
        ensure_dir(archive_dir)
        shutil.move('.cursorrules.backup', archive_dir / 'rules.backup')

if __name__ == '__main__':
    organize_rules() 