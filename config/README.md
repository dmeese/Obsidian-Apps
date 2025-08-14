# Configuration Management System

This directory contains the configuration files for Obsidian Tools. The system supports both local encrypted storage and 1Password integration for secure secret management.

## 🔐 Security Methods

### 1. Local Encrypted Storage (Default)
- **Master Password**: You set a master password to encrypt sensitive data
- **Encryption**: Uses AES-256-GCM encryption with PBKDF2 key derivation
- **Storage**: Sensitive data stored locally in encrypted `secrets.encrypted` file
- **Benefits**: Works offline, no external dependencies, full control

### 2. 1Password Integration
- **References**: Store 1Password references (e.g., `op://vault/item/field`)
- **CLI Required**: Requires 1Password CLI (`op`) to be installed
- **Benefits**: Enterprise-grade secret management, centralized access control

## 📁 File Structure

```
config/
├── config.json              # Non-sensitive configuration (git-tracked)
├── secrets.encrypted        # Encrypted sensitive data (git-ignored)
├── config.example.json      # Example configuration (git-tracked)
└── README.md               # This file (git-tracked)
```

## ⚙️ Configuration Options

### Connection Settings
- **Obsidian API URL**: Local REST API endpoint (default: `http://localhost:27123`)
- **API Timeout**: Request timeout in seconds (default: 30)
- **Default Notes Folder**: Where generated notes are stored (default: `GeneratedNotes`)

### Gemini Settings
- **Default Model**: LLM model for document processing
  - `gemini-2.5-flash` (faster, more capable)
  - `gemini-2.5-flash-lite` (lighter, potentially faster)
- **Timeout**: Gemini API timeout in seconds (default: 60)

### Ingest Settings
- **Default Ingest Folder**: Source documents folder (default: `ingest`)
- **Delete After Ingestion**: Automatically remove processed files (default: true)

## 🚀 Getting Started

### First-Time Setup
1. **Launch the GUI** and go to the Configuration tab
2. **Choose Security Method**:
   - Local Encrypted: Set a master password
   - 1Password: Enter your 1Password references
3. **Configure Settings**: Fill in connection details and preferences
4. **Save Configuration**: Click "Save Configuration" button
5. **Test Connection**: Verify your Obsidian API connection

### Using 1Password
1. **Install 1Password CLI**: Download from [1Password Developer Portal](https://developer.1password.com/docs/cli/)
2. **Sign In**: Run `op signin` in your terminal
3. **Get References**: Use `op item get --format=json` to find references
4. **Enter References**: Use format `op://vault/item/field`

## 🔄 Configuration Management

### Export Configuration
- **Without Secrets**: Safe to share, contains only non-sensitive settings
- **With Secrets**: Includes encrypted sensitive data (requires master password)

### Import Configuration
- **Backup/Restore**: Move configuration between machines
- **Team Sharing**: Share configuration templates with team members
- **Migration**: Import from existing `.env` files

### Migration from .env Files
The system can automatically migrate from existing `.env` files:
- Detects 1Password references
- Sets appropriate security method
- Preserves existing settings

## 🛡️ Security Features

### Encryption Details
- **Algorithm**: AES-256-GCM (Galois/Counter Mode)
- **Key Derivation**: PBKDF2 with 100,000 iterations
- **Salt**: Fixed salt for consistent key derivation
- **Memory Safety**: Secrets decrypted only when needed

### Best Practices
- **Strong Master Password**: Use a strong, unique password
- **Regular Updates**: Update API keys and references regularly
- **Backup Security**: Secure your exported configuration files
- **Access Control**: Limit access to configuration directory

## 🚨 Troubleshooting

### Common Issues
1. **"Master password required"**: Set a master password for local storage
2. **"1Password CLI not found"**: Install and configure 1Password CLI
3. **"Connection test failed"**: Verify Obsidian API URL and key
4. **"Configuration validation failed"**: Check required fields

### Reset Configuration
To reset to defaults:
1. Delete `config.json` and `secrets.encrypted`
2. Restart the application
3. Reconfigure from scratch

## 📋 Example Configuration

See `config.example.json` for a complete example configuration with all available options and their default values.

## 🔗 Integration

The configuration system integrates with:
- **GUI**: Configuration tab for easy management
- **Analysis**: Uses configured Obsidian settings
- **Ingest**: Uses configured Gemini settings and defaults
- **CLI**: Compatible with existing command-line tools

## 📞 Support

For configuration issues:
1. Check the GUI status messages
2. Review the application logs
3. Verify file permissions and paths
4. Test with the configuration test script: `python test_config.py`
