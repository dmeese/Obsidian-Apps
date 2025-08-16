"""
Modern Input Widgets for ObsidianTools GUI.

Custom input widgets with modern styling, validation,
and better visual feedback.
"""

from PyQt6.QtWidgets import QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox
from PyQt6.QtCore import Qt


class ModernLineEdit(QLineEdit):
    """Modern styled line edit with validation and better visual feedback."""
    
    def __init__(self, placeholder="", initial_text="", validator=None):
        super().__init__()
        self.placeholder = placeholder
        self.validator = validator
        self.setup_style()
        self.setup_validation()
        if initial_text:
            self.setText(initial_text)
    
    def setup_style(self):
        """Apply modern styling to the line edit."""
        self.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e5e7eb;
                border-radius: 6px;
                padding: 6px 10px;  /* Reduced from 8px 12px */
                font-size: 12px;  /* Reduced from 13px */
                background-color: white;
                color: #111827;
            }
            QLineEdit:focus {
                border-color: #2563eb;
                outline: none;
            }
            QLineEdit:disabled {
                background-color: #f9fafb;
                color: #6b7280;
                border-color: #d1d5db;
            }
            QLineEdit[error="true"] {
                border-color: #dc2626;
                background-color: #fef2f2;
            }
        """)
        self.setPlaceholderText(self.placeholder)
    
    def setup_validation(self):
        """Setup validation for the input."""
        if self.validator:
            self.setValidator(self.validator)
        
        # Connect text changed signal for real-time validation
        self.textChanged.connect(self.validate_input)
    
    def validate_input(self):
        """Validate input and update visual state."""
        if self.validator:
            state, _, _ = self.validator.validate(self.text(), 0)
            if state == self.validator.State.Acceptable:
                self.setProperty("error", False)
                self.setStyleSheet(self.styleSheet())
            else:
                self.setProperty("error", True)
                self.setStyleSheet(self.styleSheet())


class ModernSpinBox(QSpinBox):
    """Modern styled spin box with better visual feedback."""
    
    def __init__(self, minimum=0, maximum=100, value=0):
        super().__init__()
        self.setRange(minimum, maximum)
        self.setValue(value)
        self.setup_style()
    
    def setup_style(self):
        """Apply modern styling to the spin box."""
        self.setStyleSheet("""
            QSpinBox {
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                padding: 8px 12px;  /* Reduced from 12px 16px */
                font-size: 13px;  /* Reduced from 14px */
                background-color: white;
                color: #111827;
                min-height: 18px;  /* Reduced from 20px */
            }
            QSpinBox:focus {
                border-color: #2563eb;
                outline: none;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 20px;
                border: none;
                background-color: #f3f4f6;
                border-radius: 4px;
                margin: 2px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #e5e7eb;
            }
            QSpinBox::up-button:pressed, QSpinBox::down-button:pressed {
                background-color: #d1d5db;
            }
        """)


class ModernDoubleSpinBox(QDoubleSpinBox):
    """Modern styled double spin box with better visual feedback."""
    
    def __init__(self, minimum=0.0, maximum=100.0, value=0.0, decimals=2):
        super().__init__()
        self.setRange(minimum, maximum)
        self.setValue(value)
        self.setDecimals(decimals)
        self.setup_style()
    
    def setup_style(self):
        """Apply modern styling to the double spin box."""
        self.setStyleSheet("""
            QDoubleSpinBox {
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                background-color: white;
                color: #111827;
                min-height: 18px;
            }
            QDoubleSpinBox:focus {
                border-color: #2563eb;
                outline: none;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                width: 20px;
                border: none;
                background-color: #f3f4f6;
                border-radius: 4px;
                margin: 2px;
            }
            QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
                background-color: #e5e7eb;
            }
            QDoubleSpinBox::up-button:pressed, QDoubleSpinBox::down-button:pressed {
                background-color: #d1d5db;
            }
        """)


class ModernCheckBox(QCheckBox):
    """Modern styled check box with better visual feedback."""
    
    def __init__(self, text="", checked=False):
        super().__init__(text)
        self.setChecked(checked)
        self.setup_style()
    
    def setup_style(self):
        """Apply modern styling to the check box."""
        self.setStyleSheet("""
            QCheckBox {
                spacing: 8px;
                font-size: 13px;
                color: #111827;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #e5e7eb;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #2563eb;
                border-color: #2563eb;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
            }
            QCheckBox::indicator:checked:hover {
                background-color: #1d4ed8;
                border-color: #1d4ed8;
            }
            QCheckBox::indicator:unchecked:hover {
                border-color: #2563eb;
            }
            QCheckBox:disabled {
                color: #6b7280;
            }
            QCheckBox::indicator:disabled {
                background-color: #f3f4f6;
                border-color: #d1d5db;
            }
        """)
