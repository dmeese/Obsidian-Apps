"""
Configuration Tab for ObsidianTools GUI.

This tab handles application configuration and settings.
"""

import os
import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QFileDialog, QTextEdit, QComboBox, QCheckBox,
    QGroupBox, QMessageBox, QScrollArea, QSpinBox, QTabWidget,
    QFormLayout, QProgressBar
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QFont, QTextCursor, QIcon
from core.services import ServiceContainer


class ConfigWorker(QThread):
    """Worker thread for configuration operations."""
    
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, operation, config_manager, params):
        super().__init__()
        self.operation = operation
        self.config_manager = config_manager
        self.params = params
    
    def run(self):
        """Run the configuration operation."""
        try:
            if self.operation == "test_connection":
                self.progress.emit("Testing Obsidian connection...")
                success = self.config_manager.test_connection(
                    self.params['api_url'],
                    self.params['api_key'],
                    self.params['timeout']
                )
                result = {"success": success, "operation": "test_connection"}
                self.finished.emit(result)
                
            elif self.operation == "validate_config":
                self.progress.emit("Validating configuration...")
                is_valid, errors = self.config_manager.validate_config()
                result = {"success": is_valid, "errors": errors, "operation": "validate_config"}
                self.finished.emit(result)
                
            elif self.operation == "migrate_env":
                self.progress.emit("Migrating from environment file...")
                success = self.config_manager.migrate_from_env(self.params['env_file'])
                result = {"success": success, "operation": "migrate_env"}
                self.finished.emit(result)
                
        except Exception as e:
            self.error.emit(str(e))


