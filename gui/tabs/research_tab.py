"""
Web Research Tab for ObsidianTools GUI.

This tab handles web research and content enhancement.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QFont
from core.services import ServiceContainer


class ResearchTab(QWidget):
    """Web research tab for content enhancement."""
    
    def __init__(self, service_container: ServiceContainer):
        super().__init__()
        self.service_container = service_container
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the research tab UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Title
        title = QLabel("Web Research")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #1e293b; margin-bottom: 8px;")
        layout.addWidget(title)
        
        # Description
        description = QLabel(
            "Enhance your notes with web research, Wikipedia integration, "
            "and AI-powered content analysis."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #64748b; margin-bottom: 16px;")
        layout.addWidget(description)
        
        # Placeholder
        placeholder = QLabel("Web research functionality coming soon...")
        placeholder.setStyleSheet("color: #94a3b8; font-style: italic;")
        layout.addWidget(placeholder)
        
        # Add stretch to push everything to the top
        layout.addStretch()
    
    def update_status(self):
        """Update tab-specific status."""
        pass
