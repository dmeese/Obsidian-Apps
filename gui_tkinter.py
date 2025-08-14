import sys
import os
import logging
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from utils import load_config, create_api_session, verify_connection
from analyzer import run_analysis_process
from ingest import run_ingest_process


class ObsidianToolsTkinterGUI:
    """Tkinter-based GUI for Obsidian Tools."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Obsidian Tools")
        self.root.geometry("1000x700")
        
        # Initialize variables
        self.session = None
        self.api_url = None
        self.gemini_api_key = None
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        self.setup_ui()
        self.connect_to_obsidian()
    
    def setup_ui(self):
        """Set up the user interface."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Header
        header_label = ttk.Label(main_frame, text="Obsidian Tools", 
                                font=('Arial', 20, 'bold'))
        header_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Status bar
        self.status_var = tk.StringVar(value="Connecting to Obsidian...")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, 
                                foreground='blue')
        status_label.grid(row=1, column=0, columnspan=2, pady=(0, 20))
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create tabs
        self.create_analyze_tab()
        self.create_ingest_tab()
        
        # Progress area
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(20, 0))
        progress_frame.columnconfigure(0, weight=1)
        
        # Progress bar
        self.progress_var = tk.StringVar()
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Log output
        self.log_text = scrolledtext.ScrolledText(progress_frame, height=8, 
                                                 font=('Consolas', 9))
        self.log_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def create_analyze_tab(self):
        """Create the vault analysis tab."""
        analyze_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(analyze_frame, text="Analyze Vault")
        
        # Analysis parameters
        params_frame = ttk.LabelFrame(analyze_frame, text="Analysis Parameters", padding="10")
        params_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        params_frame.columnconfigure(1, weight=1)
        
        # Output file
        ttk.Label(params_frame, text="Output File:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.output_file_var = tk.StringVar(value="recommendations.md")
        output_file_entry = ttk.Entry(params_frame, textvariable=self.output_file_var)
        output_file_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        # Hub threshold
        ttk.Label(params_frame, text="Hub Threshold:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.hub_threshold_var = tk.IntVar(value=10)
        hub_threshold_spin = ttk.Spinbox(params_frame, from_=1, to=100, 
                                        textvariable=self.hub_threshold_var)
        hub_threshold_spin.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Link density threshold
        ttk.Label(params_frame, text="Link Density Threshold:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.link_density_var = tk.DoubleVar(value=0.02)
        link_density_spin = ttk.Spinbox(params_frame, from_=0.001, to=1.0, 
                                       increment=0.001, textvariable=self.link_density_var)
        link_density_spin.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Min word count
        ttk.Label(params_frame, text="Min Word Count:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.min_word_count_var = tk.IntVar(value=50)
        min_word_count_spin = ttk.Spinbox(params_frame, from_=10, to=1000, 
                                         textvariable=self.min_word_count_var)
        min_word_count_spin.grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Analysis button
        self.analyze_button = ttk.Button(analyze_frame, text="Analyze Vault", 
                                        command=self.run_analysis)
        self.analyze_button.grid(row=1, column=0, pady=20)
        
        # Results area
        results_frame = ttk.LabelFrame(analyze_frame, text="Analysis Results", padding="10")
        results_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(20, 0))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        analyze_frame.rowconfigure(2, weight=1)
        
        self.results_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD)
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def create_ingest_tab(self):
        """Create the document ingestion tab."""
        ingest_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(ingest_frame, text="Ingest Documents")
        
        # Folder configuration
        folders_frame = ttk.LabelFrame(ingest_frame, text="Folder Configuration", padding="10")
        folders_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        folders_frame.columnconfigure(1, weight=1)
        
        # Ingest folder
        ttk.Label(folders_frame, text="Ingest Folder:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ingest_folder_frame = ttk.Frame(folders_frame)
        ingest_folder_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        ingest_folder_frame.columnconfigure(0, weight=1)
        
        self.ingest_folder_var = tk.StringVar(value="ingest")
        ingest_folder_entry = ttk.Entry(ingest_folder_frame, textvariable=self.ingest_folder_var)
        ingest_folder_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        ingest_folder_button = ttk.Button(ingest_folder_frame, text="Browse...", 
                                         command=self.select_ingest_folder)
        ingest_folder_button.grid(row=0, column=1, padx=(10, 0))
        
        # Notes folder
        ttk.Label(folders_frame, text="Notes Folder:").grid(row=1, column=0, sticky=tk.W, pady=5)
        notes_folder_frame = ttk.Frame(folders_frame)
        notes_folder_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        notes_folder_frame.columnconfigure(0, weight=1)
        
        self.notes_folder_var = tk.StringVar(value="Inbox/Generated")
        notes_folder_entry = ttk.Entry(notes_folder_frame, textvariable=self.notes_folder_var)
        notes_folder_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        notes_folder_button = ttk.Button(notes_folder_frame, text="Browse...", 
                                        command=self.select_notes_folder)
        notes_folder_button.grid(row=0, column=1, padx=(10, 0))
        
        # Ingestion options
        options_frame = ttk.LabelFrame(ingest_frame, text="Ingestion Options", padding="10")
        options_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        
        self.delete_files_var = tk.BooleanVar(value=True)
        delete_files_check = ttk.Checkbutton(options_frame, 
                                            text="Delete source files after successful ingestion",
                                            variable=self.delete_files_var)
        delete_files_check.grid(row=0, column=0, sticky=tk.W)
        
        # Ingestion button
        self.ingest_button = ttk.Button(ingest_frame, text="Start Ingestion", 
                                       command=self.run_ingestion)
        self.ingest_button.grid(row=2, column=0, pady=20)
        
        # File list
        files_frame = ttk.LabelFrame(ingest_frame, text="Files in Ingest Folder", padding="10")
        files_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(20, 0))
        files_frame.columnconfigure(0, weight=1)
        files_frame.rowconfigure(0, weight=1)
        ingest_frame.rowconfigure(3, weight=1)
        
        self.files_text = scrolledtext.ScrolledText(files_frame, height=8, wrap=tk.WORD)
        self.files_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        refresh_button = ttk.Button(files_frame, text="Refresh File List", 
                                   command=self.refresh_file_list)
        refresh_button.grid(row=1, column=0, pady=(10, 0))
    
    def connect_to_obsidian(self):
        """Connect to Obsidian and load configuration."""
        try:
            # Load configuration
            self.api_url, obsidian_api_key, self.gemini_api_key, default_notes_folder = load_config()
            
            # Create API session
            self.session = create_api_session(obsidian_api_key)
            
            # Verify connection
            verify_connection(self.session, self.api_url, 10)
            
            # Update UI
            self.status_var.set("Connected to Obsidian")
            
            # Set default notes folder
            self.notes_folder_var.set(default_notes_folder)
            
            # Refresh file list
            self.refresh_file_list()
            
        except Exception as e:
            self.status_var.set(f"Connection failed: {str(e)}")
            self.log_message(f"Error: {str(e)}")
    
    def select_ingest_folder(self):
        """Open folder dialog to select ingest folder."""
        folder = filedialog.askdirectory(title="Select Ingest Folder")
        if folder:
            self.ingest_folder_var.set(folder)
            self.refresh_file_list()
    
    def select_notes_folder(self):
        """Open folder dialog to select notes folder."""
        folder = filedialog.askdirectory(title="Select Notes Folder")
        if folder:
            self.notes_folder_var.set(folder)
    
    def refresh_file_list(self):
        """Refresh the list of files in the ingest folder."""
        ingest_folder = self.ingest_folder_var.get()
        if not ingest_folder or not os.path.isdir(ingest_folder):
            self.files_text.delete(1.0, tk.END)
            self.files_text.insert(1.0, "Folder not found or invalid")
            return
        
        try:
            files = []
            for filename in os.listdir(ingest_folder):
                file_path = os.path.join(ingest_folder, filename)
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path)
                    files.append(f"{filename} ({size} bytes)")
            
            self.files_text.delete(1.0, tk.END)
            if files:
                self.files_text.insert(1.0, "\n".join(files))
            else:
                self.files_text.insert(1.0, "No files found in ingest folder")
        except Exception as e:
            self.files_text.delete(1.0, tk.END)
            self.files_text.insert(1.0, f"Error reading folder: {str(e)}")
    
    def run_analysis(self):
        """Run the vault analysis."""
        if not self.session:
            messagebox.showerror("Error", "Not connected to Obsidian")
            return
        
        # Disable button and show progress
        self.analyze_button.config(state='disabled')
        self.progress_bar.start()
        
        # Clear previous results
        self.results_text.delete(1.0, tk.END)
        self.log_text.delete(1.0, tk.END)
        
        # Run analysis in separate thread
        thread = threading.Thread(target=self._run_analysis_thread)
        thread.daemon = True
        thread.start()
    
    def _run_analysis_thread(self):
        """Run analysis in background thread."""
        try:
            # Redirect logging to our log output
            class LogHandler(logging.Handler):
                def __init__(self, text_widget):
                    super().__init__()
                    self.text_widget = text_widget
                
                def emit(self, record):
                    msg = self.format(record)
                    self.text_widget.insert(tk.END, msg + "\n")
                    self.text_widget.see(tk.END)
            
            # Set up logging
            handler = LogHandler(self.log_text)
            handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
            logging.getLogger().addHandler(handler)
            logging.getLogger().setLevel(logging.INFO)
            
            # Run the analysis
            run_analysis_process(
                self.session, self.api_url, 10,
                self.output_file_var.get(),
                self.hub_threshold_var.get(),
                self.link_density_var.get(),
                self.min_word_count_var.get()
            )
            
            # Read and display results
            with open(self.output_file_var.get(), 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Update UI in main thread
            self.root.after(0, lambda: self._analysis_completed(content))
            
        except Exception as e:
            # Update UI in main thread
            self.root.after(0, lambda: self._analysis_error(str(e)))
        finally:
            # Clean up logging handler
            logging.getLogger().removeHandler(handler)
    
    def _analysis_completed(self, content):
        """Handle analysis completion in main thread."""
        self.progress_bar.stop()
        self.analyze_button.config(state='normal')
        
        # Display results
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(1.0, content)
        
        # Show completion message
        messagebox.showinfo("Analysis Complete", 
                           f"Analysis completed successfully!\nResults saved to: {self.output_file_var.get()}")
        
        self.log_message("Analysis completed successfully!")
    
    def _analysis_error(self, error_msg):
        """Handle analysis error in main thread."""
        self.progress_bar.stop()
        self.analyze_button.config(state='normal')
        
        messagebox.showerror("Analysis Error", f"Analysis failed: {error_msg}")
        self.log_message(f"Error: {error_msg}")
    
    def run_ingestion(self):
        """Run the document ingestion."""
        if not self.session:
            messagebox.showerror("Error", "Not connected to Obsidian")
            return
        
        if not self.gemini_api_key:
            messagebox.showerror("Error", "Gemini API key not configured")
            return
        
        # Validate folders
        ingest_folder = self.ingest_folder_var.get()
        notes_folder = self.notes_folder_var.get()
        
        if not os.path.isdir(ingest_folder):
            messagebox.showerror("Error", f"Ingest folder not found: {ingest_folder}")
            return
        
        # Disable button and show progress
        self.ingest_button.config(state='disabled')
        self.progress_bar.start()
        
        # Clear log
        self.log_text.delete(1.0, tk.END)
        
        # Run ingestion in separate thread
        thread = threading.Thread(target=self._run_ingestion_thread)
        thread.daemon = True
        thread.start()
    
    def _run_ingestion_thread(self):
        """Run ingestion in background thread."""
        try:
            # Redirect logging to our log output
            class LogHandler(logging.Handler):
                def __init__(self, text_widget):
                    super().__init__()
                    self.text_widget = text_widget
                
                def emit(self, record):
                    msg = self.format(record)
                    self.text_widget.insert(tk.END, msg + "\n")
                    self.text_widget.see(tk.END)
            
            # Set up logging
            handler = LogHandler(self.log_text)
            handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
            logging.getLogger().addHandler(handler)
            logging.getLogger().setLevel(logging.INFO)
            
            # Run the ingestion
            run_ingest_process(
                self.ingest_folder_var.get(), self.notes_folder_var.get(),
                self.session, self.api_url, self.gemini_api_key, 10,
                self.delete_files_var.get()
            )
            
            # Update UI in main thread
            self.root.after(0, self._ingestion_completed)
            
        except Exception as e:
            # Update UI in main thread
            self.root.after(0, lambda: self._ingestion_error(str(e)))
        finally:
            # Clean up logging handler
            logging.getLogger().removeHandler(handler)
    
    def _ingestion_completed(self):
        """Handle ingestion completion in main thread."""
        self.progress_bar.stop()
        self.ingest_button.config(state='normal')
        
        # Refresh file list
        self.refresh_file_list()
        
        # Show completion message
        messagebox.showinfo("Ingestion Complete", "Document ingestion completed successfully!")
        
        self.log_message("Ingestion completed successfully!")
    
    def _ingestion_error(self, error_msg):
        """Handle ingestion error in main thread."""
        self.progress_bar.stop()
        self.ingest_button.config(state='normal')
        
        messagebox.showerror("Ingestion Error", f"Ingestion failed: {error_msg}")
        self.log_message(f"Error: {error_msg}")
    
    def log_message(self, message):
        """Add a message to the log output."""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)


def main():
    """Main function to run the GUI application."""
    root = tk.Tk()
    app = ObsidianToolsTkinterGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
