"""
Pytest configuration file.
"""

import os
import sys
import pytest
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers",
        "asyncio: mark test as requiring asyncio"
    )
    
    # Configure asyncio mode
    config.option.asyncio_mode = "auto"

@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the tests."""
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.quit()

@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment."""
    # Add any test environment setup here
    yield
    # Add any test environment cleanup here 