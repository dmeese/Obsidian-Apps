"""
Ingest Tab for ObsidianTools GUI.

This tab handles document ingestion functionality.
"""

import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QFileDialog, QTextEdit, QProgressBar, QCheckBox,
    QComboBox, QGroupBox, QMessageBox, QScrollArea
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont, QTextCursor
from core.services import ServiceContainer


class IngestWorker(QThread):
    """Worker thread for document ingestion."""
    
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, ingest_engine, params):
        super().__init__()
        self.ingest_engine = ingest_engine
        self.params = params
    
    def run(self):
        """Run the ingestion process."""
        try:
            self.progress.emit("Starting document ingestion...")
            result = self.ingest_engine.ingest_documents(self.params)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class IngestTab(QWidget):
    """Ingest tab for document ingestion functionality."""
    
    def __init__(self, service_container: ServiceContainer):
        super().__init__()
        self.service_container = service_container
        self.ingest_worker = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the ingest tab UI."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)
        
        # Title
        title = QLabel("Document Ingestion")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #1e293b; margin-bottom: 8px;")
        main_layout.addWidget(title)
        
        # Description
        description = QLabel(
            "Ingest documents and convert them into structured Obsidian notes "
            "using AI-powered analysis. Supports PDF, TXT, MD, and JSON files."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #64748b; margin-bottom: 16px;")
        main_layout.addWidget(description)
        
        # Create scrollable area for the main content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(16)
        
        # Configuration Group
        config_group = QGroupBox("Configuration")
        config_layout = QVBoxLayout(config_group)
        
        # Input folder selection
        input_layout = QHBoxLayout()
        input_label = QLabel("Input Folder:")
        input_label.setMinimumWidth(120)
        self.input_folder_edit = QLineEdit()
        self.input_folder_edit.setPlaceholderText("Select folder containing documents to process")
        input_browse_btn = QPushButton("Browse...")
        input_browse_btn.clicked.connect(self.browse_input_folder)
        input_layout.addWidget(input_label)
        input_layout.addWidget(self.input_folder_edit)
        input_layout.addWidget(input_browse_btn)
        config_layout.addLayout(input_layout)
        
        # Output folder selection
        output_layout = QHBoxLayout()
        output_label = QLabel("Output Folder:")
        output_label.setMinimumWidth(120)
        self.output_folder_edit = QLineEdit()
        self.output_folder_edit.setPlaceholderText("Select folder where notes will be created")
        output_browse_btn = QPushButton("Browse...")
        output_browse_btn.clicked.connect(self.browse_output_folder)
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_folder_edit)
        output_layout.addWidget(output_browse_btn)
        config_layout.addLayout(output_layout)
        
        # Model selection
        model_layout = QHBoxLayout()
        model_label = QLabel("LLM Model:")
        model_label.setMinimumWidth(120)
        self.model_combo = QComboBox()
        self.model_combo.addItems(["gemini-2.5-flash", "gemini-2.5-flash-lite"])
        self.model_combo.setCurrentText("gemini-2.5-flash")
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        config_layout.addLayout(model_layout)
        
        # Options
        options_layout = QHBoxLayout()
        self.delete_after_checkbox = QCheckBox("Delete source files after processing")
        self.delete_after_checkbox.setChecked(True)
        options_layout.addWidget(self.delete_after_checkbox)
        options_layout.addStretch()
        config_layout.addLayout(options_layout)
        
        content_layout.addWidget(config_group)
        
        # Control Group
        control_group = QGroupBox("Processing")
        control_layout = QVBoxLayout(control_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        self.process_btn = QPushButton("Start Processing")
        self.process_btn.clicked.connect(self.start_processing)
        self.process_btn.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #047857;
            }
            QPushButton:disabled {
                background-color: #9ca3af;
            }
        """)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_processing)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc2626;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #b91c1c;
            }
            QPushButton:disabled {
                background-color: #9ca3af;
            }
        """)
        
        button_layout.addWidget(self.process_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addStretch()
        control_layout.addLayout(button_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        control_layout.addWidget(self.progress_bar)
        
        content_layout.addWidget(control_group)
        
        # Status Group
        status_group = QGroupBox("Status & Logs")
        status_layout = QVBoxLayout(status_group)
        
        # Status label
        self.status_label = QLabel("Ready to process documents")
        self.status_label.setStyleSheet("color: #059669; font-weight: 500;")
        status_layout.addWidget(self.status_label)
        
        # Log display
        self.log_display = QTextEdit()
        self.log_display.setMaximumHeight(200)
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet("""
            QTextEdit {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
            }
        """)
        status_layout.addWidget(self.log_display)
        
        content_layout.addWidget(status_group)
        
        # Results Group
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout(results_group)
        
        self.results_display = QTextEdit()
        self.results_display.setMaximumHeight(150)
        self.results_display.setReadOnly(True)
        self.results_display.setStyleSheet("""
            QTextEdit {
                background-color: #f0f9ff;
                border: 1px solid #bae6fd;
                border-radius: 6px;
                padding: 8px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
            }
        """)
        results_layout.addWidget(self.results_display)
        
        content_layout.addWidget(results_group)
        
        # Add stretch to push everything to the top
        content_layout.addStretch()
        
        # Set the content widget
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
    
    def browse_input_folder(self):
        """Browse for input folder."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Input Folder", 
            str(Path.home())
        )
        if folder:
            self.input_folder_edit.setText(folder)
    
    def browse_output_folder(self):
        """Browse for output folder."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Output Folder", 
            str(Path.home())
        )
        if folder:
            self.output_folder_edit.setText(folder)
    
    def start_processing(self):
        """Start the document processing."""
        # Validate inputs
        input_folder = self.input_folder_edit.text().strip()
        output_folder = self.output_folder_edit.text().strip()
        
        if not input_folder:
            QMessageBox.warning(self, "Input Required", "Please select an input folder.")
            return
        
        if not output_folder:
            QMessageBox.warning(self, "Output Required", "Please select an output folder.")
            return
        
        if not os.path.exists(input_folder):
            QMessageBox.warning(self, "Invalid Input", "Input folder does not exist.")
            return
        
        # Check if ingest service is available
        ingest_service = self.service_container.get_service('ingest')
        if not ingest_service:
            QMessageBox.critical(self, "Service Error", "Ingest service is not available.")
            return
        
        # Prepare parameters
        params = {
            'ingest_folder': input_folder,
            'output_folder': output_folder,
            'delete_after_ingest': self.delete_after_checkbox.isChecked(),
            'model_name': self.model_combo.currentText()
        }
        
        # Start processing
        self.process_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Update UI
        self.status_label.setText("Processing documents...")
        self.status_label.setStyleSheet("color: #059669; font-weight: 500;")
        self.log_display.clear()
        self.results_display.clear()
        
        # Log start
        self.log_message("Starting document ingestion...")
        self.log_message(f"Input folder: {input_folder}")
        self.log_message(f"Output folder: {output_folder}")
        self.log_message(f"Model: {params['model_name']}")
        self.log_message(f"Delete after processing: {params['delete_after_ingest']}")
        
        # Create and start worker thread
        self.ingest_worker = IngestWorker(ingest_service, params)
        self.ingest_worker.progress.connect(self.log_message)
        self.ingest_worker.finished.connect(self.processing_finished)
        self.ingest_worker.error.connect(self.processing_error)
        self.ingest_worker.start()
    
    def stop_processing(self):
        """Stop the document processing."""
        if self.ingest_worker and self.ingest_worker.isRunning():
            self.ingest_worker.terminate()
            self.ingest_worker.wait()
            self.log_message("Processing stopped by user")
        
        self.reset_ui()
    
    def processing_finished(self, result):
        """Handle processing completion."""
        self.log_message("Processing completed!")
        
        # Display results
        if result.get('success', False):
            self.status_label.setText("✅ Processing completed successfully")
            self.status_label.setStyleSheet("color: #059669; font-weight: 500;")
            
            results_text = f"""
Processing Results:
• Documents processed: {result.get('documents_processed', 0)}
• Notes created: {result.get('notes_created', 0)}
• Files failed: {result.get('files_failed', 0)}
"""
            
            if result.get('processed_files'):
                results_text += f"\nProcessed files:\n"
                for file_path in result.get('processed_files', []):
                    results_text += f"• {os.path.basename(file_path)}\n"
            
            if result.get('errors'):
                results_text += f"\nErrors:\n"
                for error in result.get('errors', []):
                    results_text += f"• {error}\n"
            
            self.results_display.setPlainText(results_text)
            
        else:
            self.status_label.setText("❌ Processing failed")
            self.status_label.setStyleSheet("color: #dc2626; font-weight: 500;")
            
            error_msg = result.get('error', 'Unknown error occurred')
            self.results_display.setPlainText(f"Error: {error_msg}")
        
        self.reset_ui()
    
    def processing_error(self, error_msg):
        """Handle processing error."""
        self.log_message(f"Error: {error_msg}")
        self.status_label.setText("❌ Processing error occurred")
        self.status_label.setStyleSheet("color: #dc2626; font-weight: 500;")
        self.results_display.setPlainText(f"Error: {error_msg}")
        self.reset_ui()
    
    def reset_ui(self):
        """Reset the UI to initial state."""
        self.process_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)
        
        if self.ingest_worker:
            self.ingest_worker.deleteLater()
            self.ingest_worker = None
    
    def log_message(self, message):
        """Add a message to the log display."""
        self.log_display.append(f"[{self.get_current_time()}] {message}")
        
        # Auto-scroll to bottom
        cursor = self.log_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_display.setTextCursor(cursor)
    
    def get_current_time(self):
        """Get current time string."""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
    
    def update_status(self):
        """Update tab-specific status."""
        # Check if ingest service is available
        if self.service_container.has_service('ingest'):
            self.status_label.setText("✅ Ingest service available")
            self.status_label.setStyleSheet("color: #059669; font-weight: 500;")
        else:
            self.status_label.setText("❌ Ingest service unavailable")
            self.status_label.setStyleSheet("color: #dc2626; font-weight: 500;")
