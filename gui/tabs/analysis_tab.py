"""
Analysis Tab for ObsidianTools GUI.

This tab handles vault analysis functionality including
orphan detection, hub analysis, and report generation.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QPushButton,
    QTextEdit, QProgressBar, QSplitter, QFrame, QMessageBox,
    QFileDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from ..widgets import ModernButton, ModernLineEdit, ModernSpinBox, ModernDoubleSpinBox
from core.services import ServiceContainer


class AnalysisWorker(QThread):
    """Worker thread for running analysis operations."""
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    analysis_completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, service_container: ServiceContainer, params: dict):
        super().__init__()
        self.service_container = service_container
        self.params = params
    
    def run(self):
        """Run the analysis operation."""
        try:
            self.status_updated.emit("Starting analysis...")
            self.progress_updated.emit(10)
            
            # Get analysis service
            analysis_service = self.service_container.get_service('analysis')
            if not analysis_service:
                self.error_occurred.emit("Analysis service not available")
                return
            
            self.status_updated.emit("Fetching notes from vault...")
            self.progress_updated.emit(20)
            
            # Run analysis
            result = analysis_service.analyze_vault(self.params)
            
            self.progress_updated.emit(100)
            self.status_updated.emit("Analysis completed")
            self.analysis_completed.emit(result)
            
        except Exception as e:
            self.error_occurred.emit(str(e))


class AnalysisTab(QWidget):
    """Analysis tab for vault analysis functionality."""
    
    def __init__(self, service_container: ServiceContainer):
        super().__init__()
        self.service_container = service_container
        self.analysis_worker = None
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup the analysis tab UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Title
        title = QLabel("Vault Analysis")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #1e293b; margin-bottom: 8px;")
        layout.addWidget(title)
        
        # Description
        description = QLabel(
            "Analyze your Obsidian vault to find orphan notes, hub notes, "
            "and opportunities for improvement."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #64748b; margin-bottom: 16px;")
        layout.addWidget(description)
        
        # Create splitter for left/right layout
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel - Analysis parameters
        left_panel = self.create_parameters_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Results and output
        right_panel = self.create_results_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions (40% left, 60% right)
        splitter.setSizes([400, 600])
    
    def create_parameters_panel(self):
        """Create the left panel with analysis parameters."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # Analysis Parameters Group
        params_group = QGroupBox("Analysis Parameters")
        params_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        params_layout = QFormLayout(params_group)
        params_layout.setSpacing(12)
        
        # Output file
        self.output_file_edit = ModernLineEdit(
            placeholder="Enter output file path or browse...",
            initial_text="recommendations.md"
        )
        browse_button = ModernButton("Browse", size="small")
        browse_button.clicked.connect(self.browse_output_file)
        
        output_layout = QHBoxLayout()
        output_layout.addWidget(self.output_file_edit)
        output_layout.addWidget(browse_button)
        params_layout.addRow("Output File:", output_layout)
        
        # Hub threshold
        self.hub_threshold_spin = ModernSpinBox(1, 100, 10)
        params_layout.addRow("Hub Threshold:", self.hub_threshold_spin)
        
        # Link density threshold
        self.link_density_spin = ModernDoubleSpinBox(0.001, 1.0, 0.02, 3)
        params_layout.addRow("Link Density Threshold:", self.link_density_spin)
        
        # Min word count
        self.min_word_count_spin = ModernSpinBox(10, 1000, 50)
        params_layout.addRow("Min Word Count:", self.min_word_count_spin)
        
        layout.addWidget(params_group)
        
        # Analysis Actions Group
        actions_group = QGroupBox("Analysis Actions")
        actions_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        actions_layout = QVBoxLayout(actions_group)
        actions_layout.setSpacing(12)
        
        # Run analysis button
        self.run_analysis_button = ModernButton("Run Analysis", primary=True, size="large")
        self.run_analysis_button.clicked.connect(self.run_analysis)
        actions_layout.addWidget(self.run_analysis_button)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        actions_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready to analyze")
        self.status_label.setStyleSheet("color: #64748b; font-size: 12px;")
        actions_layout.addWidget(self.status_label)
        
        layout.addWidget(actions_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        return panel
    
    def create_results_panel(self):
        """Create the right panel with results and output."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # Results Group
        results_group = QGroupBox("Analysis Results")
        results_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        results_layout = QVBoxLayout(results_group)
        
        # Results text area
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Consolas", 10))
        self.results_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 8px;
                background-color: #f8fafc;
                color: #1e293b;
            }
        """)
        self.results_text.setPlaceholderText("Analysis results will appear here...")
        results_layout.addWidget(self.results_text)
        
        # Export button
        export_layout = QHBoxLayout()
        export_layout.addStretch()
        
        self.export_button = ModernButton("Export Results", size="medium")
        self.export_button.clicked.connect(self.export_results)
        self.export_button.setEnabled(False)
        export_layout.addWidget(self.export_button)
        
        results_layout.addLayout(export_layout)
        layout.addWidget(results_group)
        
        return panel
    
    def setup_connections(self):
        """Setup signal connections."""
        # Worker signals
        # These will be connected when the worker is created
    
    def browse_output_file(self):
        """Browse for output file location."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Analysis Report",
            "recommendations.md",
            "Markdown Files (*.md);;Text Files (*.txt);;All Files (*.*)"
        )
        if file_path:
            self.output_file_edit.setText(file_path)
    
    def run_analysis(self):
        """Run the vault analysis."""
        # Validate inputs
        output_file = self.output_file_edit.text().strip()
        if not output_file:
            QMessageBox.warning(self, "Input Error", "Please specify an output file path.")
            return
        
        # Get parameters
        params = {
            'output_file': output_file,
            'hub_threshold': self.hub_threshold_spin.value(),
            'link_density_threshold': self.link_density_spin.value(),
            'min_word_count': self.min_word_count_spin.value()
        }
        
        # Disable UI during analysis
        self.run_analysis_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Starting analysis...")
        
        # Create and start worker
        self.analysis_worker = AnalysisWorker(self.service_container, params)
        self.analysis_worker.progress_updated.connect(self.progress_bar.setValue)
        self.analysis_worker.status_updated.connect(self.status_label.setText)
        self.analysis_worker.analysis_completed.connect(self.on_analysis_completed)
        self.analysis_worker.error_occurred.connect(self.on_analysis_error)
        self.analysis_worker.finished.connect(self.on_analysis_finished)
        
        self.analysis_worker.start()
    
    def on_analysis_completed(self, result: dict):
        """Handle analysis completion."""
        # Display results
        self.results_text.clear()
        
        # Format and display results
        report = self.format_analysis_report(result)
        self.results_text.setPlainText(report)
        
        # Enable export button
        self.export_button.setEnabled(True)
        
        # Update status
        self.status_label.setText("Analysis completed successfully")
    
    def on_analysis_error(self, error_message: str):
        """Handle analysis errors."""
        QMessageBox.critical(self, "Analysis Error", f"Analysis failed: {error_message}")
        self.status_label.setText("Analysis failed")
    
    def on_analysis_finished(self):
        """Handle analysis worker completion."""
        # Re-enable UI
        self.run_analysis_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        # Clean up worker
        if self.analysis_worker:
            self.analysis_worker.deleteLater()
            self.analysis_worker = None
    
    def format_analysis_report(self, result: dict) -> str:
        """Format analysis results into a readable report."""
        report_lines = []
        report_lines.append("# Obsidian Vault Analysis Report")
        report_lines.append("")
        
        # Summary
        report_lines.append("## Summary")
        report_lines.append(f"Total Notes: {result.get('total_notes', 0)}")
        report_lines.append(f"Total Links: {result.get('total_links', 0)}")
        report_lines.append("")
        
        # Orphan notes
        orphans = result.get('orphans', [])
        report_lines.append(f"## Orphan Notes ({len(orphans)})")
        if orphans:
            for orphan in orphans:
                report_lines.append(f"- {orphan}")
        else:
            report_lines.append("No orphan notes found.")
        report_lines.append("")
        
        # Hub notes
        hubs = result.get('hubs', [])
        report_lines.append(f"## Hub Notes ({len(hubs)})")
        if hubs:
            for hub in hubs:
                report_lines.append(f"- {hub}")
        else:
            report_lines.append("No hub notes found.")
        report_lines.append("")
        
        # Dead-end notes
        dead_ends = result.get('dead_ends', [])
        report_lines.append(f"## Dead-End Notes ({len(dead_ends)})")
        if dead_ends:
            for dead_end in dead_ends:
                report_lines.append(f"- {dead_end}")
        else:
            report_lines.append("No dead-end notes found.")
        report_lines.append("")
        
        # Low density notes
        low_density = result.get('low_density_notes', [])
        report_lines.append(f"## Low Link Density Notes ({len(low_density)})")
        if low_density:
            for note in low_density:
                report_lines.append(f"- {note}")
        else:
            report_lines.append("No low density notes found.")
        report_lines.append("")
        
        # Stubs
        stubs = result.get('stubs', [])
        report_lines.append(f"## Stub Links ({len(stubs)})")
        if stubs:
            for stub in stubs:
                report_lines.append(f"- {stub}")
        else:
            report_lines.append("No stub links found.")
        
        return "\n".join(report_lines)
    
    def export_results(self):
        """Export analysis results to file."""
        if not self.results_text.toPlainText():
            QMessageBox.warning(self, "Export Error", "No results to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Analysis Results",
            "analysis_report.md",
            "Markdown Files (*.md);;Text Files (*.txt);;All Files (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.results_text.toPlainText())
                QMessageBox.information(self, "Export Success", f"Results exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export results: {e}")
    
    def update_status(self):
        """Update tab-specific status."""
        # Check if analysis service is available
        analysis_service = self.service_container.get_service('analysis')
        if analysis_service:
            self.status_label.setText("Analysis service available")
        else:
            self.status_label.setText("Analysis service not available")
