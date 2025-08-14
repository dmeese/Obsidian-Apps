import json
import os
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64


class ConfigEncryption:
    """Handles encryption and decryption of sensitive configuration data."""
    
    def __init__(self):
        # Fixed salt for key derivation (in production, this could be user-specific)
        self.salt = b'obsidian_tools_salt_2024'
        
    def derive_key(self, master_password: str) -> bytes:
        """Derive encryption key from master password using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
    
    def encrypt_secrets(self, secrets: Dict[str, Any], master_password: str) -> bytes:
        """Encrypt sensitive configuration data."""
        try:
            key = self.derive_key(master_password)
            f = Fernet(key)
            return f.encrypt(json.dumps(secrets).encode())
        except Exception as e:
            logging.error(f"Encryption failed: {e}")
            raise
    
    def decrypt_secrets(self, encrypted_data: bytes, master_password: str) -> Dict[str, Any]:
        """Decrypt sensitive configuration data."""
        try:
            key = self.derive_key(master_password)
            f = Fernet(key)
            decrypted = f.decrypt(encrypted_data)
            return json.loads(decrypted.decode())
        except Exception as e:
            logging.error(f"Decryption failed: {e}")
            raise


class ConfigManager:
    """Manages application configuration with support for encrypted secrets and 1Password."""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.config_file = self.config_dir / "config.json"
        self.secrets_file = self.config_dir / "secrets.encrypted"
        self.example_file = self.config_dir / "config.example.json"
        
        self.encryption = ConfigEncryption()
        self._config_cache: Optional[Dict[str, Any]] = None
        self._secrets_cache: Optional[Dict[str, Any]] = None
        
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration structure."""
        return {
            "obsidian": {
                "api_url": "http://localhost:27123",
                "timeout": 30,
                "default_notes_folder": "GeneratedNotes"
            },
            "gemini": {
                "default_model": "gemini-2.5-flash",
                "timeout": 60
            },
            "ingest": {
                "default_ingest_folder": "ingest",
                "delete_after_ingest": True
            },
            "security": {
                "method": "local_encrypted",  # or "1password"
                "encryption_algorithm": "AES-256-GCM"
            }
        }
    
    def get_default_secrets(self) -> Dict[str, Any]:
        """Get default secrets structure."""
        return {
            "obsidian_api_key": "",
            "gemini_api_key": "",
            "obsidian_api_key_ref": "",  # 1Password reference
            "gemini_api_key_ref": ""     # 1Password reference
        }
    
    def create_example_config(self) -> None:
        """Create example configuration file."""
        if not self.example_file.exists():
            example_config = self.get_default_config()
            example_secrets = self.get_default_secrets()
            
            # Add example values
            example_config["obsidian"]["api_url"] = "http://localhost:27123"
            example_config["gemini"]["default_model"] = "gemini-2.5-flash"
            example_config["security"]["method"] = "local_encrypted"
            
            example_secrets["obsidian_api_key_ref"] = "op://vault/item/field"
            example_secrets["gemini_api_key_ref"] = "op://vault/item/field"
            
            with open(self.example_file, 'w') as f:
                json.dump({
                    "config": example_config,
                    "secrets": example_secrets
                }, f, indent=2)
    
    def load_config(self) -> Dict[str, Any]:
        """Load non-sensitive configuration."""
        if self._config_cache is not None:
            return self._config_cache
            
        if not self.config_file.exists():
            # Create default config
            default_config = self.get_default_config()
            self.save_config(default_config)
            self._config_cache = default_config
            return default_config
        
        try:
            with open(self.config_file, 'r') as f:
                self._config_cache = json.load(f)
                return self._config_cache
        except Exception as e:
            logging.error(f"Failed to load config: {e}")
            return self.get_default_config()
    
    def save_config(self, config: Dict[str, Any]) -> None:
        """Save non-sensitive configuration."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            self._config_cache = config
        except Exception as e:
            logging.error(f"Failed to save config: {e}")
            raise
    
    def load_secrets(self, master_password: Optional[str] = None) -> Dict[str, Any]:
        """Load sensitive configuration data."""
        if self._secrets_cache is not None:
            return self._secrets_cache
            
        config = self.load_config()
        security_method = config.get("security", {}).get("method", "local_encrypted")
        
        if security_method == "1password":
            return self._load_1password_secrets()
        elif security_method == "local_encrypted":
            if not master_password:
                raise ValueError("Master password required for local encrypted storage")
            return self._load_encrypted_secrets(master_password)
        else:
            raise ValueError(f"Unsupported security method: {security_method}")
    
    def _load_encrypted_secrets(self, master_password: str) -> Dict[str, Any]:
        """Load secrets from encrypted local storage."""
        if not self.secrets_file.exists():
            # Create default secrets
            default_secrets = self.get_default_secrets()
            self.save_secrets(default_secrets, master_password)
            self._secrets_cache = default_secrets
            return default_secrets
        
        try:
            with open(self.secrets_file, 'rb') as f:
                encrypted_data = f.read()
            
            secrets = self.encryption.decrypt_secrets(encrypted_data, master_password)
            self._secrets_cache = secrets
            return secrets
        except Exception as e:
            logging.error(f"Failed to load encrypted secrets: {e}")
            raise
    
    def _load_1password_secrets(self) -> Dict[str, Any]:
        """Load secrets from 1Password."""
        try:
            config = self.load_config()
            secrets = self.get_default_secrets()
            
            # Fetch API keys from 1Password
            obsidian_ref = os.getenv("OBSIDIAN_API_KEY_REF")
            gemini_ref = os.getenv("GEMINI_API_KEY_REF")
            
            if obsidian_ref:
                secrets["obsidian_api_key"] = self._fetch_1password_secret(obsidian_ref)
                secrets["obsidian_api_key_ref"] = obsidian_ref
            
            if gemini_ref:
                secrets["gemini_api_key"] = self._fetch_1password_secret(gemini_ref)
                secrets["gemini_api_key_ref"] = gemini_ref
            
            self._secrets_cache = secrets
            return secrets
            
        except Exception as e:
            logging.error(f"Failed to load 1Password secrets: {e}")
            raise
    
    def _fetch_1password_secret(self, secret_reference: str) -> str:
        """Fetch a secret from 1Password using the op CLI."""
        try:
            result = subprocess.run(
                ["op", "read", secret_reference],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except FileNotFoundError:
            raise RuntimeError("1Password CLI ('op') not found. Please install it from https://developer.1password.com/docs/cli/")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error fetching secret from 1Password: {e.stderr}")
    
    def save_secrets(self, secrets: Dict[str, Any], master_password: Optional[str] = None) -> None:
        """Save sensitive configuration data."""
        config = self.load_config()
        security_method = config.get("security", {}).get("method", "local_encrypted")
        
        if security_method == "1password":
            # For 1Password, we only store references
            self._save_1password_references(secrets)
        elif security_method == "local_encrypted":
            if not master_password:
                raise ValueError("Master password required for local encrypted storage")
            self._save_encrypted_secrets(secrets, master_password)
        else:
            raise ValueError(f"Unsupported security method: {security_method}")
        
        self._secrets_cache = secrets
    
    def _save_encrypted_secrets(self, secrets: Dict[str, Any], master_password: str) -> None:
        """Save secrets to encrypted local storage."""
        try:
            encrypted_data = self.encryption.encrypt_secrets(secrets, master_password)
            with open(self.secrets_file, 'wb') as f:
                f.write(encrypted_data)
        except Exception as e:
            logging.error(f"Failed to save encrypted secrets: {e}")
            raise
    
    def _save_1password_references(self, secrets: Dict[str, Any]) -> None:
        """Save 1Password references to environment variables."""
        # This would typically update environment variables or a separate config
        # For now, we'll just log the references
        logging.info("1Password references saved (environment variables should be updated)")
    
    def get_api_keys(self, master_password: Optional[str] = None) -> Tuple[str, str]:
        """Get Obsidian and Gemini API keys."""
        secrets = self.load_secrets(master_password)
        
        obsidian_key = secrets.get("obsidian_api_key", "")
        gemini_key = secrets.get("gemini_api_key", "")
        
        if not obsidian_key:
            raise ValueError("Obsidian API key not configured")
        if not gemini_key:
            raise ValueError("Gemini API key not configured")
        
        return obsidian_key, gemini_key
    
    def get_obsidian_config(self) -> Tuple[str, int, str]:
        """Get Obsidian configuration."""
        config = self.load_config()
        obsidian_config = config.get("obsidian", {})
        
        api_url = obsidian_config.get("api_url", "http://localhost:27123")
        timeout = obsidian_config.get("timeout", 30)
        notes_folder = obsidian_config.get("default_notes_folder", "GeneratedNotes")
        
        return api_url, timeout, notes_folder
    
    def get_gemini_config(self) -> Tuple[str, int]:
        """Get Gemini configuration."""
        config = self.load_config()
        gemini_config = config.get("gemini", {})
        
        default_model = gemini_config.get("default_model", "gemini-2.5-flash")
        timeout = gemini_config.get("timeout", 60)
        
        return default_model, timeout
    
    def get_ingest_config(self) -> Tuple[str, str, bool]:
        """Get ingest configuration."""
        config = self.load_config()
        ingest_config = config.get("ingest", {})
        
        ingest_folder = ingest_config.get("default_ingest_folder", "ingest")
        notes_folder = ingest_config.get("default_notes_folder", "GeneratedNotes")
        delete_after = ingest_config.get("delete_after_ingest", True)
        
        return ingest_folder, notes_folder, delete_after
    
    def test_connection(self, api_url: str, api_key: str, timeout: int = 10) -> bool:
        """Test connection to Obsidian API."""
        try:
            import requests
            session = requests.Session()
            session.headers.update({"Authorization": f"Bearer {api_key}"})
            
            response = session.get(api_url, timeout=timeout)
            response.raise_for_status()
            
            # Check if it's a valid Obsidian API response
            api_info = response.json()
            if "service" in api_info and "versions" in api_info:
                return True
            return False
            
        except Exception as e:
            logging.error(f"Connection test failed: {e}")
            return False
    
    def validate_config(self) -> Tuple[bool, list]:
        """Validate current configuration."""
        errors = []
        
        try:
            config = self.load_config()
            
            # Validate Obsidian config
            obsidian_config = config.get("obsidian", {})
            if not obsidian_config.get("api_url"):
                errors.append("Obsidian API URL is required")
            
            # Validate security method
            security_config = config.get("security", {})
            method = security_config.get("method")
            if method not in ["local_encrypted", "1password"]:
                errors.append("Invalid security method")
            
            # Try to load secrets to validate them
            try:
                if method == "local_encrypted":
                    # For local encrypted, we can't validate without password
                    pass
                elif method == "1password":
                    secrets = self._load_1password_secrets()
                    if not secrets.get("obsidian_api_key") and not secrets.get("obsidian_api_key_ref"):
                        errors.append("Obsidian API key or reference is required")
                    if not secrets.get("gemini_api_key") and not secrets.get("gemini_api_key_ref"):
                        errors.append("Gemini API key or reference is required")
            except Exception as e:
                errors.append(f"Failed to validate secrets: {e}")
            
        except Exception as e:
            errors.append(f"Configuration validation failed: {e}")
        
        return len(errors) == 0, errors
    
    def migrate_from_env(self, env_file_path: str) -> bool:
        """Migrate configuration from existing .env file."""
        try:
            from dotenv import load_dotenv
            
            # Load environment variables
            load_dotenv(env_file_path)
            
            # Extract configuration
            config = self.get_default_config()
            secrets = self.get_default_secrets()
            
            # Update config from environment
            if os.getenv("OBSIDIAN_API_URL"):
                config["obsidian"]["api_url"] = os.getenv("OBSIDIAN_API_URL")
            
            if os.getenv("NEW_NOTES_FOLDER"):
                config["obsidian"]["default_notes_folder"] = os.getenv("NEW_NOTES_FOLDER")
            
            # Update secrets from environment
            if os.getenv("OBSIDIAN_API_KEY_REF"):
                secrets["obsidian_api_key_ref"] = os.getenv("OBSIDIAN_API_KEY_REF")
            
            if os.getenv("GEMINI_API_KEY_REF"):
                secrets["gemini_api_key_ref"] = os.getenv("GEMINI_API_KEY_REF")
            
            # Set security method to 1Password if references are found
            if secrets["obsidian_api_key_ref"] or secrets["gemini_api_key_ref"]:
                config["security"]["method"] = "1password"
            
            # Save configuration
            self.save_config(config)
            if config["security"]["method"] == "1password":
                self._save_1password_references(secrets)
            
            return True
            
        except Exception as e:
            logging.error(f"Migration failed: {e}")
            return False
    
    def export_config(self, export_path: str, include_secrets: bool = False, 
                     master_password: Optional[str] = None) -> bool:
        """Export configuration to file."""
        try:
            export_data = {
                "config": self.load_config(),
                "exported_at": str(Path().cwd()),
                "version": "1.0"
            }
            
            if include_secrets:
                if master_password:
                    export_data["secrets"] = self.load_secrets(master_password)
                else:
                    export_data["secrets"] = "*** ENCRYPTED ***"
            
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            return True
            
        except Exception as e:
            logging.error(f"Export failed: {e}")
            return False
    
    def import_config(self, import_path: str, master_password: Optional[str] = None) -> bool:
        """Import configuration from file."""
        try:
            with open(import_path, 'r') as f:
                import_data = json.load(f)
            
            if "config" in import_data:
                self.save_config(import_data["config"])
            
            if "secrets" in import_data and import_data["secrets"] != "*** ENCRYPTED ***":
                if master_password:
                    self.save_secrets(import_data["secrets"], master_password)
                else:
                    logging.warning("Secrets found but no master password provided")
            
            return True
            
        except Exception as e:
            logging.error(f"Import failed: {e}")
            return False
