"""
Centralized Secure Logging Module

This module provides a secure logging function that redacts sensitive information
across all modules in the ObsidianTools application.

Features:
- Automatic redaction of sensitive data (API keys, passwords, etc.)
- Configurable redaction strategies
- Support for all standard logging levels
- Thread-safe logging operations
"""

import logging
import re
from typing import Dict, Any, Optional, Union
from functools import wraps


class SecureLogger:
    """
    A secure logging utility that automatically redacts sensitive information.
    
    This class provides methods for logging at different levels while ensuring
    that sensitive data like API keys, passwords, and other secrets are never
    exposed in clear text.
    """
    
    def __init__(self, logger_name: str = None):
        """
        Initialize the secure logger.
        
        Args:
            logger_name: Name for the logger instance (defaults to module name)
        """
        self.logger = logging.getLogger(logger_name or __name__)
        
        # Common patterns for sensitive data
        self.sensitive_patterns = [
            r'sk-[a-zA-Z0-9]{20,}',  # OpenAI/Gemini API keys
            r'obs_[a-zA-Z0-9]{16,}',  # Obsidian API keys
            r'op://[a-zA-Z0-9/_-]+',  # 1Password references
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # Email addresses
            r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',  # Credit card numbers
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN pattern
        ]
        
        # Compile patterns for efficiency
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.sensitive_patterns]
    
    def _redact_sensitive_data(self, message: str, explicit_sensitive_data: Dict[str, str] = None) -> str:
        """
        Redact sensitive information from a message.
        
        Args:
            message: The message to redact
            explicit_sensitive_data: Dict of known sensitive values to redact
            
        Returns:
            Redacted message with sensitive data masked
        """
        redacted_message = message
        
        # Redact explicitly provided sensitive data
        if explicit_sensitive_data:
            for key, value in explicit_sensitive_data.items():
                if value and isinstance(value, str):
                    redacted_message = self._redact_value(redacted_message, value)
        
        # Redact patterns found in the message
        for pattern in self.compiled_patterns:
            matches = pattern.findall(redacted_message)
            for match in matches:
                redacted_message = self._redact_value(redacted_message, match)
        
        return redacted_message
    
    def _redact_value(self, message: str, value: str) -> str:
        """
        Redact a specific value from a message.
        
        Args:
            message: The message containing the value
            value: The sensitive value to redact
            
        Returns:
            Message with the value redacted
        """
        if not value or len(value) < 3:
            return message
        
        if len(value) <= 8:
            # For short values, redact completely
            redacted_value = "*" * len(value)
        else:
            # For long values, show first 4 and last 4 characters
            redacted_value = value[:4] + "*" * (len(value) - 8) + value[-4:]
        
        return message.replace(value, redacted_value)
    
    def _log(self, level: str, message: str, sensitive_data: Dict[str, str] = None, **kwargs):
        """
        Internal logging method with redaction.
        
        Args:
            level: Log level (info, warning, error, debug)
            message: Log message
            sensitive_data: Dict of sensitive values to redact
            **kwargs: Additional arguments for the logging call
        """
        # Redact sensitive information
        redacted_message = self._redact_sensitive_data(message, sensitive_data)
        
        # Get the appropriate logging method
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        
        # Log the redacted message
        log_method(redacted_message, **kwargs)
    
    def info(self, message: str, sensitive_data: Dict[str, str] = None, **kwargs):
        """Log an info message with sensitive data redaction."""
        self._log("info", message, sensitive_data, **kwargs)
    
    def warning(self, message: str, sensitive_data: Dict[str, str] = None, **kwargs):
        """Log a warning message with sensitive data redaction."""
        self._log("warning", message, sensitive_data, **kwargs)
    
    def error(self, message: str, sensitive_data: Dict[str, str] = None, **kwargs):
        """Log an error message with sensitive data redaction."""
        self._log("error", message, sensitive_data, **kwargs)
    
    def debug(self, message: str, sensitive_data: Dict[str, str] = None, **kwargs):
        """Log a debug message with sensitive data redaction."""
        self._log("debug", message, sensitive_data, **kwargs)
    
    def critical(self, message: str, sensitive_data: Dict[str, str] = None, **kwargs):
        """Log a critical message with sensitive data redaction."""
        self._log("critical", message, sensitive_data, **kwargs)


# Create a default instance for backward compatibility
default_logger = SecureLogger()

# Convenience functions for backward compatibility
def secure_log(level: str, message: str, sensitive_data: Dict[str, str] = None, **kwargs):
    """
    Secure logging function that redacts sensitive information.
    
    This is a convenience function that maintains backward compatibility
    with existing code. For new code, consider using SecureLogger directly.
    
    Args:
        level: Log level (info, warning, error, debug, critical)
        message: Log message
        sensitive_data: Dict of sensitive values to redact
        **kwargs: Additional arguments for the logging call
    """
    default_logger._log(level, message, sensitive_data, **kwargs)


def get_secure_logger(name: str = None) -> SecureLogger:
    """
    Get a secure logger instance.
    
    Args:
        name: Logger name (defaults to module name)
        
    Returns:
        SecureLogger instance
    """
    return SecureLogger(name)


# Decorator for automatic sensitive data detection
def secure_log_call(func):
    """
    Decorator that automatically logs function calls with sensitive data detection.
    
    This decorator can be used to automatically log function calls and detect
    potential sensitive data in arguments.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Create logger for this function
        logger = SecureLogger(func.__module__)
        
        # Log the function call
        logger.debug(f"Calling {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Function {func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Function {func.__name__} failed: {e}")
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
    'SecureLogger',
    'secure_log',
    'get_secure_logger',
    'secure_log_call',
    'SecureLoggingContext'
]
