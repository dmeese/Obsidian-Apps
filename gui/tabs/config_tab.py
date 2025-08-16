"""
Configuration Tab for ObsidianTools GUI.

This tab handles application configuration and settings.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QFont
from core.services import ServiceContainer


class ConfigTab(QWidget):
    """Configuration tab for application settings."""
    
    def __init__(self, service_container: ServiceContainer):
        super().__init__()
        self.service_container = service_container
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the configuration tab UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Title
        title = QLabel("Configuration")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #1e293b; margin-bottom: 8px;")
        layout.addWidget(title)
        
        # Description
        description = QLabel(
            "Configure application settings, API keys, and security preferences."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #64748b; margin-bottom: 16px;")
        layout.addWidget(description)
        
        # Placeholder
        placeholder = QLabel("Configuration functionality coming soon...")
        placeholder.setStyleSheet("color: #94a3b8; font-style: italic;")
        layout.addWidget(placeholder)
        
        # Add stretch to push everything to the top
        layout.addStretch()
    
    def update_status(self):
        """Update tab-specific status."""
        pass
