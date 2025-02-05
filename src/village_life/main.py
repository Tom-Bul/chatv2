#!/usr/bin/env python3

import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from village_life.ui.game_window import GameWindow

def main():
    """Main entry point for the game."""
    # Create necessary directories
    Path("saves").mkdir(exist_ok=True)
    Path("config").mkdir(exist_ok=True)
    
    # Create and start the application
    app = QApplication(sys.argv)
    window = GameWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 