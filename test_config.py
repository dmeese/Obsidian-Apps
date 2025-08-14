#!/usr/bin/env python3
"""
Test script for the configuration management system.
"""

import os
import tempfile
from config_manager import ConfigManager


def test_config_manager():
    """Test the configuration manager functionality."""
    print("🧪 Testing Configuration Manager...")
    print("=" * 50)
    
    # Create a temporary config directory
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Using temporary directory: {temp_dir}")
        
        # Initialize config manager
        cm = ConfigManager(temp_dir)
        print("✅ Config manager initialized")
        
        # Test default configuration
        default_config = cm.get_default_config()
        print(f"✅ Default config loaded: {len(default_config)} sections")
        
        # Test default secrets
        default_secrets = cm.get_default_secrets()
        print(f"✅ Default secrets loaded: {len(default_secrets)} items")
        
        # Test configuration save/load
        test_config = {
            "obsidian": {
                "api_url": "http://localhost:27123",
                "timeout": 45,
                "default_notes_folder": "TestNotes"
            },
            "gemini": {
                "default_model": "gemini-2.5-flash-lite",
                "timeout": 90
            },
            "ingest": {
                "default_ingest_folder": "test_ingest",
                "delete_after_ingest": False
            },
            "security": {
                "method": "local_encrypted",
                "encryption_algorithm": "AES-256-GCM"
            }
        }
        
        cm.save_config(test_config)
        print("✅ Test configuration saved")
        
        loaded_config = cm.load_config()
        print("✅ Configuration loaded back")
        
        # Verify the loaded config matches
        if loaded_config == test_config:
            print("✅ Configuration round-trip successful")
        else:
            print("❌ Configuration round-trip failed")
            print(f"Expected: {test_config}")
            print(f"Got: {loaded_config}")
        
        # Test encrypted secrets
        test_secrets = {
            "obsidian_api_key": "test_obsidian_key_12345",
            "gemini_api_key": "test_gemini_key_67890",
            "obsidian_api_key_ref": "",
            "gemini_api_key_ref": ""
        }
        
        master_password = "test_master_password_2024"
        
        try:
            cm.save_secrets(test_secrets, master_password)
            print("✅ Test secrets encrypted and saved")
            
            loaded_secrets = cm.load_secrets(master_password)
            print("✅ Encrypted secrets loaded back")
            
            # Verify the loaded secrets match
            if loaded_secrets == test_secrets:
                print("✅ Secrets round-trip successful")
            else:
                print("❌ Secrets round-trip failed")
                print(f"Expected: {test_secrets}")
                print(f"Got: {loaded_secrets}")
                
        except Exception as e:
            print(f"❌ Secrets encryption/decryption failed: {e}")
        
        # Test configuration validation
        is_valid, errors = cm.validate_config()
        if is_valid:
            print("✅ Configuration validation passed")
        else:
            print(f"❌ Configuration validation failed: {errors}")
        
        # Test export/import
        export_path = os.path.join(temp_dir, "export_config.json")
        if cm.export_config(export_path, include_secrets=True, master_password=master_password):
            print("✅ Configuration exported successfully")
            
            # Test import
            if cm.import_config(export_path, master_password):
                print("✅ Configuration imported successfully")
            else:
                print("❌ Configuration import failed")
        else:
            print("❌ Configuration export failed")
        
        print("\n✅ All configuration tests completed!")


if __name__ == "__main__":
    test_config_manager()
