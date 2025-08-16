"""
Main entry point for ObsidianTools.

This module provides the main entry point for the restructured
ObsidianTools application.
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from gui.main_window import ObsidianToolsGUI


def main():
    """Main function to run the ObsidianTools application."""
    # Create the application
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Obsidian Tools")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("ObsidianTools")
    
    # Set application style
    app.setStyle('Fusion')
    
    # Enable high DPI scaling
    app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    
    # Create and show the main window
    try:
        window = ObsidianToolsGUI()
        window.show()
        
        # Run the application
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"Failed to start application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
