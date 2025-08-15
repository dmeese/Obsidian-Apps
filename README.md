# Obsidian Tools

A comprehensive Python toolkit for managing and growing your Obsidian vault with advanced analysis, intelligent document ingestion, and a modern graphical interface.

## Overview

This project provides multiple tools for Obsidian vault management:

-   **Analyze Mode**: Analyzes the structure of your vault to find linking opportunities and structural issues.
-   **Ingest Mode**: Uses Google Gemini LLM to intelligently decompose documents into interconnected, Zettelkasten-style notes with automatic wikilinks.
-   **Graphical Interface**: Modern PyQt6-based GUI for easy interaction with all features.
-   **Configuration Management**: Secure hybrid approach for managing API keys and settings.

## Features

### Core Functionality
- Connects to a running Obsidian instance via the **Local REST API** plugin.
- Securely fetches API keys from **1Password** using its CLI or local encrypted storage.
- Builds a complete graph of all notes and their `[[wikilinks]]`.
- Generates comprehensive reports identifying:
  - **Orphan Notes**: Notes that have no incoming links.
  - **Hub Notes**: Highly-connected notes that serve as entry points to topics.
  - **Dead-End Notes**: Notes that have incoming links but no outbound links.
  - **Low-Density Notes**: Notes that may be information silos, with few links for their size.
  - **Untapped Potential**: Unlinked mentions of other note titles.
  - **Stub Links**: Links that point to notes that do not yet exist.

### Advanced Document Ingestion
- **Intelligent Decomposition**: Uses Google Gemini LLM to break down documents into meaningful, interconnected notes.
- **Automatic Connectivity**: Creates `[[wikilinks]]` between related concepts within the same document.
- **Note Types**: Generates both "atomic" notes (single concepts) and "structure" notes (hubs/MOCs).
- **Multiple Formats**: Supports `.txt`, `.pdf`, `.md`, and `.json` files.
- **Model Selection**: Choose between `gemini-2.5-flash` and `gemini-2.5-flash-lite` for different performance needs.
- **File Management**: Option to automatically delete source files after successful processing.

### Modern User Interface
- **PyQt6 GUI**: Professional, responsive interface with tabbed design.
- **Real-time Status**: Live connection status and progress indicators.
- **Configuration Tab**: Easy management of all settings and API keys.
- **Responsive Design**: Adapts to different window sizes and screen resolutions.
- **Input Validation**: Real-time validation and error handling.

## Setup

This toolkit has several prerequisites for connecting to your vault and securely managing credentials.

### 1. Install Python Dependencies

It is recommended to use a virtual environment.

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
pip install -r requirements.txt
```

### 2. 1Password CLI (Optional but Recommended)

For enhanced security, you can use the [1Password CLI](https://developer.1password.com/docs/cli/get-started/) to securely fetch your API keys. You must have it installed and configured on your system.

You can test your setup by running `op account list`.

### 3. API Keys

The following API keys are required:

- **Obsidian API Key**: For connecting to your vault via the Local REST API plugin
- **Google Gemini API Key**: For the intelligent document ingestion feature

### 4. Obsidian Local REST API Plugin

You must have the "Local REST API" community plugin installed and enabled in Obsidian.

### 5. Configuration Setup

The toolkit uses a hybrid approach for secure configuration management:

#### Option A: 1Password Integration (Recommended)
1. In your 1Password vault, create items for your API keys
2. Copy the Secret References (e.g., `op://<vault>/<item>/<field>`)
3. Use the GUI Configuration tab to enter these references

#### Option B: Local Encrypted Storage
1. Use the GUI Configuration tab to enter your API keys directly
2. Keys are encrypted using AES-256-GCM with PBKDF2 key derivation
3. A master password protects your encrypted configuration

### 6. Initial Configuration

1. Run the GUI: `python gui.py`
2. Go to the Configuration tab
3. Enter your Obsidian API URL (default: `http://127.0.0.1:27123`)
4. Choose your security method (1Password or local encrypted)
5. Enter your API keys or 1Password references
6. Save your configuration

## Usage

The toolkit can be used in multiple ways: command-line interface, graphical interface, or as a Python module.

### Command Line Interface

The traditional command-line interface operates in two modes: `analyze` and `ingest`.

#### Analyze Mode

To run the existing vault analysis:

```bash
python ObsidianAnalyzer.py analyze
```

Or, if you are using VS Code, simply open the project and press `F5` to run the debugger.

#### Ingest Mode

To process documents and create new notes:

