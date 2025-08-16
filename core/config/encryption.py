"""
Configuration encryption utilities for ObsidianTools.

This module handles encryption and decryption of sensitive
configuration data using Fernet encryption.
"""

import os
import json
import base64
from pathlib import Path
from typing import Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from secure_logging import ZeroSensitiveLogger, SafeLogContext


class ConfigEncryption:
    """Handles encryption and decryption of sensitive configuration data."""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.salt_file = config_dir / ".salt"
        self.logger = ZeroSensitiveLogger("config_encryption")
        self._ensure_salt_exists()
    
    def _ensure_salt_exists(self):
        """Generate a unique random salt if it doesn't exist"""
        if not self.salt_file.exists():
            # Generate a cryptographically secure random salt
            salt = os.urandom(32)  # 256-bit random salt
            # Store the salt in a hidden file
            with open(self.salt_file, 'wb') as f:
                f.write(salt)
            # Set restrictive permissions (owner read/write only)
            try:
                os.chmod(self.salt_file, 0o600)
            except OSError:
                pass  # Windows may not support chmod
        
        # Load the existing salt
        with open(self.salt_file, 'rb') as f:
            self.salt = f.read()
    
    def derive_key(self, master_password: str) -> bytes:
        """Derive encryption key from master password using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=600000,  # Increased from default for better security
        )
        return base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
    
    def encrypt_secrets(self, secrets: Dict[str, Any], master_password: str) -> bytes:
        """Encrypt sensitive configuration data."""
        try:
            key = self.derive_key(master_password)
            f = Fernet(key)
            return f.encrypt(json.dumps(secrets).encode())
        except Exception as e:
            self.logger.error("Encryption operation failed", SafeLogContext(
                operation="encryption",
                status="failed",
                metadata={"error_type": type(e).__name__, "operation": "encrypt"}
            ))
            raise
    
    def decrypt_secrets(self, encrypted_data: bytes, master_password: str) -> Dict[str, Any]:
        """Decrypt sensitive configuration data."""
        try:
            key = self.derive_key(master_password)
            f = Fernet(key)
            decrypted = f.decrypt(encrypted_data)
            return json.loads(decrypted.decode())
        except Exception as e:
            self.logger.error("Decryption operation failed", SafeLogContext(
                operation="decryption",
                status="failed",
                metadata={"error_type": type(e).__name__, "operation": "decrypt"}
            ))
            raise
