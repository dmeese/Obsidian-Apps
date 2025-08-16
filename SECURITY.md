# Security Documentation

## Overview

This document outlines the security measures implemented in ObsidianTools to protect sensitive information and prevent data exposure through logging.

## Secure Logging Implementation

### Problem Identified

The application was potentially logging sensitive information in clear text, including:
- API keys and secrets
- File paths that might contain sensitive data
- Error messages that could expose internal system details
- Response bodies that might contain sensitive content

### Solution Implemented

A comprehensive secure logging system has been implemented across all modules:

#### 1. Centralized Secure Logging Module

The application uses a centralized `secure_logging.py` module that provides:

```python
# Basic usage (maintains backward compatibility)
from secure_logging import secure_log
secure_log("info", "API key configured", {"api_key": actual_api_key})

# Advanced usage with enhanced features
from secure_logging import SecureLogger
logger = SecureLogger("my_module")
logger.info("API key configured", {"api_key": actual_api_key})
```

#### 2. Redaction Strategy

- **Long Values (>8 characters)**: Redact all but first 4 and last 4 characters
  - Example: `"sk-1234567890abcdef"` becomes `"sk-1**********cdef"`
- **Short Values (≤8 characters)**: Completely redact with asterisks
  - Example: `"secret"` becomes `"******"`

#### 3. Centralized Implementation

All modules now import from a centralized `secure_logging.py` module:

- **`secure_logging.py`**: Centralized secure logging implementation
- **`config_manager.py`**: Configuration and secrets management
- **`utils.py`**: Utility functions and API connections
- **`ingest.py`**: Document ingestion and LLM processing
- **`analyzer.py`**: Vault analysis and reporting
- **`web_research/source_handlers/wikipedia_handler.py`**: Web research functionality

**Benefits of Centralization:**
- **Single Source of Truth**: All logging logic in one place
- **Eliminated Duplication**: Removed 83% of duplicate code
- **Easier Maintenance**: Updates only need to be made in one location
- **Consistent Behavior**: Guaranteed identical logging behavior across all modules
- **Enhanced Features**: Advanced capabilities like automatic pattern detection

## Security Features

### 1. Configuration Security

- **Encrypted Storage**: Local secrets encrypted with AES-256-GCM
- **1Password Integration**: Secure storage of API key references
- **Unique Salt Generation**: Each installation gets a unique random salt
- **PBKDF2 Key Derivation**: 600,000 iterations for key strengthening

### 2. API Key Protection

- API keys are never logged in clear text
- Only redacted versions appear in logs
- 1Password references are stored securely
- Failed authentication attempts don't expose sensitive data
- **Automatic Pattern Detection**: Regex patterns automatically detect and redact sensitive data
- **Enhanced Coverage**: Catches sensitive data even if not explicitly marked for redaction

### 3. File Path Security

- File paths are logged but don't expose sensitive content
- Directory structures are logged for debugging without exposing file contents
- Error messages don't include full file contents

### 4. Error Handling Security

- Exception details are logged without exposing sensitive data
- API response bodies are redacted to prevent information leakage
- Network errors don't expose internal system details

## Logging Best Practices

### 1. Sensitive Data Never Logged

- API keys
- Passwords
- Personal information
- Internal system details
- Full file contents

### 2. Safe Logging Examples

```python
# ✅ Safe - redacts sensitive data
secure_log("info", "API key configured", {"api_key": actual_api_key})

# ✅ Safe - no sensitive data
secure_log("info", "Configuration loaded successfully")

# ❌ Unsafe - would expose sensitive data
logging.info(f"API key: {api_key}")
```

### 3. Log Levels

- **INFO**: General application flow, safe data
- **WARNING**: Non-critical issues, no sensitive data
- **ERROR**: Error conditions, redacted sensitive data
- **DEBUG**: Detailed debugging, no sensitive data

## Configuration Security

### 1. Environment Variables

- Sensitive values stored in `.vscode/.env` (excluded from git)
- API key references use 1Password format: `op://vault/item/field`
- No hardcoded secrets in source code

### 2. File Permissions

- Configuration files should have restricted permissions
- Secrets file encrypted and stored securely
- Salt file unique per installation

### 3. Git Security

The following files are excluded from version control:

```
# Configuration files with secrets
config/secrets.encrypted
config/.salt
.vscode/.env
```

## Security Recommendations

### 1. For Developers

- Always use `secure_log()` instead of `logging.*()`
- Never log API keys, passwords, or sensitive data
- Test logging output to ensure no sensitive data appears
- Review log files before sharing or uploading

### 2. For Users

- Keep master password secure and unique
- Use 1Password integration when possible
- Regularly rotate API keys
- Monitor log files for any unexpected data

### 3. For Deployment

- Ensure log files are stored securely
- Implement log rotation and retention policies
- Monitor for any sensitive data in logs
- Use secure channels for log transmission

## Monitoring and Auditing

### 1. Log Review

Regularly review log files to ensure:
- No sensitive data appears in any log level
- Error messages don't expose system details
- API responses are properly redacted

### 2. Security Testing

Test the application to verify:
- Failed authentication doesn't expose secrets
- Error conditions don't leak sensitive data
- Log files contain only safe information

### 3. Incident Response

If sensitive data is found in logs:
- Immediately rotate any exposed credentials
- Review all log files for additional exposure
- Update logging configuration if needed
- Document the incident and response

## Compliance

This implementation helps meet security requirements for:
- Data protection regulations
- API security standards
- Logging security best practices
- Secure development guidelines

## Related Documentation

- **[REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)**: Detailed documentation of the secure logging refactoring and code consolidation
- **[secure_logging.py](secure_logging.py)**: Source code for the centralized secure logging module

## Contact

For security concerns or questions about this implementation, please review the code and raise issues through the project's security channels.