class ConfigTab(QWidget):
    """Configuration tab for application settings."""
    
    def __init__(self, service_container: ServiceContainer):
        super().__init__()
        self.service_container = service_container
        self.config_manager = service_container.get_service('config')
        self.config_worker = None
        self.setup_ui()
        self.load_current_config()
    
    def setup_ui(self):
        """Setup the configuration tab UI."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)
        
        # Title
        title = QLabel("Configuration & Security")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #1e293b; margin-bottom: 8px;")
        main_layout.addWidget(title)
        
        # Description
        description = QLabel(
            "Configure application settings, API keys, and security preferences. "
            "Choose between 1Password integration or local encrypted storage for your secrets."
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
        
        # Security Method Group
        security_group = QGroupBox("Security Method")
        security_layout = QVBoxLayout(security_group)
        
        # Security method selection
        method_layout = QHBoxLayout()
        method_label = QLabel("Security Method:")
        method_label.setMinimumWidth(120)
        self.security_method_combo = QComboBox()
        self.security_method_combo.addItems(["local_encrypted", "1password"])
        self.security_method_combo.currentTextChanged.connect(self.on_security_method_changed)
        method_layout.addWidget(method_label)
        method_layout.addWidget(self.security_method_combo)
        method_layout.addStretch()
        security_layout.addLayout(method_layout)
        
        # Security method description
        self.security_description = QLabel("")
        self.security_description.setWordWrap(True)
        self.security_description.setStyleSheet("color: #64748b; font-size: 12px;")
        security_layout.addWidget(self.security_description)
        
        content_layout.addWidget(security_group)
        
        # Obsidian Configuration Group
        obsidian_group = QGroupBox("Obsidian Configuration")
        obsidian_layout = QFormLayout(obsidian_group)
        
        # API URL
        self.obsidian_url_edit = QLineEdit()
        self.obsidian_url_edit.setPlaceholderText("http://localhost:27123")
        obsidian_layout.addRow("API URL:", self.obsidian_url_edit)
        
        # Timeout
        self.obsidian_timeout_spin = QSpinBox()
        self.obsidian_timeout_spin.setRange(5, 120)
        self.obsidian_timeout_spin.setValue(30)
        self.obsidian_timeout_spin.setSuffix(" seconds")
        obsidian_layout.addRow("Timeout:", self.obsidian_timeout_spin)
        
        # Default notes folder
        self.obsidian_folder_edit = QLineEdit()
        self.obsidian_folder_edit.setPlaceholderText("GeneratedNotes")
        obsidian_layout.addRow("Default Notes Folder:", self.obsidian_folder_edit)
        
        content_layout.addWidget(obsidian_group)
        
        # API Keys Group
        api_keys_group = QGroupBox("API Keys")
        api_keys_layout = QVBoxLayout(api_keys_group)
        
        # 1Password References (shown when 1Password is selected)
        self.onepassword_widget = QWidget()
        self.onepassword_layout = QFormLayout(self.onepassword_widget)
        
        # Obsidian API Key Reference
        self.obsidian_ref_edit = QLineEdit()
        self.obsidian_ref_edit.setPlaceholderText("op://vault/item/field")
        self.onepassword_layout.addRow("Obsidian API Key Reference:", self.obsidian_ref_edit)
        
        # Gemini API Key Reference
        self.gemini_ref_edit = QLineEdit()
        self.gemini_ref_edit.setPlaceholderText("op://vault/item/field")
        self.onepassword_layout.addRow("Gemini API Key Reference:", self.gemini_ref_edit)
        
        api_keys_layout.addWidget(self.onepassword_widget)
        
        # Local Encrypted (shown when local encrypted is selected)
        self.local_encrypted_widget = QWidget()
        self.local_encrypted_layout = QFormLayout(self.local_encrypted_widget)
        
        # Master Password
        self.master_password_edit = QLineEdit()
        self.master_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.master_password_edit.setPlaceholderText("Enter master password")
        self.local_encrypted_layout.addRow("Master Password:", self.master_password_edit)
        
        # Confirm Master Password
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_edit.setPlaceholderText("Confirm master password")
        self.local_encrypted_layout.addRow("Confirm Password:", self.confirm_password_edit)
        
        # Show/Hide Password Checkbox
        self.show_password_checkbox = QCheckBox("Show passwords")
        self.show_password_checkbox.toggled.connect(self.on_show_password_toggled)
        self.local_encrypted_layout.addRow("", self.show_password_checkbox)
        
        api_keys_layout.addWidget(self.local_encrypted_widget)
        
        content_layout.addWidget(api_keys_group)
        
        # Gemini Configuration Group
        gemini_group = QGroupBox("Gemini Configuration")
        gemini_layout = QFormLayout(gemini_group)
        
        # Default Model
        self.gemini_model_combo = QComboBox()
        self.gemini_model_combo.addItems(["gemini-2.5-flash", "gemini-2.5-flash-lite"])
        gemini_layout.addRow("Default Model:", self.gemini_model_combo)
        
        # Timeout
        self.gemini_timeout_spin = QSpinBox()
        self.gemini_timeout_spin.setRange(10, 300)
        self.gemini_timeout_spin.setValue(60)
        self.gemini_timeout_spin.setSuffix(" seconds")
        gemini_layout.addRow("Timeout:", self.gemini_timeout_spin)
        
        content_layout.addWidget(gemini_group)
        
        # Ingest Configuration Group
        ingest_group = QGroupBox("Ingest Configuration")
        ingest_layout = QFormLayout(ingest_group)
        
        # Default Ingest Folder
        self.ingest_folder_edit = QLineEdit()
        self.ingest_folder_edit.setPlaceholderText("ingest")
        ingest_layout.addRow("Default Ingest Folder:", self.ingest_folder_edit)
        
        # Delete After Ingest
        self.delete_after_checkbox = QCheckBox("Delete source files after processing")
        self.delete_after_checkbox.setChecked(True)
        ingest_layout.addRow("", self.delete_after_checkbox)
        
        content_layout.addWidget(ingest_group)
        
        # Control Buttons Group
        control_group = QGroupBox("Configuration Actions")
        control_layout = QVBoxLayout(control_group)
        
        # Button row 1
        button_row1 = QHBoxLayout()
        
        self.save_btn = QPushButton("Save Configuration")
        self.save_btn.clicked.connect(self.save_configuration)
        self.save_btn.setStyleSheet("""
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
        
        self.test_connection_btn = QPushButton("Test Connection")
        self.test_connection_btn.clicked.connect(self.test_connection)
        self.test_connection_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:disabled {
                background-color: #9ca3af;
            }
        """)
        
        self.validate_btn = QPushButton("Validate Configuration")
        self.validate_btn.clicked.connect(self.validate_configuration)
        self.validate_btn.setStyleSheet("""
            QPushButton {
                background-color: #7c3aed;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #6d28d9;
            }
            QPushButton:disabled {
                background-color: #9ca3af;
            }
        """)
        
        button_row1.addWidget(self.save_btn)
        button_row1.addWidget(self.test_connection_btn)
        button_row1.addWidget(self.validate_btn)
        button_row1.addStretch()
        control_layout.addLayout(button_row1)
        
        # Button row 2
        button_row2 = QHBoxLayout()
        
        self.export_btn = QPushButton("Export Configuration")
        self.export_btn.clicked.connect(self.export_configuration)
        self.export_btn.setStyleSheet("""
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
        
        self.import_btn = QPushButton("Import Configuration")
        self.import_btn.clicked.connect(self.import_configuration)
        self.import_btn.setStyleSheet("""
            QPushButton {
                background-color: #ea580c;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #c2410c;
            }
            QPushButton:disabled {
                background-color: #9ca3af;
            }
        """)
        
        self.migrate_env_btn = QPushButton("Migrate from .env")
        self.migrate_env_btn.clicked.connect(self.migrate_from_env)
        self.migrate_env_btn.setStyleSheet("""
            QPushButton {
                background-color: #0891b2;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0e7490;
            }
            QPushButton:disabled {
                background-color: #9ca3af;
            }
        """)
        
        button_row2.addWidget(self.export_btn)
        button_row2.addWidget(self.import_btn)
        button_row2.addWidget(self.migrate_env_btn)
        button_row2.addStretch()
        control_layout.addLayout(button_row2)
        
        content_layout.addWidget(control_group)
        
        # Status & Logs Group
        status_group = QGroupBox("Status & Logs")
        status_layout = QVBoxLayout(status_group)
        
        # Status label
        self.status_label = QLabel("Configuration ready")
        self.status_label.setStyleSheet("color: #059669; font-weight: 500;")
        status_layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
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
        
        # Add stretch to push everything to the top
        content_layout.addStretch()
        
        # Set the content widget
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        # Update security method description
        self.on_security_method_changed(self.security_method_combo.currentText())
    
    def on_security_method_changed(self, method):
        """Handle security method change."""
        if method == "1password":
            self.security_description.setText(
                "1Password Integration: Store API key references securely in 1Password. "
                "You'll need the 1Password CLI installed and authenticated."
            )
            self.onepassword_widget.setVisible(True)
            self.local_encrypted_widget.setVisible(False)
        else:
            self.security_description.setText(
                "Local Encrypted Storage: Store API keys locally using AES-256 encryption. "
                "You'll need to remember a master password to access your keys."
            )
            self.onepassword_widget.setVisible(False)
            self.local_encrypted_widget.setVisible(True)
    
    def on_show_password_toggled(self, checked):
        """Handle show/hide password toggle."""
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self.master_password_edit.setEchoMode(mode)
        self.confirm_password_edit.setEchoMode(mode)
    
    def load_current_config(self):
        """Load current configuration into the UI."""
        try:
            if not self.config_manager:
                self.log_message("Configuration manager not available")
                return
            
            # Load configuration
            config = self.config_manager.load_config()
            
            # Update UI with current config
            self.obsidian_url_edit.setText(config.get('obsidian', {}).get('api_url', 'http://localhost:27123'))
            self.obsidian_timeout_spin.setValue(config.get('obsidian', {}).get('timeout', 30))
            self.obsidian_folder_edit.setText(config.get('obsidian', {}).get('default_notes_folder', 'GeneratedNotes'))
            
            self.gemini_model_combo.setCurrentText(config.get('gemini', {}).get('default_model', 'gemini-2.5-flash'))
            self.gemini_timeout_spin.setValue(config.get('gemini', {}).get('timeout', 60))
            
            self.ingest_folder_edit.setText(config.get('ingest', {}).get('default_ingest_folder', 'ingest'))
            self.delete_after_checkbox.setChecked(config.get('ingest', {}).get('delete_after_ingest', True))
            
            # Set security method
            security_method = config.get('security', {}).get('method', 'local_encrypted')
            self.security_method_combo.setCurrentText(security_method)
            
            # Try to load secrets (without password for display purposes)
            try:
                secrets = self.config_manager.load_secrets()
                self.obsidian_ref_edit.setText(secrets.get('obsidian_api_key_ref', ''))
                self.gemini_ref_edit.setText(secrets.get('gemini_api_key_ref', ''))
            except:
                pass
            
            self.log_message("Configuration loaded successfully")
            
        except Exception as e:
            self.log_message(f"Failed to load configuration: {e}")
    
    def save_configuration(self):
        """Save the current configuration."""
        try:
            if not self.config_manager:
                QMessageBox.critical(self, "Error", "Configuration manager not available")
                return
            
            # Validate inputs
            if not self.validate_inputs():
                return
            
            # Prepare configuration
            config = {
                "obsidian": {
                    "api_url": self.obsidian_url_edit.text().strip(),
                    "timeout": self.obsidian_timeout_spin.value(),
                    "default_notes_folder": self.obsidian_folder_edit.text().strip()
                },
                "gemini": {
                    "default_model": self.gemini_model_combo.currentText(),
                    "timeout": self.gemini_timeout_spin.value()
                },
                "ingest": {
                    "default_ingest_folder": self.ingest_folder_edit.text().strip(),
                    "delete_after_ingest": self.delete_after_checkbox.isChecked()
                },
                "security": {
                    "method": self.security_method_combo.currentText()
                }
            }
            
            # Prepare secrets
            secrets = {}
            if self.security_method_combo.currentText() == "1password":
                secrets = {
                    "obsidian_api_key_ref": self.obsidian_ref_edit.text().strip(),
                    "gemini_api_key_ref": self.gemini_ref_edit.text().strip()
                }
            else:
                # For local encrypted, we need the master password
                master_password = self.master_password_edit.text()
                if not master_password:
                    QMessageBox.warning(self, "Password Required", "Please enter a master password for local encryption.")
                    return
                
                if master_password != self.confirm_password_edit.text():
                    QMessageBox.warning(self, "Password Mismatch", "Passwords do not match.")
                    return
                
                # Create empty secrets for now (keys will be added later)
                secrets = {
                    "obsidian_api_key": "",
                    "gemini_api_key": ""
                }
            
            # Save configuration
            self.config_manager.save_config(config)
            
            # Save secrets
            if self.security_method_combo.currentText() == "local_encrypted":
                master_password = self.master_password_edit.text()
                self.config_manager.save_secrets(secrets, master_password)
            else:
                self.config_manager.save_secrets(secrets)
            
            # Reload services
            self.service_container.reload_services()
            
            self.log_message("Configuration saved successfully")
            self.status_label.setText("✅ Configuration saved")
            self.status_label.setStyleSheet("color: #059669; font-weight: 500;")
            
            QMessageBox.information(self, "Success", "Configuration saved successfully!")
            
        except Exception as e:
            error_msg = f"Failed to save configuration: {e}"
            self.log_message(error_msg)
            self.status_label.setText("❌ Configuration save failed")
            self.status_label.setStyleSheet("color: #dc2626; font-weight: 500;")
            QMessageBox.critical(self, "Error", error_msg)
    
    def validate_inputs(self):
        """Validate user inputs."""
        errors = []
        
        # Check required fields
        if not self.obsidian_url_edit.text().strip():
            errors.append("Obsidian API URL is required")
        
        if self.security_method_combo.currentText() == "1password":
            if not self.obsidian_ref_edit.text().strip():
                errors.append("Obsidian API key reference is required")
            if not self.gemini_ref_edit.text().strip():
                errors.append("Gemini API key reference is required")
        else:
            if not self.master_password_edit.text():
                errors.append("Master password is required")
            if self.master_password_edit.text() != self.confirm_password_edit.text():
                errors.append("Passwords do not match")
        
        if errors:
            QMessageBox.warning(self, "Validation Errors", "\n".join(errors))
            return False
        
        return True
    
    def test_connection(self):
        """Test the Obsidian connection."""
        try:
            if not self.validate_inputs():
                return
            
            # Get API key for testing
            api_key = ""
            if self.security_method_combo.currentText() == "1password":
                # For 1Password, we need to fetch the actual key
                try:
                    secrets = self.config_manager.load_secrets()
                    api_key = secrets.get('obsidian_api_key', '')
                except:
                    QMessageBox.warning(self, "Warning", "Cannot test connection without valid API keys. Please save configuration first.")
                    return
            else:
                # For local encrypted, we can't test without the password
                QMessageBox.warning(self, "Warning", "Cannot test connection without valid API keys. Please save configuration first.")
                return
            
            # Start connection test
            params = {
                'api_url': self.obsidian_url_edit.text().strip(),
                'api_key': api_key,
                'timeout': self.obsidian_timeout_spin.value()
            }
            
            self.start_worker("test_connection", params)
            
        except Exception as e:
            self.log_message(f"Connection test failed: {e}")
    
    def validate_configuration(self):
        """Validate the current configuration."""
        try:
            self.start_worker("validate_config", {})
        except Exception as e:
            self.log_message(f"Configuration validation failed: {e}")
    
    def export_configuration(self):
        """Export configuration to file."""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Configuration", 
                str(Path.home() / "obsidian_tools_config.json"),
                "JSON Files (*.json)"
            )
            
            if file_path:
                include_secrets = QMessageBox.question(
                    self, "Include Secrets", 
                    "Do you want to include API keys in the export? (Not recommended for security)",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                ) == QMessageBox.StandardButton.Yes
                
                self.config_manager.export_config(file_path, include_secrets)
                self.log_message(f"Configuration exported to: {file_path}")
                QMessageBox.information(self, "Success", "Configuration exported successfully!")
                
        except Exception as e:
            error_msg = f"Failed to export configuration: {e}"
            self.log_message(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
    
    def import_configuration(self):
        """Import configuration from file."""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Import Configuration", 
                str(Path.home()),
                "JSON Files (*.json)"
            )
            
            if file_path:
                # Ask for master password if needed
                master_password = None
                if self.security_method_combo.currentText() == "local_encrypted":
                    master_password, ok = QMessageBox.getText(
                        self, "Master Password", 
                        "Enter master password for imported configuration:",
                        QLineEdit.EchoMode.Password
                    )
                    if not ok:
                        return
                
                self.config_manager.import_config(file_path, master_password)
                self.load_current_config()
                self.log_message(f"Configuration imported from: {file_path}")
                QMessageBox.information(self, "Success", "Configuration imported successfully!")
                
        except Exception as e:
            error_msg = f"Failed to import configuration: {e}"
            self.log_message(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
    
    def migrate_from_env(self):
        """Migrate configuration from .env file."""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select .env File", 
                str(Path.home()),
                "Environment Files (*.env);;All Files (*)"
            )
            
            if file_path:
                self.start_worker("migrate_env", {'env_file': file_path})
                
        except Exception as e:
            self.log_message(f"Migration failed: {e}")
    
    def start_worker(self, operation, params):
        """Start a configuration worker thread."""
        if self.config_worker and self.config_worker.isRunning():
            self.config_worker.terminate()
            self.config_worker.wait()
        
        self.config_worker = ConfigWorker(operation, self.config_manager, params)
        self.config_worker.progress.connect(self.log_message)
        self.config_worker.finished.connect(self.worker_finished)
        self.config_worker.error.connect(self.worker_error)
        
        # Update UI
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.status_label.setText("Processing...")
        self.status_label.setStyleSheet("color: #059669; font-weight: 500;")
        
        # Disable buttons
        self.save_btn.setEnabled(False)
        self.test_connection_btn.setEnabled(False)
        self.validate_btn.setEnabled(False)
        
        self.config_worker.start()
    
    def worker_finished(self, result):
        """Handle worker completion."""
        operation = result.get('operation', 'unknown')
        
        if operation == "test_connection":
            if result.get('success', False):
                self.status_label.setText("✅ Connection test successful")
                self.status_label.setStyleSheet("color: #059669; font-weight: 500;")
                self.log_message("Connection test successful!")
                QMessageBox.information(self, "Success", "Connection test successful!")
            else:
                self.status_label.setText("❌ Connection test failed")
                self.status_label.setStyleSheet("color: #dc2626; font-weight: 500;")
                self.log_message("Connection test failed!")
                QMessageBox.warning(self, "Warning", "Connection test failed!")
                
        elif operation == "validate_config":
            if result.get('success', False):
                self.status_label.setText("✅ Configuration is valid")
                self.status_label.setStyleSheet("color: #059669; font-weight: 500;")
                self.log_message("Configuration validation successful!")
                QMessageBox.information(self, "Success", "Configuration is valid!")
            else:
                errors = result.get('errors', [])
                self.status_label.setText("❌ Configuration has errors")
                self.status_label.setStyleSheet("color: #dc2626; font-weight: 500;")
                self.log_message("Configuration validation failed:")
                for error in errors:
                    self.log_message(f"  - {error}")
                QMessageBox.warning(self, "Validation Errors", "\n".join(errors))
                
        elif operation == "migrate_env":
            if result.get('success', False):
                self.status_label.setText("✅ Migration successful")
                self.status_label.setStyleSheet("color: #059669; font-weight: 500;")
                self.log_message("Environment migration successful!")
                self.load_current_config()
                QMessageBox.information(self, "Success", "Migration from .env file successful!")
            else:
                self.status_label.setText("❌ Migration failed")
                self.status_label.setStyleSheet("color: #dc2626; font-weight: 500;")
                self.log_message("Environment migration failed!")
                QMessageBox.warning(self, "Warning", "Migration from .env file failed!")
        
        self.reset_ui()
    
    def worker_error(self, error_msg):
        """Handle worker error."""
        self.log_message(f"Error: {error_msg}")
        self.status_label.setText("❌ Operation failed")
        self.status_label.setStyleSheet("color: #dc2626; font-weight: 500;")
        QMessageBox.critical(self, "Error", f"Operation failed: {error_msg}")
        self.reset_ui()
    
    def reset_ui(self):
        """Reset the UI to normal state."""
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)
        
        # Re-enable buttons
        self.save_btn.setEnabled(True)
        self.test_connection_btn.setEnabled(True)
        self.validate_btn.setEnabled(True)
        
        if self.config_worker:
            self.config_worker.deleteLater()
            self.config_worker = None
    
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
        if not self.config_manager:
            self.status_label.setText("❌ Configuration manager unavailable")
            self.status_label.setStyleSheet("color: #dc2626; font-weight: 500;")
            return
        
        # Check if configuration is valid
        try:
            is_valid, errors = self.config_manager.validate_config()
            if is_valid:
                self.status_label.setText("✅ Configuration is valid")
                self.status_label.setStyleSheet("color: #059669; font-weight: 500;")
            else:
                self.status_label.setText(f"⚠️ Configuration has {len(errors)} errors")
                self.status_label.setStyleSheet("color: #f59e0b; font-weight: 500;")
        except:
            self.status_label.setText("❌ Configuration validation failed")
            self.status_label.setStyleSheet("color: #dc2626; font-weight: 500;")
