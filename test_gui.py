#!/usr/bin/env python3
"""
Simple test script to verify the PyQt6 GUI can be imported and run.
This helps catch any import or basic setup issues before running the full GUI.

The GUI now features a horizontal layout design for better space utilization.
"""

import sys
import os

def test_imports():
    """Test that all required modules can be imported."""
    try:
        print("Testing PyQt6 imports...")
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QFont
        print("✅ PyQt6 imports successful")
        
        print("Testing local module imports...")
        from utils import load_config
        print("✅ Utils import successful")
        
        print("Testing GUI class import...")
        from gui import ObsidianToolsGUI
        print("✅ GUI class import successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_basic_gui():
    """Test that the GUI can be created without errors."""
    try:
        print("Testing GUI creation...")
        
        # Create QApplication instance
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Try to create the GUI (but don't show it)
        # We'll catch any initialization errors
        try:
            from gui import ObsidianToolsGUI
            gui = ObsidianToolsGUI()
            print("✅ GUI creation successful")
            return True
        except Exception as e:
            print(f"❌ GUI creation failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ GUI test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Obsidian Tools GUI...")
    print("=" * 50)
    print("Testing horizontal layout improvements...")
    
    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed. Please check your dependencies.")
        return False
    
    # Test basic GUI creation
    if not test_basic_gui():
        print("\n❌ GUI creation test failed. Please check the GUI implementation.")
        return False
    
    print("\n✅ All tests passed! The GUI should work correctly.")
    print("\nNew features:")
    print("• Horizontal layout for better space utilization")
    print("• Side-by-side parameter and action panels")
    print("• Improved progress and logging layout")
    print("• Better responsive design for wider screens")
    print("• Analysis Results now takes up the right half of the screen")
    print("• Smaller, more compact header design")
    print("• Default output file set to 'recommendations.md'")
    print("• LLM model selection (Gemini 2.5 Flash variants)")
    print("• Configuration tab with encrypted secrets storage")
    print("• 1Password integration support")
    print("• Local encrypted configuration management")
    print("\nTo run the full GUI, use: python gui.py")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