```bash
python ObsidianAnalyzer.py ingest
```

**Note:** By default, files in the ingest folder are automatically deleted after successful processing. Use the `--keep-files` flag to preserve original files:

```bash
python ObsidianAnalyzer.py ingest --keep-files
```

**Model Selection:** Choose between different Gemini models for different performance needs:

```bash
python ObsidianAnalyzer.py ingest --model gemini-2.5-flash-lite
```

## Graphical User Interface

For a more user-friendly experience, you can use the modern graphical interface instead of the command line.

### PyQt6 GUI (Recommended)

The PyQt6 version provides a professional, responsive interface with advanced features:

```bash
python gui.py
```

### GUI Features

The PyQt6 GUI provides a comprehensive interface for all Obsidian Tools functionality:

#### Analysis Tab
- **Vault Analysis**: Run comprehensive vault structure analysis
- **Parameter Configuration**: Adjust analysis thresholds and settings
- **Results Display**: View analysis results directly in the interface
- **Export Options**: Save analysis reports to markdown files

#### Ingest Tab
- **Document Processing**: Process `.txt`, `.pdf`, `.md`, and `.json` files
- **Model Selection**: Choose between `gemini-2.5-flash` and `gemini-2.5-flash-lite`
- **Folder Management**: Browse dialogs for selecting input/output folders
- **File Operations**: View files in ingest folder, refresh listings, and manage processing
- **Progress Tracking**: Real-time progress indicators and detailed logging
- **File Cleanup**: Option to automatically delete source files after processing

#### Configuration Tab
- **Security Management**: Choose between 1Password integration or local encrypted storage
- **API Configuration**: Manage Obsidian and Gemini API settings
- **Connection Testing**: Test API connections and validate configuration
- **Status Monitoring**: Real-time connection status and configuration validation
- **Export/Import**: Backup and restore configuration settings

#### General Features
- **Responsive Design**: Adapts to different window sizes and screen resolutions
- **Real-time Status**: Live connection status and progress indicators
- **Input Validation**: Real-time validation and error handling
- **Modern UI**: Professional styling with light theme and intuitive navigation

### VS Code Integration

The project includes VS Code launch configurations for all options:
- Press `F5` and select "Run: GUI (PyQt6)" for the modern interface
- Select "Run: Ingest Documents" for command-line ingestion
- Select "Run: Ingest Documents (Keep Files)" to preserve source files

## Advanced Features

### Intelligent Document Ingestion

The ingest system uses advanced AI to create interconnected knowledge networks:

#### Note Types
- **Atomic Notes**: Focus on single, core concepts for maximum clarity and reusability
- **Structure Notes**: Serve as hubs or Maps of Content (MOCs) that organize related concepts

#### Automatic Connectivity
- **Wikilink Generation**: Creates `[[wikilinks]]` between related concepts within the same document
- **Wikilink Cleaning**: Automatically fixes malformed wikilinks (removes quotes, extra spaces) for Obsidian compatibility
- **Concept Mapping**: Identifies relationships and automatically links related notes
- **Knowledge Graph**: Builds a network of interconnected ideas in your vault

#### LLM Integration
- **Google Gemini**: Uses state-of-the-art language models for intelligent content analysis
- **Model Selection**: Choose between performance-optimized models based on your needs
- **Prompt Engineering**: Sophisticated prompts ensure high-quality, structured output

### Security Features

#### Hybrid Security Approach
- **1Password Integration**: Secure API key management using industry-standard password manager
- **Local Encryption**: AES-256-GCM encryption with PBKDF2 key derivation for local storage
- **Master Password Protection**: Additional layer of security for encrypted configurations
- **Git Security**: Sensitive files are automatically excluded from version control

#### Configuration Management
- **Centralized Settings**: All configuration managed through the GUI
- **Real-time Validation**: Immediate feedback on configuration errors
- **Connection Testing**: Verify API connections before processing
- **Export/Import**: Backup and restore configuration settings

## Project Structure

```
ObsidianTools/
├── ObsidianAnalyzer.py      # Main command-line entry point
├── analyzer.py              # Core vault analysis logic
├── ingest.py                # Document ingestion and LLM integration
├── gui.py                   # PyQt6 graphical user interface
├── config_manager.py        # Configuration and security management
├── utils.py                 # Utility functions
├── requirements.txt         # Python dependencies
├── config/                  # Configuration directory
│   ├── config.json         # User configuration (git-tracked)
│   ├── secrets.encrypted   # Encrypted secrets (git-ignored)
│   └── config.example.json # Example configuration
└── .gitignore              # Git ignore patterns
```

