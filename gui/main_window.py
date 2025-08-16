"""
Main Application Window for ObsidianTools.

This module contains the main application window and
orchestrates the tab-based interface.
"""

import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget,
    QMenuBar, QStatusBar, QSplitter, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QIcon

from core.services import ServiceContainer
from .tabs.analysis_tab import AnalysisTab
from .tabs.ingest_tab import IngestTab
from .tabs.config_tab import ConfigTab
from .tabs.research_tab import ResearchTab


class ObsidianToolsGUI(QMainWindow):
    """Main application window for ObsidianTools."""
    
    def __init__(self):
        super().__init__()
        self.service_container = ServiceContainer()
        self.setup_ui()
        self.setup_connections()
        self.setup_status_timer()
    
    def setup_ui(self):
        """Setup the main UI structure."""
        self.setWindowTitle("Obsidian Tools")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 1000)
        
        # Set application style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8fafc;
            }
            QTabWidget::pane {
                border: 1px solid #e2e8f0;
                background-color: white;
                border-radius: 8px;
                margin: 4px;
            }
            QTabWidget::tab-bar {
                alignment: center;
            }
            QTabBar::tab {
                background-color: #f1f5f9;
                border: 1px solid #e2e8f0;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: 500;
                color: #475569;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom-color: white;
                color: #1e293b;
            }
            QTabBar::tab:hover:!selected {
                background-color: #e2e8f0;
            }
        """)
        
        self.setup_central_widget()
        self.setup_menu_bar()
        self.setup_status_bar()
    
    def setup_central_widget(self):
        """Setup the main content area."""
        # Create main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setFont(QFont("Segoe UI", 10))
        
        # Create tab controllers
        self.analysis_tab = AnalysisTab(self.service_container)
        self.ingest_tab = IngestTab(self.service_container)
        self.config_tab = ConfigTab(self.service_container)
        self.research_tab = ResearchTab(self.service_container)
        
        # Add tabs
        self.tab_widget.addTab(self.analysis_tab, "📊 Analysis")
        self.tab_widget.addTab(self.ingest_tab, "📥 Ingest")
        self.tab_widget.addTab(self.config_tab, "⚙️ Configuration")
        self.tab_widget.addTab(self.research_tab, "🔍 Web Research")
        
        main_layout.addWidget(self.tab_widget)
    
    def setup_menu_bar(self):
        """Setup the application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # Add menu actions here
        # file_menu.addAction("&Open...")
        # file_menu.addAction("&Save...")
        # file_menu.addSeparator()
        # file_menu.addAction("E&xit")
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        # Add menu actions here
        # tools_menu.addAction("&Settings...")
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        # Add menu actions here
        # help_menu.addAction("&About...")
    
    def setup_status_bar(self):
        """Setup the application status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Status label
        self.status_label = self.status_bar.addWidget("Ready")
        self.status_label.setStyleSheet("color: #475569; font-size: 12px;")
        
        # Progress bar (hidden by default)
        self.progress_bar = self.status_bar.addWidget("")
        self.progress_bar.hide()
    
    def setup_connections(self):
        """Setup signal connections between components."""
        # Connect tab signals to main window
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # Connect service container signals
        # self.service_container.service_updated.connect(self.on_service_updated)
    
    def setup_status_timer(self):
        """Setup timer for status updates."""
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)  # Update every 5 seconds
    
    def on_tab_changed(self, index: int):
        """Handle tab changes."""
        tab_name = self.tab_widget.tabText(index)
        self.status_label.setText(f"Active: {tab_name}")
        
        # Update tab-specific status
        current_tab = self.tab_widget.currentWidget()
        if hasattr(current_tab, 'update_status'):
            current_tab.update_status()
    
    def update_status(self):
        """Update application status."""
        # Check service availability
        available_services = self.service_container.get_available_services()
        if len(available_services) < 4:  # Expected services: config, obsidian, llm, analysis
            self.status_label.setText("⚠️ Some services unavailable")
            self.status_label.setStyleSheet("color: #dc2626; font-size: 12px;")
        else:
            self.status_label.setText("✅ All services available")
            self.status_label.setStyleSheet("color: #059669; font-size: 12px;")
    
    def show_status_message(self, message: str, timeout: int = 3000):
        """Show a temporary status message."""
        self.status_bar.showMessage(message, timeout)
    
    def reload_services(self):
        """Reload all services (useful after configuration changes)."""
        self.service_container.reload_services()
        self.update_status()
        self.show_status_message("Services reloaded", 2000)
    
    def closeEvent(self, event):
        """Handle application close event."""
        # Cleanup any resources
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()
        
        # Accept the close event
        event.accept()
