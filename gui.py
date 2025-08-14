import sys
import os
import logging
import threading
import json
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QLabel, QTextEdit, QLineEdit,
    QSpinBox, QDoubleSpinBox, QCheckBox, QFileDialog, QProgressBar,
    QGroupBox, QFormLayout, QMessageBox, QSplitter, QFrame,
    QScrollArea, QSizePolicy, QGridLayout, QHBoxLayout, QVBoxLayout,
    QComboBox, QRadioButton
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QIcon, QTextCursor, QPalette, QColor, QPixmap
from utils import create_api_session, verify_connection
from analyzer import run_analysis_process
from ingest import run_ingest_process
from config_manager import ConfigManager


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
    
    def __init__(self, minimum=0.0, maximum=1.0, value=0.0, decimals=3):
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
                padding: 8px 12px;  /* Reduced from 12px 16px */
                font-size: 13px;  /* Reduced from 14px */
                background-color: white;
                color: #111827;
                min-height: 18px;  /* Reduced from 20px */
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
    
    def __init__(self, text=""):
        super().__init__(text)
        self.setup_style()
    
    def setup_style(self):
        """Apply modern styling to the check box."""
        self.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
                color: #111827;
                spacing: 12px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #e5e7eb;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #2563eb;
                border-color: #2563eb;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
            }
            QCheckBox::indicator:hover {
                border-color: #2563eb;
            }
        """)


class ModernGroupBox(QGroupBox):
    """Modern styled group box with better visual feedback."""
    
    def __init__(self, title=""):
        super().__init__(title)
        self.setup_style()
    
    def setup_style(self):
        """Apply modern styling to the group box."""
        self.setStyleSheet("""
            QGroupBox {
                font-weight: 600;
                font-size: 14px;  /* Reduced from 16px */
                color: #111827;
                border: 2px solid #e5e7eb;
                border-radius: 10px;  /* Reduced from 12px */
                margin-top: 12px;  /* Reduced from 16px */
                padding-top: 12px;  /* Reduced from 16px */
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;  /* Reduced from 16px */
                padding: 0 6px 0 6px;  /* Reduced from 8px */
                background-color: #ffffff;
            }
        """)


class AnalysisWorker(QThread):
    """Worker thread for running vault analysis."""
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, session, api_url, timeout, output_file, hub_threshold, 
                 link_density_threshold, min_word_count):
        super().__init__()
        self.session = session
        self.api_url = api_url
        self.timeout = timeout
        self.output_file = output_file
        self.hub_threshold = hub_threshold
        self.link_density_threshold = link_density_threshold
        self.min_word_count = min_word_count

    def run(self):
        try:
            # Redirect logging to our progress signal
            class LogHandler(logging.Handler):
                def __init__(self, signal):
                    super().__init__()
                    self.signal = signal

                def emit(self, record):
                    msg = self.format(record)
                    self.signal.emit(msg)

            # Set up logging to capture progress
            handler = LogHandler(self.progress)
            handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
            logging.getLogger().addHandler(handler)
            logging.getLogger().setLevel(logging.INFO)

            # Run the analysis
            run_analysis_process(
                self.session, self.api_url, self.timeout, self.output_file,
                self.hub_threshold, self.link_density_threshold, self.min_word_count
            )

            # Read the results
            with open(self.output_file, 'r', encoding='utf-8') as f:
                content = f.read()

            result = {
                'output_file': self.output_file,
                'content': content
            }
            self.finished.emit(result)

        except Exception as e:
            self.error.emit(str(e))
        finally:
            # Clean up logging handler
            logging.getLogger().removeHandler(handler)


class IngestWorker(QThread):
    """Worker thread for running document ingestion."""
    progress = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, ingest_folder, notes_folder, session, api_url, 
                 gemini_api_key, timeout, delete_after_ingest, model_name):
        super().__init__()
        self.ingest_folder = ingest_folder
        self.notes_folder = notes_folder
        self.session = session
        self.api_url = api_url
        self.gemini_api_key = gemini_api_key
        self.timeout = timeout
        self.delete_after_ingest = delete_after_ingest
        self.model_name = model_name

    def run(self):
        try:
            # Redirect logging to our progress signal
            class LogHandler(logging.Handler):
                def __init__(self, signal):
                    super().__init__()
                    self.signal = signal

                def emit(self, record):
                    msg = self.format(record)
                    self.signal.emit(msg)

            # Set up logging to capture progress
            handler = LogHandler(self.progress)
            handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
            logging.getLogger().addHandler(handler)
            logging.getLogger().setLevel(logging.INFO)

            # Run the ingestion
            run_ingest_process(
                self.ingest_folder, self.notes_folder, self.session,
                self.api_url, self.gemini_api_key, self.timeout,
                self.delete_after_ingest, self.model_name
            )

            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))
        finally:
            # Clean up logging handler
            logging.getLogger().removeHandler(handler)


class ObsidianToolsGUI(QMainWindow):
    """Main GUI window for Obsidian Tools with modern design."""
    
    def __init__(self):
        super().__init__()
        self.analysis_worker = None
        self.ingest_worker = None
        self.session = None
        self.api_url = None
        self.gemini_api_key = None
        
        # Initialize configuration manager
        self.config_manager = ConfigManager()
        self.master_password = None
        
        self.init_ui()
        self.load_configuration()
        self.setup_responsive_design()
        
        # Connect to Obsidian after UI is fully initialized
        # Use QTimer to ensure this runs after the UI is displayed
        QTimer.singleShot(100, self.connect_to_obsidian)

    def init_ui(self):
        """Initialize the user interface with modern design."""
        self.setWindowTitle("Obsidian Tools")
        self.setGeometry(100, 100, 1000, 1250)  # Increased height to 1250 pixels
        self.setMinimumSize(800, 1100)  # Increased minimum height accordingly
        
        # Set up the central widget with scroll area for responsiveness
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout - reduced spacing and margins
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(12)  # Reduced from 16
        main_layout.setContentsMargins(16, 16, 16, 16)  # Reduced from 20
        
        # Header section
        self.create_header(main_layout)
        
        # Status section
        self.create_status_section(main_layout)
        
        # Tab widget for different functions
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f3f4f6;
                color: #6b7280;
                padding: 8px 16px;  /* Reduced from 10px 20px */
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: 600;
                font-size: 13px;  /* Reduced from 14px */
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #111827;
                border-bottom: 2px solid #2563eb;
            }
            QTabBar::tab:hover:!selected {
                background-color: #e5e7eb;
                color: #374151;
            }
        """)
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_analyze_tab()
        self.create_ingest_tab()
        self.create_web_research_tab()  # New web research tab
        self.create_config_tab()
        
        # Progress area
        self.create_progress_section(main_layout)

    def create_header(self, layout):
        """Create the header section with title and description."""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border-radius: 12px;
                padding: 12px;  /* Reduced from 16px */
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setSpacing(12)  # Reduced from 16
        
        # Title
        title_label = QLabel("Obsidian Tools")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;  /* Reduced from 20px */
                font-weight: 700;
                color: #111827;
                margin-bottom: 2px;  /* Reduced from 4px */
            }
        """)
        
        # Subtitle
        subtitle_label = QLabel("Professional vault analysis and document ingestion")
        subtitle_label.setStyleSheet("""
            QLabel {
                font-size: 12px;  /* Reduced from 13px */
                color: #6b7280;
                font-weight: 500;
            }
        """)
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        
        layout.addWidget(header_frame)

    def create_status_section(self, layout):
        """Create the status section with connection information."""
        self.status_frame = QFrame()
        self.status_frame.setStyleSheet("""
            QFrame {
                background-color: #fef3c7;
                border: 2px solid #f59e0b;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        status_layout = QHBoxLayout(self.status_frame)
        status_layout.setContentsMargins(12, 12, 12, 12)
        
        # Status icon (placeholder for now)
        status_icon = QLabel("🔄")
        status_icon.setStyleSheet("font-size: 24px; margin-right: 12px;")
        status_layout.addWidget(status_icon)
        
        # Status text
        self.status_label = QLabel("Connecting to Obsidian...")
        self.status_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Medium))  # Reduced from 14
        self.status_label.setStyleSheet("color: #92400e; margin: 0;")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        # Add refresh button
        self.refresh_status_button = ModernButton("🔄 Refresh Status", size="small")
        self.refresh_status_button.clicked.connect(self.refresh_connection_status)
        self.refresh_status_button.setToolTip("Refresh connection status and retry connection")
        status_layout.addWidget(self.refresh_status_button)
        
        layout.addWidget(self.status_frame)

    def create_progress_section(self, layout):
        """Create the progress section with progress bar and logging."""
        progress_group = ModernGroupBox("Progress & Logs")
        progress_layout = QVBoxLayout(progress_group)  # Changed to vertical layout
        progress_layout.setSpacing(16)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                text-align: center;
                font-weight: 600;
                color: #111827;
                background-color: #f9fafb;
            }
            QProgressBar::chunk {
                background-color: #2563eb;
                border-radius: 6px;
                margin: 2px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        # Status info
        status_info = QLabel("Monitor operation progress and view detailed logs below.\n\nProgress bar shows current operation status, while the log displays real-time information.")
        status_info.setWordWrap(True)
        status_info.setStyleSheet("color: #6b7280; font-size: 13px; line-height: 1.5;")  # Increased font size
        progress_layout.addWidget(status_info)
        
        # Log output - full width
        log_label = QLabel("Operation Log")
        log_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Medium))  # Increased font size
        log_label.setStyleSheet("color: #374151; margin: 0;")
        progress_layout.addWidget(log_label)
        
        self.log_output = QTextEdit()
        self.log_output.setMinimumHeight(200)  # Changed from maximum to minimum height
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("""
            QTextEdit {
                background-color: #1f2937;
                color: #f9fafb;
                border: 2px solid #374151;
                border-radius: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 13px;  /* Increased font size */
                padding: 16px;  /* Increased padding */
            }
        """)
        progress_layout.addWidget(self.log_output)
        
        layout.addWidget(progress_group)

    def create_analyze_tab(self):
        """Create the vault analysis tab with modern design."""
        analyze_widget = QWidget()
        layout = QVBoxLayout(analyze_widget)  # Changed back to vertical layout for better proportions
        layout.setSpacing(16)  # Increased spacing for better breathing room
        layout.setContentsMargins(20, 20, 20, 20)  # Increased margins
        
        # Top section: Parameters and Actions side by side
        top_section = QHBoxLayout()
        top_section.setSpacing(12)  # Reduced spacing between groups for more compact layout
        
        # Analysis parameters - give it more width
        params_group = ModernGroupBox("Analysis Parameters")
        params_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        params_layout = QFormLayout(params_group)
        params_layout.setSpacing(6)  # Reduced spacing for more compact layout
        params_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Make input fields wider by setting minimum width
        self.output_file_edit = ModernLineEdit(placeholder="Enter output filename", initial_text="recommendations.md")
        self.output_file_edit.setMinimumWidth(250)  # Set minimum width
        params_layout.addRow("Output File:", self.output_file_edit)
        
        self.hub_threshold_spin = ModernSpinBox(1, 100, 10)
        self.hub_threshold_spin.setMinimumWidth(120)  # Set minimum width
        params_layout.addRow("Hub Threshold:", self.hub_threshold_spin)
        
        self.link_density_spin = ModernDoubleSpinBox(0.001, 1.0, 0.02, 3)
        self.link_density_spin.setMinimumWidth(120)  # Set minimum width
        params_layout.addRow("Link Density Threshold:", self.link_density_spin)
        
        self.min_word_count_spin = ModernSpinBox(10, 1000, 50)
        self.min_word_count_spin.setMinimumWidth(120)  # Set minimum width
        params_layout.addRow("Min Word Count:", self.min_word_count_spin)
        
        top_section.addWidget(params_group, 2)  # Give parameters more space (2 parts)
        
        # Actions group - more compact
        action_group = ModernGroupBox("Actions")
        action_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        action_layout = QVBoxLayout(action_group)
        action_layout.setSpacing(8)  # Reduced spacing for more compact layout
        
        # Analysis button
        self.analyze_button = ModernButton("🔍 Analyze Vault", primary=True, size="large")
        self.analyze_button.clicked.connect(self.run_analysis)
        action_layout.addWidget(self.analyze_button)
        
        # Status info
        status_info = QLabel("Click the button above to start vault analysis.\n\nThis will analyze your Obsidian vault and generate recommendations for improving note structure and linking.")
        status_info.setWordWrap(True)
        status_info.setStyleSheet("color: #6b7280; font-size: 12px; line-height: 1.4;")  # Increased font size
        action_layout.addWidget(status_info)
        
        action_layout.addStretch()
        top_section.addWidget(action_group, 1)  # Give actions less space (1 part)
        
        layout.addLayout(top_section)
        
        # Results area - full width below
        results_group = ModernGroupBox("Analysis Results")
        results_layout = QVBoxLayout(results_group)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMinimumHeight(300)  # Set minimum height
        self.results_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;  /* Increased font size */
                line-height: 1.5;  /* Increased line height */
                padding: 16px;  /* Increased padding */
            }
        """)
        results_layout.addWidget(self.results_text)
        
        layout.addWidget(results_group)
        
        self.tab_widget.addTab(analyze_widget, "🔍 Analyze Vault")

    def create_ingest_tab(self):
        """Create the document ingestion tab with modern design."""
        ingest_widget = QWidget()
        layout = QVBoxLayout(ingest_widget)
        layout.setSpacing(12)  # Reduced from 16
        layout.setContentsMargins(16, 16, 16, 16)  # Reduced from 20
        
        # Top section: Folder configuration and options side by side
        top_row = QHBoxLayout()
        top_row.setSpacing(20)  # Increased spacing
        
        # Left side: Folder configuration - give it more width
        folders_group = ModernGroupBox("Folder Configuration")
        folders_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        folders_layout = QFormLayout(folders_group)
        folders_layout.setSpacing(16)  # Increased spacing
        folders_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Ingest folder selection
        ingest_folder_layout = QHBoxLayout()
        ingest_folder_layout.setSpacing(12)  # Increased spacing
        
        self.ingest_folder_edit = ModernLineEdit(placeholder="Select ingest folder", initial_text="ingest")
        self.ingest_folder_edit.setMinimumWidth(300)  # Set minimum width
        ingest_folder_layout.addWidget(self.ingest_folder_edit)
        
        self.ingest_folder_button = ModernButton("📁 Browse...", size="small")
        self.ingest_folder_button.clicked.connect(self.select_ingest_folder)
        ingest_folder_layout.addWidget(self.ingest_folder_button)
        folders_layout.addRow("Ingest Folder:", ingest_folder_layout)
        
        # Notes folder selection
        notes_folder_layout = QHBoxLayout()
        notes_folder_layout.setSpacing(12)  # Increased spacing
        
        self.notes_folder_edit = ModernLineEdit(placeholder="Select notes folder", initial_text="GeneratedNotes")
        self.notes_folder_edit.setMinimumWidth(300)  # Set minimum width
        notes_folder_layout.addWidget(self.notes_folder_edit)
        
        self.notes_folder_button = ModernButton("📁 Browse...", size="small")
        self.notes_folder_button.clicked.connect(self.select_notes_folder)
        notes_folder_layout.addWidget(self.notes_folder_button)
        folders_layout.addRow("Notes Folder:", notes_folder_layout)
        
        top_row.addWidget(folders_group, 2)  # Give folders more space (2 parts)
        
        # Right side: Options and actions - more compact
        right_group = ModernGroupBox("Options & Actions")
        right_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        right_layout = QVBoxLayout(right_group)
        right_layout.setSpacing(16)  # Increased spacing
        
        # Model selection
        model_label = QLabel("🤖 LLM Model:")
        model_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Medium))
        model_label.setStyleSheet("color: #374151; margin: 0;")
        right_layout.addWidget(model_label)
        
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite"
        ])
        self.model_combo.setCurrentText("gemini-2.5-flash")  # Default selection
        self.model_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                padding: 6px 10px;  /* Reduced from 8px 12px */
                font-size: 13px;  /* Reduced from 14px */
                background-color: white;
                color: #111827;
                min-height: 18px;  /* Reduced from 20px */
            }
            QComboBox:focus {
                border-color: #2563eb;
                outline: none;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTMgNEw2IDdNOSA0IiBzdHJva2U9IiM2YjcyODAiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
                width: 12px;
                height: 12px;
            }
        """)
        right_layout.addWidget(self.model_combo)
        
        # Ingestion options
        self.delete_files_checkbox = ModernCheckBox("🗑️ Delete source files after successful ingestion")
        self.delete_files_checkbox.setChecked(True)
        self.delete_files_checkbox.setToolTip("When checked, successfully processed files will be removed from the ingest folder")
        right_layout.addWidget(self.delete_files_checkbox)
        
        # Ingestion button
        self.ingest_button = ModernButton("📥 Start Ingestion", primary=True, size="large")
        self.ingest_button.clicked.connect(self.run_ingestion)
        right_layout.addWidget(self.ingest_button)
        
        # Add some spacing and status info
        status_info = QLabel("Configure your folders above and click the button to start document ingestion.\n\nThis will process documents in your ingest folder and create structured notes in Obsidian.")
        status_info.setWordWrap(True)
        status_info.setStyleSheet("color: #6b7280; font-size: 12px; line-height: 1.4;")  # Reduced from 13px
        right_layout.addWidget(status_info)
        
        right_layout.addStretch()
        top_row.addWidget(right_group, 1)  # Give it equal space
        
        layout.addLayout(top_row)
        
        # Bottom row: File list and refresh controls
        files_group = ModernGroupBox("Files in Ingest Folder")
        files_layout = QVBoxLayout(files_group)
        files_layout.setSpacing(12)  # Reduced from default
        
        # File count and refresh button row
        file_header_layout = QHBoxLayout()
        file_count_label = QLabel("0 files found")
        file_count_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Medium))
        file_count_label.setStyleSheet("color: #374151;")
        file_header_layout.addWidget(file_count_label)
        
        file_header_layout.addStretch()
        
        refresh_button = ModernButton("🔄 Refresh", size="small")
        refresh_button.clicked.connect(self.refresh_file_list)
        file_header_layout.addWidget(refresh_button)
        
        files_layout.addLayout(file_header_layout)
        
        self.files_text = QTextEdit()
        self.files_text.setReadOnly(True)
        self.files_text.setMaximumHeight(200)
        self.files_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                padding: 16px;
            }
        """)
        files_layout.addWidget(self.files_text)
        
        layout.addWidget(files_group)
        
        self.tab_widget.addTab(ingest_widget, "📥 Ingest Documents")

    def create_web_research_tab(self):
        """Create the web research tab with modern design."""
        research_widget = QWidget()
        layout = QVBoxLayout(research_widget)
        layout.setSpacing(12)  # Reduced spacing
        layout.setContentsMargins(16, 16, 16, 16)  # Reduced margins
        
        # Top section: Folder targeting and research options
        top_row = QHBoxLayout()
        top_row.setSpacing(20)  # Increased spacing
        
        # Left side: Folder targeting - give it more width
        targeting_group = ModernGroupBox("📁 Folder Targeting")
        targeting_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        targeting_layout = QFormLayout(targeting_group)
        targeting_layout.setSpacing(12)  # Increased spacing
        targeting_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Vault folder selection
        vault_folder_layout = QHBoxLayout()
        vault_folder_layout.setSpacing(12)  # Increased spacing
        
        self.vault_folder_edit = ModernLineEdit(placeholder="Select vault folder to research", initial_text="")
        self.vault_folder_edit.setMinimumWidth(300)  # Set minimum width
        vault_folder_layout.addWidget(self.vault_folder_edit)
        
        self.vault_folder_button = ModernButton("📁 Browse...", size="small")
        self.vault_folder_button.clicked.connect(self.select_vault_folder)
        vault_folder_layout.addWidget(self.vault_folder_button)
        targeting_layout.addRow("Vault Folder:", vault_folder_layout)
        
        # Recursive processing option
        self.recursive_checkbox = ModernCheckBox("📂 Process subfolders recursively")
        self.recursive_checkbox.setChecked(True)
        targeting_layout.addRow("", self.recursive_checkbox)
        
        top_row.addWidget(targeting_group, 2)  # Give targeting more space (2 parts)
        
        # Right side: Research options - more compact
        options_group = ModernGroupBox("🔍 Research Options")
        options_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        options_layout = QVBoxLayout(options_group)
        options_layout.setSpacing(12)  # Increased spacing
        
        # Wikipedia research options
        self.wikipedia_checkbox = ModernCheckBox("🌐 Enable Wikipedia research")
        self.wikipedia_checkbox.setChecked(True)
        options_layout.addWidget(self.wikipedia_checkbox)
        
        # Max articles per note
        max_articles_layout = QHBoxLayout()
        max_articles_layout.setSpacing(8)
        
        max_articles_label = QLabel("Max articles per note:")
        max_articles_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
        max_articles_label.setStyleSheet("color: #374151; margin: 0;")
        max_articles_layout.addWidget(max_articles_label)
        
        self.max_articles_spin = ModernSpinBox(1, 10, 3)
        max_articles_layout.addWidget(self.max_articles_spin)
        
        options_layout.addLayout(max_articles_layout)
        
        # Backup original notes
        self.backup_original_checkbox = ModernCheckBox("💾 Backup original notes before enhancement")
        self.backup_original_checkbox.setChecked(True)
        options_layout.addWidget(self.backup_original_checkbox)
        
        options_layout.addStretch()
        top_row.addWidget(options_group, 1)
        
        layout.addLayout(top_row)
        
        # Research actions
        actions_group = ModernGroupBox("🚀 Research Actions")
        actions_layout = QVBoxLayout(actions_group)
        actions_layout.setSpacing(12)
        
        # Research button
        self.research_button = ModernButton("🔍 Start Research", primary=True, size="large")
        self.research_button.clicked.connect(self.start_web_research)
        actions_layout.addWidget(self.research_button)
        
        # Status info
        research_info = QLabel("Select a folder in your Obsidian vault to research and enhance notes with Wikipedia content.\n\nThis will add research context, citations, and enhanced wikilinks to your notes.")
        research_info.setWordWrap(True)
        research_info.setStyleSheet("color: #6b7280; font-size: 11px; line-height: 1.3;")
        actions_layout.addWidget(research_info)
        
        actions_layout.addStretch()
        layout.addWidget(actions_group)
        
        # Research progress and results
        results_group = ModernGroupBox("📊 Research Progress & Results")
        results_layout = QVBoxLayout(results_group)
        
        # Progress bar for research
        self.research_progress_bar = QProgressBar()
        self.research_progress_bar.setVisible(False)
        self.research_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e5e7eb;
                border-radius: 6px;
                text-align: center;
                font-weight: 600;
                color: #111827;
                background-color: #f9fafb;
            }
            QProgressBar::chunk {
                background-color: #10b981;
                border-radius: 4px;
                margin: 2px;
            }
        """)
        results_layout.addWidget(self.research_progress_bar)
        
        # Research results text
        self.research_results_text = QTextEdit()
        self.research_results_text.setReadOnly(True)
        self.research_results_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 11px;
                line-height: 1.3;
                padding: 12px;
            }
        """)
        results_layout.addWidget(self.research_results_text)
        
        layout.addWidget(results_group)
        
        self.tab_widget.addTab(research_widget, "🌐 Web Research")

    def create_config_tab(self):
        """Create the configuration tab with modern design and scroll capability."""
        config_widget = QWidget()
        
        # Create scroll area for the configuration content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #f3f4f6;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #d1d5db;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #9ca3af;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # Create the scrollable content widget
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(16)  # Reduced from 24
        layout.setContentsMargins(20, 20, 20, 20)  # Reduced from 32
        
        # Security method selection
        security_group = ModernGroupBox("Security Method")
        security_layout = QVBoxLayout(security_group)
        security_layout.setSpacing(12)  # Reduced from 16
        
        # Security method radio buttons
        self.security_local_radio = QRadioButton("🔒 Local Encrypted Storage")
        self.security_local_radio.setChecked(True)
        self.security_local_radio.setStyleSheet("""
            QRadioButton {
                font-size: 13px;  /* Reduced from 14px */
                color: #111827;
                spacing: 8px;  /* Reduced from 12px */
            }
        """)
        security_layout.addWidget(self.security_local_radio)
        
        self.security_1password_radio = QRadioButton("🔑 1Password Integration")
        self.security_1password_radio.setStyleSheet("""
            QRadioButton {
                font-size: 13px;  /* Reduced from 14px */
                color: #111827;
                spacing: 8px;  /* Reduced from 12px */
            }
        """)
        security_layout.addWidget(self.security_1password_radio)
        
        # Connect radio buttons to be mutually exclusive
        self.security_local_radio.toggled.connect(lambda checked: self.security_1password_radio.setChecked(not checked) if checked else None)
        self.security_1password_radio.toggled.connect(lambda checked: self.security_local_radio.setChecked(not checked) if checked else None)
        
        # Master password input (for local encryption)
        self.master_password_layout = QHBoxLayout()
        self.master_password_layout.setSpacing(12)  # Reduced from default
        self.master_password_edit = ModernLineEdit(placeholder="Enter master password for encryption")
        self.master_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.master_password_layout.addWidget(self.master_password_edit)
        
        self.confirm_password_edit = ModernLineEdit(placeholder="Confirm master password")
        self.confirm_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.master_password_layout.addWidget(self.confirm_password_edit)
        
        security_layout.addLayout(self.master_password_layout)
        
        layout.addWidget(security_group)
        
        # Configuration status - moved to top
        status_group = ModernGroupBox("Configuration Status")
        status_layout = QVBoxLayout(status_group)
        
        self.config_status_label = QLabel("Configuration not loaded")
        self.config_status_label.setStyleSheet("color: #6b7280; font-size: 12px;")  # Reduced from 13px
        status_layout.addWidget(self.config_status_label)
        
        layout.addWidget(status_group)
        
        # Action buttons - moved to top
        actions_group = ModernGroupBox("Configuration Actions")
        actions_layout = QHBoxLayout(actions_group)
        actions_layout.setSpacing(12)  # Reduced from 16
        
        # Test connection button
        self.test_connection_button = ModernButton("🔗 Test Connection", size="medium")
        self.test_connection_button.clicked.connect(self.test_connection)
        actions_layout.addWidget(self.test_connection_button)
        
        # Save configuration button
        self.save_config_button = ModernButton("💾 Save Configuration", primary=True, size="medium")
        self.save_config_button.clicked.connect(self.save_configuration)
        actions_layout.addWidget(self.save_config_button)
        
        # Load configuration button
        self.load_config_button = ModernButton("📂 Load Configuration", size="medium")
        self.load_config_button.clicked.connect(self.load_configuration)
        actions_layout.addWidget(self.load_config_button)
        
        # Export configuration button
        self.export_config_button = ModernButton("📤 Export Config", size="medium")
        self.export_config_button.clicked.connect(self.export_configuration)
        actions_layout.addWidget(self.export_config_button)
        
        # Import configuration button
        self.import_config_button = ModernButton("📥 Import Config", size="medium")
        self.import_config_button.clicked.connect(self.import_configuration)
        actions_layout.addWidget(self.import_config_button)
        
        actions_layout.addStretch()
        layout.addWidget(actions_group)
        
        # Connection settings
        connection_group = ModernGroupBox("Connection Settings")
        connection_layout = QFormLayout(connection_group)
        connection_layout.setSpacing(12)  # Reduced from 16
        connection_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Obsidian API URL
        self.obsidian_url_edit = ModernLineEdit(placeholder="http://localhost:27123", initial_text="http://localhost:27123")
        connection_layout.addRow("Obsidian API URL:", self.obsidian_url_edit)
        
        # Timeout settings
        self.obsidian_timeout_spin = ModernSpinBox(5, 300, 30)
        connection_layout.addRow("API Timeout (seconds):", self.obsidian_timeout_spin)
        
        # Default notes folder
        self.default_notes_folder_edit = ModernLineEdit(placeholder="GeneratedNotes", initial_text="GeneratedNotes")
        connection_layout.addRow("Default Notes Folder:", self.default_notes_folder_edit)
        
        layout.addWidget(connection_group)
        
        # API Keys section
        api_keys_group = ModernGroupBox("API Keys")
        api_keys_layout = QVBoxLayout(api_keys_group)
        api_keys_layout.setSpacing(12)  # Reduced from 16
        
        # Local API keys (for local encrypted storage)
        self.local_keys_layout = QFormLayout()
        self.local_keys_layout.setSpacing(12)  # Reduced from 16
        self.local_keys_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.obsidian_api_key_edit = ModernLineEdit(placeholder="Enter Obsidian API key")
        self.obsidian_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.local_keys_layout.addRow("Obsidian API Key:", self.obsidian_api_key_edit)
        
        self.gemini_api_key_edit = ModernLineEdit(placeholder="Enter Gemini API key")
        self.gemini_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.local_keys_layout.addRow("Gemini API Key:", self.gemini_api_key_edit)
        
        api_keys_layout.addLayout(self.local_keys_layout)
        
        # 1Password references (for 1Password integration)
        self.onepassword_layout = QFormLayout()
        self.onepassword_layout.setSpacing(12)  # Reduced from 16
        self.onepassword_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.obsidian_1p_ref_edit = ModernLineEdit(placeholder="op://vault/item/field")
        self.obsidian_1p_ref_edit.textChanged.connect(self.strip_quotes_from_1p_ref)
        self.obsidian_1p_ref_edit.setToolTip("1Password reference (e.g., op://vault/item/field)\nQuotes are automatically stripped if present.")
        self.onepassword_layout.addRow("Obsidian API Key Ref:", self.obsidian_1p_ref_edit)
        
        self.gemini_1p_ref_edit = ModernLineEdit(placeholder="op://vault/item/field")
        self.gemini_1p_ref_edit.textChanged.connect(self.strip_quotes_from_1p_ref)
        self.gemini_1p_ref_edit.setToolTip("1Password reference (e.g., op://vault/item/field)\nQuotes are automatically stripped if present.")
        self.onepassword_layout.addRow("Gemini API Key Ref:", self.gemini_1p_ref_edit)
        
        api_keys_layout.addLayout(self.onepassword_layout)
        
        layout.addWidget(api_keys_group)
        
        # Ingest settings
        ingest_config_group = ModernGroupBox("Ingest Settings")
        ingest_config_layout = QFormLayout(ingest_config_group)
        ingest_config_layout.setSpacing(12)  # Reduced from 16
        ingest_config_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Default ingest folder
        self.default_ingest_folder_edit = ModernLineEdit(placeholder="ingest", initial_text="ingest")
        ingest_config_layout.addRow("Default Ingest Folder:", self.default_ingest_folder_edit)
        
        # Default delete after ingest
        self.default_delete_after_ingest_checkbox = ModernCheckBox("Delete source files after successful ingestion")
        self.default_delete_after_ingest_checkbox.setChecked(True)
        ingest_config_layout.addRow("", self.default_delete_after_ingest_checkbox)
        
        # Default Gemini model
        self.default_gemini_model_combo = QComboBox()
        self.default_gemini_model_combo.addItems([
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite"
        ])
        self.default_gemini_model_combo.setCurrentText("gemini-2.5-flash")
        self.default_gemini_model_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                padding: 6px 10px;  /* Reduced from 8px 12px */
                font-size: 13px;  /* Reduced from 14px */
                background-color: white;
                color: #111827;
                min-height: 18px;  /* Reduced from 20px */
            }
            QComboBox:focus {
                border-color: #2563eb;
                outline: none;
            }
        """)
        ingest_config_layout.addRow("Default Gemini Model:", self.default_gemini_model_combo)
        
        layout.addWidget(ingest_config_group)
        
        # Set the content widget as the scroll area's widget
        scroll_area.setWidget(content_widget)
        
        # Add the scroll area to the main config widget
        config_layout = QVBoxLayout(config_widget)
        config_layout.setContentsMargins(0, 0, 0, 0)
        config_layout.addWidget(scroll_area)
        
        self.tab_widget.addTab(config_widget, "⚙️ Configuration")

    def setup_responsive_design(self):
        """Setup responsive design for different window sizes."""
        # Set size policies for better responsiveness
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Connect resize event for dynamic adjustments
        self.resizeEvent = self.on_resize

    def on_resize(self, event):
        """Handle window resize events for responsive design."""
        # Adjust font sizes based on window size
        width = event.size().width()
        if width < 1200:
            # Smaller fonts for compact view
            self.setStyleSheet("""
                QLabel { font-size: 12px; }
                QGroupBox { font-size: 14px; }
                QPushButton { font-size: 12px; }
            """)
        else:
            # Normal fonts for larger view
            self.setStyleSheet("")
        
        super().resizeEvent(event)

    def connect_to_obsidian(self):
        """Connect to Obsidian and load configuration."""
        try:
            # Get configuration from config manager
            api_url, timeout, default_notes_folder = self.config_manager.get_obsidian_config()
            default_model, gemini_timeout = self.config_manager.get_gemini_config()
            default_ingest_folder, _, default_delete_after = self.config_manager.get_ingest_config()
            
            # Get API keys based on security method
            config = self.config_manager.load_config()
            security_method = config.get("security", {}).get("method", "local_encrypted")
            
            if security_method == "1password":
                # For 1Password, we need to check if references exist and optionally fetch actual keys
                try:
                    # Read references from the GUI fields (which should already be populated)
                    obsidian_api_key_ref = self.obsidian_1p_ref_edit.text().strip()
                    gemini_api_key_ref = self.gemini_1p_ref_edit.text().strip()
                    
                    if not obsidian_api_key_ref or not gemini_api_key_ref:
                        self.update_status("⚠️ 1Password mode: API key references not configured", "warning")
                        self.log_message("Configuration warning: 1Password references not found")
                        # Don't return - continue with setup but mark as not fully connected
                        self.api_url = api_url
                        self.session = None
                        self.gemini_api_key = None
                        
                        # Set default values in ingest tab
                        self.ingest_folder_edit.setText(default_ingest_folder)
                        self.notes_folder_edit.setText(default_notes_folder)
                        self.delete_files_checkbox.setChecked(default_delete_after)
                        self.model_combo.setCurrentText(default_model)
                        
                        # Refresh file list
                        self.refresh_file_list()
                        return
                    
                    # Try to fetch actual keys from 1Password, but don't fail if not authenticated
                    try:
                        obsidian_api_key = self.config_manager._fetch_1password_secret(obsidian_api_key_ref)
                        self.gemini_api_key = self.config_manager._fetch_1password_secret(gemini_api_key_ref)
                        
                        # If we got here, we successfully fetched the keys
                        self.api_url = api_url
                        self.session = create_api_session(obsidian_api_key)
                        
                        # Verify connection
                        verify_connection(self.session, self.api_url, timeout)
                        
                        # Update UI
                        self.update_status("✅ Connected to Obsidian", "success")
                        
                        # Update configuration status to show successful connection
                        if hasattr(self, 'config_status_label'):
                            self.config_status_label.setText("✅ Connected to Obsidian successfully")
                            self.config_status_label.setStyleSheet("color: #10b981; font-size: 13px;")
                        
                        # Set default values in ingest tab
                        self.ingest_folder_edit.setText(default_ingest_folder)
                        self.notes_folder_edit.setText(default_notes_folder)
                        self.delete_files_checkbox.setChecked(default_delete_after)
                        self.model_combo.setCurrentText(default_model)
                        
                        # Refresh file list
                        self.refresh_file_list()
                        return
                        
                    except Exception as e:
                        # 1Password might not be logged in - show warning instead of error
                        if "not signed in" in str(e).lower() or "authentication" in str(e).lower():
                            self.update_status("⚠️ 1Password not authenticated - please sign in via CLI", "warning")
                            self.log_message(f"1Password authentication required: {str(e)}")
                        else:
                            self.update_status(f"⚠️ 1Password error: {str(e)}", "warning")
                            self.log_message(f"1Password error: {str(e)}")
                        
                        # Update configuration status
                        if hasattr(self, 'config_status_label'):
                            self.config_status_label.setText("⚠️ 1Password authentication required")
                            self.config_status_label.setStyleSheet("color: #f59e0b; font-size: 12px;")
                        
                        # Continue with setup but mark as not fully connected
                        self.api_url = api_url
                        self.session = None
                        self.gemini_api_key = None
                        
                        # Set default values in ingest tab
                        self.ingest_folder_edit.setText(default_ingest_folder)
                        self.notes_folder_edit.setText(default_notes_folder)
                        self.delete_files_checkbox.setChecked(default_delete_after)
                        self.model_combo.setCurrentText(default_model)
                        
                        # Refresh file list
                        self.refresh_file_list()
                        return
                    
                except Exception as e:
                    # General error loading secrets - show warning
                    self.update_status(f"⚠️ Configuration warning: {str(e)}", "warning")
                    self.log_message(f"Configuration warning: {str(e)}")
                    
                    # Update configuration status
                    if hasattr(self, 'config_status_label'):
                        self.config_status_label.setText(f"⚠️ Configuration warning: {str(e)}")
                        self.config_status_label.setStyleSheet("color: #f59e0b; font-size: 12px;")
                    
                    # Continue with setup but mark as not fully connected
                    self.api_url = api_url
                    self.session = None
                    self.gemini_api_key = None
                    
                    # Set default values in ingest tab
                    self.ingest_folder_edit.setText(default_ingest_folder)
                    self.notes_folder_edit.setText(default_notes_folder)
                    self.delete_files_checkbox.setChecked(default_delete_after)
                    self.model_combo.setCurrentText(default_model)
                    
                    # Refresh file list
                    self.refresh_file_list()
                    return
            else:
                # For local encrypted storage
                try:
                    obsidian_api_key, self.gemini_api_key = self.config_manager.get_api_keys(self.master_password)
                except ValueError as e:
                    self.update_status(f"❌ Configuration incomplete: {str(e)}", "error")
                    self.log_message(f"Configuration error: {str(e)}")
                    return
            
            # Store API URL
            self.api_url = api_url
            
            # Create API session
            self.session = create_api_session(obsidian_api_key)
            
            # Verify connection
            verify_connection(self.session, self.api_url, timeout)
            
            # Update UI
            self.update_status("✅ Connected to Obsidian", "success")
            
            # Update configuration status to show successful connection
            if hasattr(self, 'config_status_label'):
                self.config_status_label.setText("✅ Connected to Obsidian successfully")
                self.config_status_label.setStyleSheet("color: #10b981; font-size: 13px;")
            
            # Set default values in ingest tab
            self.ingest_folder_edit.setText(default_ingest_folder)
            self.notes_folder_edit.setText(default_notes_folder)
            self.delete_files_checkbox.setChecked(default_delete_after)
            self.model_combo.setCurrentText(default_model)
            
            # Refresh file list
            self.refresh_file_list()
            
        except Exception as e:
            self.update_status(f"❌ Connection failed: {str(e)}", "error")
            self.log_message(f"Error: {str(e)}")

    def refresh_connection_status(self):
        """Refresh the connection status by reconnecting to Obsidian."""
        try:
            self.log_message("🔄 Refreshing connection status...")
            self.refresh_status_button.setEnabled(False)
            self.refresh_status_button.setText("🔄 Connecting...")
            
            # Use QTimer to avoid blocking the UI
            QTimer.singleShot(100, self._perform_connection_refresh)
        except Exception as e:
            self.log_message(f"❌ Error in refresh_connection_status: {str(e)}")
            # Re-enable the button if there's an error
            self.refresh_status_button.setEnabled(True)
            self.refresh_status_button.setText("🔄 Refresh Status")
    
    def _perform_connection_refresh(self):
        """Perform the actual connection refresh."""
        try:
            self.log_message("🔄 Performing connection refresh...")
            # Clear previous connection state
            self.session = None
            self.gemini_api_key = None
            
            # Attempt to reconnect (but don't call refresh_file_list during refresh)
            self._connect_to_obsidian_refresh()
            
        except Exception as e:
            self.log_message(f"❌ Connection refresh failed: {str(e)}")
        finally:
            # Re-enable the refresh button
            self.refresh_status_button.setEnabled(True)
            self.refresh_status_button.setText("🔄 Refresh Status")
    
    def _connect_to_obsidian_refresh(self):
        """Connect to Obsidian during refresh (without calling refresh_file_list)."""
        try:
            # Get configuration from config manager
            api_url, timeout, default_notes_folder = self.config_manager.get_obsidian_config()
            default_model, gemini_timeout = self.config_manager.get_gemini_config()
            default_ingest_folder, _, default_delete_after = self.config_manager.get_ingest_config()
            
            # Get API keys based on security method
            config = self.config_manager.load_config()
            security_method = config.get("security", {}).get("method", "local_encrypted")
            
            if security_method == "1password":
                # For 1Password, we need to check if references exist and optionally fetch actual keys
                try:
                    # Read references from the GUI fields (which should already be populated)
                    obsidian_api_key_ref = self.obsidian_1p_ref_edit.text().strip()
                    gemini_api_key_ref = self.gemini_1p_ref_edit.text().strip()
                    
                    if not obsidian_api_key_ref or not gemini_api_key_ref:
                        self.update_status("⚠️ 1Password mode: API key references not configured", "warning")
                        self.log_message("Configuration warning: 1Password references not found")
                        # Don't return - continue with setup but mark as not fully connected
                        self.api_url = api_url
                        self.session = None
                        self.gemini_api_key = None
                        
                        # Set default values in ingest tab (but don't refresh file list)
                        self.ingest_folder_edit.setText(default_ingest_folder)
                        self.notes_folder_edit.setText(default_notes_folder)
                        self.delete_files_checkbox.setChecked(default_delete_after)
                        self.model_combo.setCurrentText(default_model)
                        return
                    
                    # Try to fetch actual keys from 1Password, but don't fail if not authenticated
                    try:
                        obsidian_api_key = self.config_manager._fetch_1password_secret(obsidian_api_key_ref)
                        self.gemini_api_key = self.config_manager._fetch_1password_secret(gemini_api_key_ref)
                        
                        # If we got here, we successfully fetched the keys
                        self.api_url = api_url
                        self.session = create_api_session(obsidian_api_key)
                        
                        # Verify connection
                        verify_connection(self.session, self.api_url, timeout)
                        
                        # Update UI
                        self.update_status("✅ Connected to Obsidian", "success")
                        
                        # Update configuration status to show successful connection
                        if hasattr(self, 'config_status_label'):
                            self.config_status_label.setText("✅ Connected to Obsidian successfully")
                            self.config_status_label.setStyleSheet("color: #10b981; font-size: 13px;")
                        
                        # Set default values in ingest tab (but don't refresh file list)
                        self.ingest_folder_edit.setText(default_ingest_folder)
                        self.notes_folder_edit.setText(default_notes_folder)
                        self.delete_files_checkbox.setChecked(default_delete_after)
                        self.model_combo.setCurrentText(default_model)
                        return
                        
                    except Exception as e:
                        # 1Password might not be logged in - show warning instead of error
                        if "not signed in" in str(e).lower() or "authentication" in str(e).lower():
                            self.update_status("⚠️ 1Password not authenticated - please sign in via CLI", "warning")
                            self.log_message(f"1Password authentication required: {str(e)}")
                        else:
                            self.update_status(f"⚠️ 1Password error: {str(e)}", "warning")
                            self.log_message(f"1Password error: {str(e)}")
                        
                        # Update configuration status
                        if hasattr(self, 'config_status_label'):
                            self.config_status_label.setText("⚠️ 1Password authentication required")
                            self.config_status_label.setStyleSheet("color: #f59e0b; font-size: 12px;")
                        
                        # Continue with setup but mark as not fully connected
                        self.api_url = api_url
                        self.session = None
                        self.gemini_api_key = None
                        
                        # Set default values in ingest tab (but don't refresh file list)
                        self.ingest_folder_edit.setText(default_ingest_folder)
                        self.notes_folder_edit.setText(default_notes_folder)
                        self.delete_files_checkbox.setChecked(default_delete_after)
                        self.model_combo.setCurrentText(default_model)
                        return
                    
                except Exception as e:
                    # General error loading secrets - show warning
                    self.update_status(f"⚠️ Configuration warning: {str(e)}", "warning")
                    self.log_message(f"Configuration warning: {str(e)}")
                    
                    # Update configuration status
                    if hasattr(self, 'config_status_label'):
                        self.config_status_label.setText(f"⚠️ Configuration warning: {str(e)}")
                        self.config_status_label.setStyleSheet("color: #f59e0b; font-size: 12px;")
                    
                    # Continue with setup but mark as not fully connected
                    self.api_url = api_url
                    self.session = None
                    self.gemini_api_key = None
                    
                    # Set default values in ingest tab (but don't refresh file list)
                    self.ingest_folder_edit.setText(default_ingest_folder)
                    self.notes_folder_edit.setText(default_notes_folder)
                    self.delete_files_checkbox.setChecked(default_delete_after)
                    self.model_combo.setCurrentText(default_model)
                    return
            else:
                # For local encrypted storage
                try:
                    obsidian_api_key, self.gemini_api_key = self.config_manager.get_api_keys(self.master_password)
                except ValueError as e:
                    self.update_status(f"❌ Configuration incomplete: {str(e)}", "error")
                    self.log_message(f"Configuration error: {str(e)}")
                    return
            
            # Store API URL
            self.api_url = api_url
            
            # Create API session
            self.session = create_api_session(obsidian_api_key)
            
            # Verify connection
            verify_connection(self.session, self.api_url, timeout)
            
            # Update UI
            self.update_status("✅ Connected to Obsidian", "success")
            
            # Update configuration status to show successful connection
            if hasattr(self, 'config_status_label'):
                self.config_status_label.setText("✅ Connected to Obsidian successfully")
                self.config_status_label.setStyleSheet("color: #10b981; font-size: 13px;")
            
            # Set default values in ingest tab (but don't refresh file list)
            self.ingest_folder_edit.setText(default_ingest_folder)
            self.notes_folder_edit.setText(default_notes_folder)
            self.delete_files_checkbox.setChecked(default_delete_after)
            self.model_combo.setCurrentText(default_model)
            
        except Exception as e:
            self.update_status(f"❌ Connection failed: {str(e)}", "error")
            self.log_message(f"Error: {str(e)}")

    def update_status(self, message, status_type):
        """Update the status display with different types."""
        self.status_label.setText(message)
        
        if status_type == "success":
            self.status_frame.setStyleSheet("""
                QFrame {
                    background-color: #d1fae5;
                    border: 2px solid #10b981;
                    border-radius: 12px;
                    padding: 16px;
                }
            """)
            self.status_label.setStyleSheet("color: #065f46; margin: 0;")
        elif status_type == "error":
            self.status_frame.setStyleSheet("""
                QFrame {
                    background-color: #fee2e2;
                    border: 2px solid #ef4444;
                    border-radius: 12px;
                    padding: 16px;
                }
            """)
            self.status_label.setStyleSheet("color: #991b1b; margin: 0;")
        elif status_type == "warning":
            self.status_frame.setStyleSheet("""
                QFrame {
                    background-color: #fef3c7;
                    border: 2px solid #f59e0b;
                    border-radius: 12px;
                    padding: 16px;
                }
            """)
            self.status_label.setStyleSheet("color: #92400e; margin: 0;")
        else:
            self.status_frame.setStyleSheet("""
                QFrame {
                    background-color: #fef3c7;
                    border: 2px solid #f59e0b;
                    border-radius: 12px;
                    padding: 16px;
                }
            """)
            self.status_label.setStyleSheet("color: #92400e; margin: 0;")

    def select_ingest_folder(self):
        """Open folder dialog to select ingest folder."""
        folder = QFileDialog.getExistingDirectory(self, "Select Ingest Folder")
        if folder:
            self.ingest_folder_edit.setText(folder)
            self.refresh_file_list()

    def select_notes_folder(self):
        """Open folder dialog to select notes folder."""
        folder = QFileDialog.getExistingDirectory(self, "Select Notes Folder")
        if folder:
            self.notes_folder_edit.setText(folder)

    def select_vault_folder(self):
        """Open folder dialog to select vault folder for research."""
        folder = QFileDialog.getExistingDirectory(self, "Select Vault Folder to Research")
        if folder:
            self.vault_folder_edit.setText(folder)

    def start_web_research(self):
        """Start the web research process."""
        if not self.vault_folder_edit.text().strip():
            QMessageBox.warning(self, "Warning", "Please select a vault folder to research.")
            return
        
        if not self.wikipedia_checkbox.isChecked():
            QMessageBox.warning(self, "Warning", "Please enable at least one research source.")
            return
        
        # Disable button and show progress
        self.research_button.setEnabled(False)
        self.research_progress_bar.setVisible(True)
        self.research_progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Clear previous results
        self.research_results_text.clear()
        
        # Log start of research
        self.log_message("Starting web research...")
        self.research_results_text.append("🔍 Starting web research...\n")
        
        # TODO: Implement actual web research functionality
        # For now, just show a placeholder message
        self.research_results_text.append("✅ Web research tab is ready!\n")
        self.research_results_text.append("📁 Selected folder: " + self.vault_folder_edit.text() + "\n")
        self.research_results_text.append("🌐 Wikipedia research: " + ("Enabled" if self.wikipedia_checkbox.isChecked() else "Disabled") + "\n")
        self.research_results_text.append("📊 Max articles per note: " + str(self.max_articles_spin.value()) + "\n")
        self.research_results_text.append("💾 Backup original notes: " + ("Yes" if self.backup_original_checkbox.isChecked() else "No") + "\n")
        
        # Re-enable button and hide progress
        self.research_button.setEnabled(True)
        self.research_progress_bar.setVisible(False)
        
        self.log_message("Web research completed (placeholder implementation)")

    def refresh_file_list(self):
        """Refresh the list of files in the ingest folder."""
        try:
            # Check if the widgets exist before using them
            if not hasattr(self, 'ingest_folder_edit') or not hasattr(self, 'files_text'):
                self.log_message("Warning: Cannot refresh file list - widgets not ready")
                return
            
            ingest_folder = self.ingest_folder_edit.text()
            if not ingest_folder or not os.path.isdir(ingest_folder):
                self.files_text.setText("Folder not found or invalid")
                return
            
            files = []
            for filename in os.listdir(ingest_folder):
                file_path = os.path.join(ingest_folder, filename)
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path)
                    files.append(f"{filename} ({size} bytes)")
            
            if files:
                self.files_text.setText("\n".join(files))
            else:
                self.files_text.setText("No files found in ingest folder")
        except Exception as e:
            # Log the error but don't crash
            if hasattr(self, 'log_output'):
                self.log_message(f"Error refreshing file list: {str(e)}")
            if hasattr(self, 'files_text'):
                self.files_text.setText(f"Error reading folder: {str(e)}")

    def run_analysis(self):
        """Run the vault analysis."""
        if not self.session:
            QMessageBox.critical(self, "Error", "Not connected to Obsidian")
            return
        
        # Validate input
        if not self.validate_analysis_input():
            return
        
        # Disable button and show progress
        self.analyze_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Clear previous results
        self.results_text.clear()
        self.log_output.clear()
        
        # Create and start worker thread
        self.analysis_worker = AnalysisWorker(
            self.session, self.api_url, 10,
            self.output_file_edit.text(),
            self.hub_threshold_spin.value(),
            self.link_density_spin.value(),
            self.min_word_count_spin.value()
        )
        
        self.analysis_worker.progress.connect(self.log_message)
        self.analysis_worker.finished.connect(self.analysis_completed)
        self.analysis_worker.error.connect(self.analysis_error)
        
        self.analysis_worker.start()

    def validate_analysis_input(self):
        """Validate analysis input parameters."""
        errors = []
        
        # Check output file
        output_file = self.output_file_edit.text().strip()
        print(f"DEBUG: Output file text: '{output_file}' (length: {len(output_file)})")  # Debug output
        if not output_file:
            errors.append("Output file name is required")
        elif not output_file.endswith('.md'):
            errors.append("Output file must have .md extension")
        
        # Check hub threshold
        if self.hub_threshold_spin.value() < 1:
            errors.append("Hub threshold must be at least 1")
        
        # Check link density
        if self.link_density_spin.value() <= 0:
            errors.append("Link density threshold must be positive")
        
        # Check word count
        if self.min_word_count_spin.value() < 1:
            errors.append("Minimum word count must be at least 1")
        
        if errors:
            QMessageBox.warning(self, "Validation Error", 
                              "Please fix the following errors:\n\n" + "\n".join(f"• {error}" for error in errors))
            return False
        
        return True

    def analysis_completed(self, result):
        """Handle analysis completion."""
        self.progress_bar.setVisible(False)
        self.analyze_button.setEnabled(True)
        
        # Display results
        self.results_text.setText(result['content'])
        
        # Show completion message
        QMessageBox.information(self, "Analysis Complete", 
                              f"Analysis completed successfully!\nResults saved to: {result['output_file']}")
        
        self.log_message("✅ Analysis completed successfully!")

    def analysis_error(self, error_msg):
        """Handle analysis error."""
        self.progress_bar.setVisible(False)
        self.analyze_button.setEnabled(True)
        
        QMessageBox.critical(self, "Analysis Error", f"Analysis failed: {error_msg}")
        self.log_message(f"❌ Error: {error_msg}")

    def run_ingestion(self):
        """Run the document ingestion."""
        if not self.session:
            QMessageBox.critical(self, "Error", "Not connected to Obsidian")
            return
        
        if not self.gemini_api_key:
            QMessageBox.critical(self, "Error", "Gemini API key not configured")
            return
        
        # Validate input
        if not self.validate_ingestion_input():
            return
        
        # Disable button and show progress
        self.ingest_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Clear log
        self.log_output.clear()
        
        # Create and start worker thread
        self.ingest_worker = IngestWorker(
            self.ingest_folder_edit.text(), self.notes_folder_edit.text(), self.session,
            self.api_url, self.gemini_api_key, 10,
            self.delete_files_checkbox.isChecked(),
            self.model_combo.currentText()
        )
        
        self.ingest_worker.progress.connect(self.log_message)
        self.ingest_worker.finished.connect(self.ingestion_completed)
        self.ingest_worker.error.connect(self.ingestion_error)
        
        self.ingest_worker.start()

    def validate_ingestion_input(self):
        """Validate ingestion input parameters."""
        errors = []
        
        # Check ingest folder
        ingest_folder = self.ingest_folder_edit.text().strip()
        if not ingest_folder:
            errors.append("Ingest folder is required")
        elif not os.path.isdir(ingest_folder):
            errors.append(f"Ingest folder not found: {ingest_folder}")
        
        # Check notes folder
        notes_folder = self.notes_folder_edit.text().strip()
        if not notes_folder:
            errors.append("Notes folder is required")
        
        if errors:
            QMessageBox.warning(self, "Validation Error", 
                              "Please fix the following errors:\n\n" + "\n".join(f"• {error}" for error in errors))
            return False
        
        return True

    def ingestion_completed(self):
        """Handle ingestion completion."""
        self.progress_bar.setVisible(False)
        self.ingest_button.setEnabled(True)
        
        # Refresh file list
        self.refresh_file_list()
        
        # Show completion message
        QMessageBox.information(self, "Ingestion Complete", 
                              "Document ingestion completed successfully!")
        
        self.log_message("✅ Ingestion completed successfully!")

    def ingestion_error(self, error_msg):
        """Handle ingestion error."""
        self.progress_bar.setVisible(False)
        self.ingest_button.setEnabled(True)
        
        QMessageBox.critical(self, "Ingestion Error", f"Ingestion failed: {error_msg}")
        self.log_message(f"❌ Error: {error_msg}")

    def load_configuration(self):
        """Load configuration from the config manager."""
        try:
            config = self.config_manager.load_config()
            
            # Update security method
            security_method = config.get("security", {}).get("method", "local_encrypted")
            if security_method == "local_encrypted":
                self.security_local_radio.setChecked(True)
            else:
                self.security_1password_radio.setChecked(True)
            
            # Update connection settings
            obsidian_config = config.get("obsidian", {})
            self.obsidian_url_edit.setText(obsidian_config.get("api_url", "http://localhost:27123"))
            self.obsidian_timeout_spin.setValue(obsidian_config.get("timeout", 30))
            self.default_notes_folder_edit.setText(obsidian_config.get("default_notes_folder", "GeneratedNotes"))
            
            # Update ingest settings
            ingest_config = config.get("ingest", {})
            self.default_ingest_folder_edit.setText(ingest_config.get("default_ingest_folder", "ingest"))
            self.default_delete_after_ingest_checkbox.setChecked(ingest_config.get("delete_after_ingest", True))
            
            gemini_config = config.get("gemini", {})
            default_model = gemini_config.get("default_model", "gemini-2.5-flash")
            index = self.default_gemini_model_combo.findText(default_model)
            if index >= 0:
                self.default_gemini_model_combo.setCurrentIndex(index)
            
            # Load secrets to populate API key fields
            try:
                if security_method == "local_encrypted":
                    # For local encrypted, we can't load the actual keys without master password
                    # But we can show that they exist
                    try:
                        secrets = self.config_manager.load_secrets()
                        if secrets.get("obsidian_api_key"):
                            self.obsidian_api_key_edit.setText("*** ENCRYPTED ***")
                        if secrets.get("gemini_api_key"):
                            self.gemini_api_key_edit.setText("*** ENCRYPTED ***")
                    except:
                        # If we can't decrypt, that's okay
                        pass
                else:
                    # For 1Password, load the references directly from the secrets file
                    try:
                        secrets_file = self.config_manager.secrets_file
                        if secrets_file.exists():
                            with open(secrets_file, 'r') as f:
                                saved_secrets = json.load(f)
                            
                            # Load 1Password references
                            if saved_secrets.get("obsidian_api_key_ref"):
                                self.obsidian_1p_ref_edit.setText(saved_secrets["obsidian_api_key_ref"])
                            if saved_secrets.get("gemini_api_key_ref"):
                                self.gemini_1p_ref_edit.setText(saved_secrets["gemini_api_key_ref"])
                    except Exception as e:
                        # If we can't load references, that's okay
                        self.log_message(f"Could not load 1Password references: {str(e)}")
            except Exception as e:
                # If we can't load secrets, that's okay - they might be encrypted
                self.log_message(f"Could not load secrets: {str(e)}")
            
            # Update status - don't show success until connection is actually tested
            self.config_status_label.setText("Configuration loaded - connection status pending")
            self.config_status_label.setStyleSheet("color: #6b7280; font-size: 12px;")
            
        except Exception as e:
            self.config_status_label.setText(f"❌ Failed to load configuration: {str(e)}")
            self.config_status_label.setStyleSheet("color: #ef4444; font-size: 13px;")
            self.log_message(f"Configuration load error: {str(e)}")
    
    def save_configuration(self):
        """Save configuration to the config manager."""
        try:
            # Validate inputs
            if not self.validate_config_input():
                return
            
            # Build configuration
            config = {
                "obsidian": {
                    "api_url": self.obsidian_url_edit.text().strip(),
                    "timeout": self.obsidian_timeout_spin.value(),
                    "default_notes_folder": self.default_notes_folder_edit.text().strip()
                },
                "gemini": {
                    "default_model": self.default_gemini_model_combo.currentText(),
                    "timeout": 60
                },
                "ingest": {
                    "default_ingest_folder": self.default_ingest_folder_edit.text().strip(),
                    "delete_after_ingest": self.default_delete_after_ingest_checkbox.isChecked()
                },
                "security": {
                    "method": "local_encrypted" if self.security_local_radio.isChecked() else "1password",
                    "encryption_algorithm": "AES-256-GCM"
                }
            }
            
            # Build secrets
            secrets = {
                "obsidian_api_key": "",
                "gemini_api_key": "",
                "obsidian_api_key_ref": "",
                "gemini_api_key_ref": ""
            }
            
            if self.security_local_radio.isChecked():
                # Local encrypted storage
                secrets["obsidian_api_key"] = self.obsidian_api_key_edit.text().strip()
                secrets["gemini_api_key"] = self.gemini_api_key_edit.text().strip()
                
                # Validate master password
                master_password = self.master_password_edit.text().strip()
                confirm_password = self.confirm_password_edit.text().strip()
                
                if not master_password:
                    QMessageBox.warning(self, "Validation Error", "Master password is required for local encrypted storage")
                    return
                
                if master_password != confirm_password:
                    QMessageBox.warning(self, "Validation Error", "Master passwords do not match")
                    return
                
                self.master_password = master_password
                
            else:
                # 1Password integration
                secrets["obsidian_api_key_ref"] = self.strip_1password_quotes(self.obsidian_1p_ref_edit.text().strip())
                secrets["gemini_api_key_ref"] = self.strip_1password_quotes(self.gemini_1p_ref_edit.text().strip())
            
            # Save configuration
            self.config_manager.save_config(config)
            self.config_manager.save_secrets(secrets, self.master_password)
            
            # Update status
            self.config_status_label.setText("✅ Configuration saved successfully")
            self.config_status_label.setStyleSheet("color: #10b981; font-size: 13px;")
            
            # Update ingest tab with new defaults
            self.ingest_folder_edit.setText(config["ingest"]["default_ingest_folder"])
            self.notes_folder_edit.setText(config["obsidian"]["default_notes_folder"])
            self.delete_files_checkbox.setChecked(config["ingest"]["delete_after_ingest"])
            self.model_combo.setCurrentText(config["gemini"]["default_model"])
            
            QMessageBox.information(self, "Success", "Configuration saved successfully!")
            
        except Exception as e:
            self.config_status_label.setText(f"❌ Failed to save configuration: {str(e)}")
            self.config_status_label.setStyleSheet("color: #ef4444; font-size: 13px;")
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {str(e)}")
            self.log_message(f"Configuration save error: {str(e)}")
    
    def validate_config_input(self):
        """Validate configuration input."""
        errors = []
        
        # Check required fields
        if not self.obsidian_url_edit.text().strip():
            errors.append("Obsidian API URL is required")
        
        if not self.default_notes_folder_edit.text().strip():
            errors.append("Default notes folder is required")
        
        if not self.default_ingest_folder_edit.text().strip():
            errors.append("Default ingest folder is required")
        
        # Check security method specific validation
        if self.security_local_radio.isChecked():
            if not self.obsidian_api_key_edit.text().strip():
                errors.append("Obsidian API key is required for local storage")
            if not self.gemini_api_key_edit.text().strip():
                errors.append("Gemini API key is required for local storage")
        else:
            if not self.obsidian_1p_ref_edit.text().strip():
                errors.append("Obsidian API key reference is required for 1Password")
            else:
                # Validate 1Password reference format
                obsidian_ref = self.strip_1password_quotes(self.obsidian_1p_ref_edit.text().strip())
                is_valid, error_msg = self.validate_1password_reference(obsidian_ref)
                if not is_valid:
                    errors.append(f"Obsidian API key reference: {error_msg}")
            
            if not self.gemini_1p_ref_edit.text().strip():
                errors.append("Gemini API key reference is required for 1Password")
            else:
                # Validate 1Password reference format
                gemini_ref = self.strip_1password_quotes(self.gemini_1p_ref_edit.text().strip())
                is_valid, error_msg = self.validate_1password_reference(gemini_ref)
                if not is_valid:
                    errors.append(f"Gemini API key reference: {error_msg}")
        
        if errors:
            QMessageBox.warning(self, "Validation Error", 
                              "Please fix the following errors:\n\n" + "\n".join(f"• {error}" for error in errors))
            return False
        
        return True
    
    def test_connection(self):
        """Test connection to Obsidian API."""
        try:
            # Get current configuration
            api_url = self.obsidian_url_edit.text().strip()
            timeout = self.obsidian_timeout_spin.value()
            
            # Get API key based on security method
            if self.security_local_radio.isChecked():
                api_key = self.obsidian_api_key_edit.text().strip()
            else:
                # For 1Password, we need to fetch the key
                try:
                    ref = self.obsidian_1p_ref_edit.text().strip()
                    if ref:
                        # Strip quotes from 1Password reference
                        ref = self.strip_1password_quotes(ref)
                        api_key = self.config_manager._fetch_1password_secret(ref)
                    else:
                        QMessageBox.warning(self, "Validation Error", "Please enter a 1Password reference")
                        return
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to fetch API key from 1Password: {str(e)}")
                    return
            
            if not api_key:
                QMessageBox.warning(self, "Validation Error", "API key is required")
                return
            
            # Test connection
            if self.config_manager.test_connection(api_url, api_key, timeout):
                QMessageBox.information(self, "Success", "Connection test successful!")
                # Don't update the main status label here - it should reflect the actual app state
                # Just log the success
                self.log_message("✅ Connection test successful")
            else:
                QMessageBox.warning(self, "Connection Failed", "Failed to connect to Obsidian API")
                self.config_status_label.setText("❌ Connection test failed")
                self.config_status_label.setStyleSheet("color: #ef4444; font-size: 13px;")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Connection test failed: {str(e)}")
            self.log_message(f"Connection test error: {str(e)}")
    
    def export_configuration(self):
        """Export configuration to file."""
        try:
            from PyQt6.QtWidgets import QFileDialog
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Configuration", "obsidian_tools_config.json", "JSON Files (*.json)"
            )
            
            if file_path:
                include_secrets = QMessageBox.question(
                    self, "Include Secrets", 
                    "Do you want to include sensitive data in the export?\n\nThis will require your master password.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                ) == QMessageBox.StandardButton.Yes
                
                master_password = None
                if include_secrets and self.security_local_radio.isChecked():
                    master_password = self.master_password_edit.text().strip()
                    if not master_password:
                        QMessageBox.warning(self, "Error", "Master password required to export secrets")
                        return
                
                if self.config_manager.export_config(file_path, include_secrets, master_password):
                    QMessageBox.information(self, "Success", f"Configuration exported to:\n{file_path}")
                else:
                    QMessageBox.critical(self, "Error", "Failed to export configuration")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")
            self.log_message(f"Export error: {str(e)}")
    
    def import_configuration(self):
        """Import configuration from file."""
        try:
            from PyQt6.QtWidgets import QFileDialog
            
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Import Configuration", "", "JSON Files (*.json)"
            )
            
            if file_path:
                master_password = None
                if self.security_local_radio.isChecked():
                    master_password = self.master_password_edit.text().strip()
                    if not master_password:
                        QMessageBox.warning(self, "Error", "Master password required to import secrets")
                        return
                
                if self.config_manager.import_config(file_path, master_password):
                    QMessageBox.information(self, "Success", "Configuration imported successfully")
                    self.load_configuration()  # Reload the configuration
                else:
                    QMessageBox.critical(self, "Error", "Failed to import configuration")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Import failed: {str(e)}")
            self.log_message(f"Import error: {str(e)}")

    def log_message(self, message):
        """Add a message to the log output."""
        self.log_output.append(message)
        # Auto-scroll to bottom
        cursor = self.log_output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_output.setTextCursor(cursor)

    def strip_quotes_from_1p_ref(self):
        """Strip quotes from 1Password reference line edits."""
        # Get the sender to determine which field was changed
        sender = self.sender()
        if not sender:
            return
            
        text = sender.text()
        stripped_text = text
        
        # Remove surrounding quotes (both single and double quotes)
        if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
            stripped_text = text[1:-1]
            # Only update if we actually stripped quotes to avoid infinite loops
            if stripped_text != text:
                sender.setText(stripped_text)
                # Show a brief status message
                field_name = "Obsidian API key" if sender == self.obsidian_1p_ref_edit else "Gemini API key"
                self.config_status_label.setText(f"ℹ️ Quotes automatically removed from {field_name} reference")
                self.config_status_label.setStyleSheet("color: #3b82f6; font-size: 12px;")
                # Clear the message after 3 seconds
                QTimer.singleShot(3000, lambda: self.config_status_label.setText("Configuration not loaded"))
    
    def strip_1password_quotes(self, text):
        """Utility method to strip quotes from 1Password references."""
        if not text:
            return text
        
        # First strip whitespace to handle cases like '  "text"  '
        text = text.strip()
        
        # Remove surrounding quotes (both single and double quotes)
        if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
            text = text[1:-1]
        
        # Also clean up common formatting issues
        text = text.replace('\n', '').replace('\r', '')  # Remove newlines and carriage returns
        
        return text
    
    def validate_1password_reference(self, ref):
        """Validate 1Password reference format."""
        if not ref:
            return False, "1Password reference cannot be empty"
        
        # Check if it starts with op://
        if not ref.startswith('op://'):
            return False, "1Password reference must start with 'op://'"
        
        # Check if it has the required parts: op://vault/item/field
        parts = ref.split('/')
        if len(parts) < 5:  # op://vault/item/field = 5 parts
            return False, "1Password reference must be in format: op://vault/item/field"
        
        return True, "Valid 1Password reference"


def main():
    """Main function to run the GUI application."""
    app = QApplication(sys.argv)
    
    # Set application style and properties
    app.setStyle('Fusion')
    app.setApplicationName("Obsidian Tools")
    app.setApplicationVersion("1.0.0")
    
    # Create and show the main window
    window = ObsidianToolsGUI()
    window.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