### Key Files

- **`ObsidianAnalyzer.py`**: Command-line interface for analysis and ingestion
- **`gui.py`**: Modern PyQt6-based graphical interface
- **`ingest.py`**: AI-powered document processing with automatic wikilink generation
- **`config_manager.py`**: Secure configuration management with encryption support
- **`analyzer.py`**: Vault structure analysis and reporting

## Ingestion Examples

### What the New System Creates

The updated ingestion system creates interconnected notes that form knowledge networks:

#### Example: Processing a Research Paper

**Input**: A PDF about "Machine Learning in Healthcare"

**Output**: Multiple interconnected notes:

1. **Structure Note**: "Machine Learning in Healthcare"
   - Summary of the topic
   - Links to: [[Supervised Learning in Medical Diagnosis]], [[Data Privacy in Healthcare ML]], [[Ethical Considerations in AI Medicine]]

2. **Atomic Note**: "Supervised Learning in Medical Diagnosis"
   - Core concept explanation
   - Links to: [[Machine Learning in Healthcare]], [[Medical Data Types]], [[Diagnostic Accuracy Metrics]]

3. **Atomic Note**: "Data Privacy in Healthcare ML"
   - Privacy considerations
   - Links to: [[Machine Learning in Healthcare]], [[HIPAA Compliance]], [[Data Anonymization Techniques]]

#### Benefits

- **Automatic Connectivity**: Notes are linked from the start, not isolated
- **Knowledge Discovery**: Easy to navigate between related concepts
- **Scalable Structure**: As you add more documents, the network grows organically
- **Better Recall**: Interconnected notes improve memory and understanding

## Troubleshooting

### Common Issues

#### GUI Not Starting
- Ensure PyQt6 is installed: `pip install PyQt6`
- Check Python version compatibility (Python 3.8+ required)

#### Configuration Issues
- **1Password Errors**: Ensure 1Password CLI is installed and authenticated (`op signin`)
- **Connection Failures**: Verify Obsidian Local REST API plugin is enabled and running
- **API Key Issues**: Test connections using the Configuration tab's "Test Connection" button

#### Ingestion Problems
- **Empty Notes**: Check that source files contain readable text content
- **LLM Errors**: Verify Gemini API key is valid and has sufficient quota
- **File Deletion**: Use `--keep-files` flag if you want to preserve source documents
- **Wikilink Issues**: The system automatically cleans malformed wikilinks, but ensure your LLM prompt is clear about format requirements

### Getting Help

- Check the logs in the GUI for detailed error messages
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Ensure your Obsidian vault is accessible and the Local REST API plugin is configured

## What's New

### Recent Major Updates

#### 🚀 Enhanced Document Ingestion (Latest)
- **Automatic Wikilinks**: LLM now creates `[[wikilinks]]` between related concepts
- **Note Types**: Support for "atomic" and "structure" notes with intelligent categorization
- **Interconnected Knowledge**: Documents are decomposed into networks of linked notes
- **Advanced Prompting**: Sophisticated AI prompts for better note quality and connectivity

#### 🎨 Modern PyQt6 GUI
- **Professional Interface**: Modern, responsive design with tabbed layout
- **Configuration Management**: Integrated settings and security management
- **Real-time Status**: Live connection monitoring and progress tracking
- **Input Validation**: Immediate feedback and error handling

#### 🔐 Enhanced Security
- **Hybrid Approach**: Choose between 1Password integration or local encrypted storage
- **AES-256 Encryption**: Military-grade encryption for local secrets
- **PBKDF2 Key Derivation**: 600,000 iterations for enhanced security
- **Git Security**: Automatic exclusion of sensitive files from version control
- **Secure Logging**: Comprehensive redaction of sensitive information in all logs
- **No Clear Text Secrets**: API keys and passwords are never logged in plain text

For detailed security information, see [SECURITY.md](SECURITY.md).

#### ⚙️ Configuration System
- **Centralized Management**: All settings managed through the GUI
- **Migration Support**: Easy transition from existing `.env` files
- **Export/Import**: Backup and restore configuration settings
- **Connection Testing**: Validate API connections before processing

## Contributing

This project welcomes contributions! Areas for improvement include:
- Additional LLM model support
- Enhanced vault analysis algorithms
- GUI theme customization
- Plugin architecture for extensibility
- Performance optimizations for large vaults

## License

This project is open source. Please check the repository for license details.
