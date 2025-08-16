"""
Modern Button Widget for ObsidianTools GUI.

A custom QPushButton with modern styling, hover effects,
and better visual feedback.
"""

from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt


class ModernButton(QPushButton):
    """Modern styled button with hover effects and better visual feedback."""
    
    def __init__(self, text="", primary=False, size="medium"):
        super().__init__(text)
        self.primary = primary
        self.size = size
        self.setup_style()
        self.setup_behavior()
    
    def setup_style(self):
        """Apply modern styling to the button."""
        if self.primary:
            base_color = "#2563eb"  # Blue
            hover_color = "#1d4ed8"
            pressed_color = "#1e40af"
        else:
            base_color = "#6b7280"  # Gray
            hover_color = "#4b5563"
            pressed_color = "#374151"
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {base_color};
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: {self._get_font_size()};
                padding: {self._get_padding()};
                min-height: {self._get_min_height()};
            }}
            QPushButton:hover {{
                background-color: {hover_color};
                transform: translateY(-1px);
            }}
            QPushButton:pressed {{
                background-color: {pressed_color};
                transform: translateY(0px);
            }}
            QPushButton:disabled {{
                background-color: #d1d5db;
                color: #9ca3af;
            }}
        """)
    
    def _get_font_size(self):
        if self.size == "large":
            return "14px"  # Reduced from 15px
        elif self.size == "small":
            return "10px"  # Reduced from 11px
        else:
            return "12px"  # Reduced from 13px
    
    def _get_padding(self):
        if self.size == "large":
            return "10px 16px"  # Reduced from 12px 20px
        elif self.size == "small":
            return "5px 10px"  # Reduced from 6px 12px
        else:
            return "8px 14px"  # Reduced from 10px 16px
    
    def _get_min_height(self):
        if self.size == "large":
            return "40px"  # Reduced from 44px
        elif self.size == "small":
            return "24px"  # Reduced from 28px
        else:
            return "32px"  # Reduced from 36px
    
    def setup_behavior(self):
        """Setup button behavior and effects."""
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
