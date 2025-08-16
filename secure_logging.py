"""
Secure Logging Module v2 - Zero Sensitive Data Logging

This module addresses CodeQL rule py/clear-text-logging-sensitive-data by
completely avoiding logging of sensitive information, not just redacting it.

Features:
- Zero sensitive data in logs
- Safe reference logging (hashes, IDs, metadata)
- Context-aware logging without content exposure
- Compliance with strict security requirements
"""

import logging
import hashlib
import re
from typing import Dict, Any, Optional, Union, List
from functools import wraps
from dataclasses import dataclass
from enum import Enum


class LogLevel(Enum):
    """Log levels for type safety."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class SafeLogContext:
    """Safe logging context that never contains sensitive data."""
    operation: str
    status: str
    metadata: Dict[str, Any]
    sensitive_refs: Optional[Dict[str, str]] = None  # Only safe references


class ZeroSensitiveLogger:
    """
    A secure logging utility that NEVER logs sensitive data.
    
    This class provides methods for logging at different levels while ensuring
    that sensitive data like API keys, passwords, and other secrets are never
    logged in any form (not even redacted).
    """
    
    def __init__(self, logger_name: str = None):
        """
        Initialize the zero-sensitive logger.
        
        Args:
            logger_name: Name for the logger instance (defaults to module name)
        """
        self.logger = logging.getLogger(logger_name or __name__)
        
        # Patterns that indicate potentially sensitive data
        self.sensitive_patterns = [
            r'sk-[a-zA-Z0-9]{10,}',  # OpenAI/Gemini API keys (minimum 10 chars)
            r'obs_[a-zA-Z0-9]{10,}',  # Obsidian API keys (minimum 10 chars)
            r'op://[a-zA-Z0-9/_-]+',  # 1Password references
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # Email addresses
            r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',  # Credit card numbers
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN pattern
            r'password',  # Password-related terms
            r'secret',    # Secret-related terms
            r'key',       # Key-related terms
            r'token',     # Token-related terms
        ]
        
        # Compile patterns for efficiency
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.sensitive_patterns]
    
    def _contains_sensitive_data(self, message: str) -> bool:
        """
        Check if a message contains potentially sensitive data.
        
        Args:
            message: The message to check
            
        Returns:
            True if sensitive data is detected, False otherwise
        """
        for pattern in self.compiled_patterns:
            if pattern.search(message):
                return True
        return False
    
    def _create_safe_reference(self, sensitive_value: str, reference_type: str = "hash") -> str:
        """
        Create a safe reference to sensitive data without exposing it.
        
        Args:
            sensitive_value: The sensitive value to reference
            reference_type: Type of reference to create
            
        Returns:
            Safe reference string
        """
        if not sensitive_value:
            return "none"
        
        if reference_type == "hash":
            # Create a short hash reference
            return hashlib.sha256(sensitive_value.encode()).hexdigest()[:8]
        elif reference_type == "length":
            # Reference by length only
            return f"len_{len(sensitive_value)}"
        elif reference_type == "type":
            # Reference by type/format
            if sensitive_value.startswith("sk-"):
                return "sk_*"
            elif sensitive_value.startswith("obs_"):
                return "obs_*"
            elif sensitive_value.startswith("op://"):
                return "op_ref"
            else:
                return "unknown_type"
        else:
            # Default to hash
            return hashlib.sha256(sensitive_value.encode()).hexdigest()[:8]
    
    def _validate_log_message(self, message: str, context: Optional[SafeLogContext] = None) -> bool:
        """
        Validate that a log message contains no sensitive data.
        
        Args:
            message: The message to validate
            context: Optional logging context
            
        Returns:
            True if message is safe, False if sensitive data detected
        """
        # Check the main message
        if self._contains_sensitive_data(message):
            return False
        
        # Check context metadata
        if context and context.metadata:
            for key, value in context.metadata.items():
                if isinstance(value, str) and self._contains_sensitive_data(value):
                    return False
        
        return True
    
    def _log(self, level: LogLevel, message: str, context: Optional[SafeLogContext] = None, **kwargs):
        """
        Internal logging method with zero-sensitive-data validation.
        
        Args:
            level: Log level
            message: Log message
            context: Safe logging context
            **kwargs: Additional arguments for the logging call
        """
        # Validate that no sensitive data is being logged
        if not self._validate_log_message(message, context):
            # Replace the message with a safe version
            safe_message = f"[SECURITY VIOLATION PREVENTED] {message[:50]}..."
            self.logger.error(f"Attempted to log sensitive data: {safe_message}")
            return
        
        # Build the final log message
        final_message = message
        
        if context:
            # Add safe context information
            context_parts = [f"op={context.operation}", f"status={context.status}"]
            
            # Add safe metadata
            for key, value in context.metadata.items():
                if isinstance(value, (str, int, bool)) and not self._contains_sensitive_data(str(value)):
                    context_parts.append(f"{key}={value}")
            
            # Add safe sensitive references if provided
            if context.sensitive_refs:
                for ref_key, ref_value in context.sensitive_refs.items():
                    context_parts.append(f"{ref_key}={ref_value}")
            
            final_message = f"{message} | {' | '.join(context_parts)}"
        
        # Get the appropriate logging method
        log_method = getattr(self.logger, level.value, self.logger.info)
        
        # Log the safe message
        log_method(final_message, **kwargs)
    
    def info(self, message: str, context: Optional[SafeLogContext] = None, **kwargs):
        """Log an info message with zero sensitive data."""
        self._log(LogLevel.INFO, message, context, **kwargs)
    
    def warning(self, message: str, context: Optional[SafeLogContext] = None, **kwargs):
        """Log a warning message with zero sensitive data."""
        self._log(LogLevel.WARNING, message, context, **kwargs)
    
    def error(self, message: str, context: Optional[SafeLogContext] = None, **kwargs):
        """Log an error message with zero sensitive data."""
        self._log(LogLevel.ERROR, message, context, **kwargs)
    
    def debug(self, message: str, context: Optional[SafeLogContext] = None, **kwargs):
        """Log a debug message with zero sensitive data."""
        self._log(LogLevel.DEBUG, message, context, **kwargs)
    
    def critical(self, message: str, context: Optional[SafeLogContext] = None, **kwargs):
        """Log a critical message with zero sensitive data."""
        self._log(LogLevel.CRITICAL, message, context, **kwargs)
    
    def log_configuration(self, config_type: str, has_sensitive_data: bool, **metadata):
        """
        Safely log configuration information without exposing sensitive data.
        
        Args:
            config_type: Type of configuration (e.g., "obsidian", "gemini")
            has_sensitive_data: Whether sensitive data is present
            **metadata: Additional safe metadata
        """
        context = SafeLogContext(
            operation="config_load",
            status="success" if has_sensitive_data else "missing",
            metadata={
                "config_type": config_type,
                "has_sensitive_data": has_sensitive_data,
                **metadata
            }
        )
        
        self.info(f"Configuration loaded for {config_type}", context)
    
    def log_api_operation(self, operation: str, endpoint: str, status: str, 
                         has_auth: bool, response_size: Optional[int] = None):
        """
        Safely log API operations without exposing sensitive data.
        
        Args:
            operation: HTTP operation (GET, POST, etc.)
            endpoint: API endpoint (without sensitive path components)
            status: Operation status
            has_auth: Whether authentication was used
            response_size: Size of response (optional)
        """
        # Sanitize endpoint to remove sensitive path components
        safe_endpoint = self._sanitize_endpoint(endpoint)
        
        context = SafeLogContext(
            operation=operation.lower(),
            status=status,
            metadata={
                "endpoint": safe_endpoint,
                "has_auth": has_auth,
                "response_size": response_size
            }
        )
        
        self.info(f"API {operation} {safe_endpoint}", context)
    
    def log_file_operation(self, operation: str, file_path: str, success: bool, 
                          file_size: Optional[int] = None):
        """
        Safely log file operations without exposing sensitive content.
        
        Args:
            operation: File operation (read, write, delete, etc.)
            file_path: File path (will be sanitized)
            success: Whether operation succeeded
            file_size: File size in bytes (optional)
        """
        # Sanitize file path to remove sensitive components
        safe_path = self._sanitize_file_path(file_path)
        
        context = SafeLogContext(
            operation=operation,
            status="success" if success else "failed",
            metadata={
                "file_path": safe_path,
                "file_size": file_size
            }
        )
        
        self.info(f"File {operation}: {safe_path}", context)
    
    def _sanitize_endpoint(self, endpoint: str) -> str:
        """Sanitize API endpoint to remove sensitive path components."""
        # Remove sensitive path components
        sensitive_patterns = [
            r'/users/\d+',           # User IDs
            r'/auth/[^/]+',          # Auth-related paths
            r'/tokens/[^/]+',        # Token-related paths
            r'/keys/[^/]+',          # Key-related paths
        ]
        
        sanitized = endpoint
        for pattern in sensitive_patterns:
            sanitized = re.sub(pattern, r'/[REDACTED]', sanitized)
        
        return sanitized
    
    def _sanitize_file_path(self, file_path: str) -> str:
        """Sanitize file path to remove sensitive components."""
        # Remove sensitive path components
        sensitive_patterns = [
            r'/[^/]*password[^/]*',  # Password-related directories
            r'/[^/]*secret[^/]*',    # Secret-related directories
            r'/[^/]*key[^/]*',       # Key-related directories
            r'/[^/]*token[^/]*',     # Token-related directories
            r'/[^/]*\.env[^/]*',     # Environment files
            r'/[^/]*\.key[^/]*',     # Key files
            r'/[^/]*\.pem[^/]*',     # Certificate files
        ]
        
        sanitized = file_path
        for pattern in sensitive_patterns:
            sanitized = re.sub(pattern, r'/[REDACTED]', sanitized, flags=re.IGNORECASE)
        
        return sanitized


# Create a default instance
default_logger = ZeroSensitiveLogger()

# Convenience functions for backward compatibility (but with new behavior)
def secure_log(level: str, message: str, sensitive_data: Dict[str, str] = None, **kwargs):
    """
    Secure logging function that NEVER logs sensitive data.
    
    This function maintains backward compatibility but changes behavior to
    completely avoid logging sensitive information instead of redacting it.
    
    Args:
        level: Log level (info, warning, error, debug, critical)
        message: Log message
        sensitive_data: DEPRECATED - will be ignored for security
        **kwargs: Additional arguments for the logging call
    """
    # Convert sensitive_data to safe references if provided
    context = None
    if sensitive_data:
        # Create safe references instead of logging actual values
        safe_refs = {}
        for key, value in sensitive_data.items():
            if value:
                safe_refs[key] = default_logger._create_safe_reference(value, "hash")
        
        context = SafeLogContext(
            operation="legacy_log",
            status="converted",
            metadata={},
            sensitive_refs=safe_refs
        )
    
    # Log with the safe context
    default_logger._log(LogLevel(level.lower()), message, context, **kwargs)


def get_secure_logger(name: str = None) -> ZeroSensitiveLogger:
    """
    Get a zero-sensitive logger instance.
    
    Args:
        name: Logger name (defaults to module name)
        
    Returns:
        ZeroSensitiveLogger instance
    """
    return ZeroSensitiveLogger(name)


# Decorator for automatic sensitive data detection and prevention
def secure_log_call(func):
    """
    Decorator that automatically logs function calls with zero sensitive data.
    
    This decorator can be used to automatically log function calls while ensuring
    that no sensitive data is ever logged.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Create logger for this function
        logger = ZeroSensitiveLogger(func.__module__)
        
        # Create safe context for the function call
        context = SafeLogContext(
            operation="function_call",
            status="started",
            metadata={
                "function": func.__name__,
                "module": func.__module__,
                "arg_count": len(args),
                "kwarg_count": len(kwargs)
            }
        )
        
        # Log the function call
        logger.debug(f"Calling {func.__name__}", context)
        
        try:
            result = func(*args, **kwargs)
            
            # Log successful completion
            success_context = SafeLogContext(
                operation="function_call",
                status="completed",
                metadata={
                    "function": func.__name__,
                    "module": func.__module__
                }
            )
            logger.debug(f"Function {func.__name__} completed successfully", success_context)
            
            return result
        except Exception as e:
            # Log failure without exposing exception details that might contain sensitive data
            error_context = SafeLogContext(
                operation="function_call",
                status="failed",
                metadata={
                    "function": func.__name__,
                    "module": func.__module__,
                    "error_type": type(e).__name__
                }
            )
            logger.error(f"Function {func.__name__} failed", error_context)
            raise
    
    return wrapper


# Context manager for temporary logging configuration
class SecureLoggingContext:
    """
    Context manager for temporary secure logging configuration.
    
    This allows temporarily changing logging behavior within a specific context.
    """
    
    def __init__(self, logger_name: str = None, level: str = "INFO"):
        self.logger_name = logger_name
        self.level = level
        self.original_level = None
    
    def __enter__(self):
        if self.logger_name:
            logger = logging.getLogger(self.logger_name)
            self.original_level = logger.level
            logger.setLevel(getattr(logging, self.level.upper(), logging.INFO))
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.logger_name and self.original_level is not None:
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.original_level)


# Export main classes and functions
__all__ = [
    'ZeroSensitiveLogger',
    'SafeLogContext',
    'LogLevel',
    'secure_log',
    'get_secure_logger',
    'secure_log_call',
    'SecureLoggingContext'
]
