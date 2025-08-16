"""
Obsidian API client for ObsidianTools.

This module provides a client for communicating with the
Obsidian Local REST API.
"""

import json
import requests
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from secure_logging import ZeroSensitiveLogger, SafeLogContext


class ObsidianClient:
    """Client for communicating with Obsidian Local REST API."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_url = config.get('obsidian', {}).get('api_url', 'http://localhost:27123')
        self.timeout = config.get('obsidian', {}).get('timeout', 30)
        self.api_key = config.get('obsidian', {}).get('api_key', '')
        self.logger = ZeroSensitiveLogger("obsidian_client")
        
        # Session for making requests
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})
    
    def test_connection(self) -> bool:
        """Test connection to Obsidian API."""
        try:
            response = self.session.get(f"{self.api_url}/", timeout=self.timeout)
            response.raise_for_status()
            
            # Check if it's a valid Obsidian API response
            api_info = response.json()
            if "service" in api_info and "versions" in api_info:
                self.logger.info("Obsidian API connection successful", SafeLogContext(
                    operation="connection_test",
                    status="success",
                    metadata={"api_url": self.api_url}
                ))
                return True
            return False
            
        except Exception as e:
            self.logger.error("Obsidian API connection failed", SafeLogContext(
                operation="connection_test",
                status="failed",
                metadata={"error_type": type(e).__name__, "api_url": self.api_url}
            ))
            return False
    
    def get_vault_info(self) -> Optional[Dict[str, Any]]:
        """Get vault information from Obsidian."""
        try:
            response = self.session.get(f"{self.api_url}/", timeout=self.timeout)
            response.raise_for_status()
            
            vault_info = response.json()
            self.logger.info("Vault info retrieved successfully", SafeLogContext(
                operation="vault_info_fetch",
                status="success",
                metadata={"api_url": self.api_url}
            ))
            return vault_info
            
        except Exception as e:
            self.logger.error("Failed to get vault info", SafeLogContext(
                operation="vault_info_fetch",
                status="failed",
                metadata={"error_type": type(e).__name__, "api_url": self.api_url}
            ))
            return None
    
    def get_notes(self, folder_path: str = "") -> List[Dict[str, Any]]:
        """Get notes from the vault, optionally filtered by folder."""
        try:
            params = {}
            if folder_path:
                params['path'] = folder_path
            
            response = self.session.get(f"{self.api_url}/vault/notes", params=params, timeout=self.timeout)
            response.raise_for_status()
            
            notes = response.json()
            self.logger.info("Notes retrieved successfully", SafeLogContext(
                operation="notes_fetch",
                status="success",
                metadata={"folder_path": folder_path, "note_count": len(notes)}
            ))
            return notes
            
        except Exception as e:
            self.logger.error("Failed to get notes", SafeLogContext(
                operation="notes_fetch",
                status="failed",
                metadata={"error_type": type(e).__name__, "folder_path": folder_path}
            ))
            return []
    
    def get_folders(self) -> List[str]:
        """Get list of folders in the vault."""
        try:
            response = self.session.get(f"{self.api_url}/vault/folders", timeout=self.timeout)
            response.raise_for_status()
            
            folders = response.json()
            self.logger.info("Folders retrieved successfully", SafeLogContext(
                operation="folders_fetch",
                status="success",
                metadata={"folder_count": len(folders)}
            ))
            return folders
            
        except Exception as e:
            self.logger.error("Failed to get folders", SafeLogContext(
                operation="folders_fetch",
                status="failed",
                metadata={"error_type": type(e).__name__}
            ))
            return []
    
    def get_note_content(self, note_path: str) -> Optional[str]:
        """Get the content of a specific note."""
        try:
            response = self.session.get(f"{self.api_url}/vault/notes/{note_path}", timeout=self.timeout)
            response.raise_for_status()
            
            note_data = response.json()
            content = note_data.get('content', '')
            
            self.logger.info("Note content retrieved successfully", SafeLogContext(
                operation="note_content_fetch",
                status="success",
                metadata={"note_path": note_path, "content_length": len(content)}
            ))
            return content
            
        except Exception as e:
            self.logger.error("Failed to get note content", SafeLogContext(
                operation="note_content_fetch",
                status="failed",
                metadata={"error_type": type(e).__name__, "note_path": note_path}
            ))
            return None
    
    def create_note(self, path: str, content: str, folder: str = "") -> bool:
        """Create a new note in the vault."""
        try:
            note_data = {
                "path": path,
                "content": content
            }
            if folder:
                note_data["folder"] = folder
            
            response = self.session.post(
                f"{self.api_url}/vault/notes",
                json=note_data,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            self.logger.info("Note created successfully", SafeLogContext(
                operation="note_create",
                status="success",
                metadata={"note_path": path, "folder": folder, "content_length": len(content)}
            ))
            return True
            
        except Exception as e:
            self.logger.error("Failed to create note", SafeLogContext(
                operation="note_create",
                status="failed",
                metadata={"error_type": type(e).__name__, "note_path": path, "folder": folder}
            ))
            return False
    
    def update_note(self, path: str, content: str) -> bool:
        """Update an existing note in the vault."""
        try:
            note_data = {
                "content": content
            }
            
            response = self.session.put(
                f"{self.api_url}/vault/notes/{path}",
                json=note_data,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            self.logger.info("Note updated successfully", SafeLogContext(
                operation="note_update",
                status="success",
                metadata={"note_path": path, "content_length": len(content)}
            ))
            return True
            
        except Exception as e:
            self.logger.error("Failed to update note", SafeLogContext(
                operation="note_update",
                status="failed",
                metadata={"error_type": type(e).__name__, "note_path": path}
            ))
            return False
    
    def delete_note(self, path: str) -> bool:
        """Delete a note from the vault."""
        try:
            response = self.session.delete(f"{self.api_url}/vault/notes/{path}", timeout=self.timeout)
            response.raise_for_status()
            
            self.logger.info("Note deleted successfully", SafeLogContext(
                operation="note_delete",
                status="success",
                metadata={"note_path": path}
            ))
            return True
            
        except Exception as e:
            self.logger.error("Failed to delete note", SafeLogContext(
                operation="note_delete",
                status="failed",
                metadata={"error_type": type(e).__name__, "note_path": path}
            ))
            return False
    
    def search_notes(self, query: str, folder: str = "") -> List[Dict[str, Any]]:
        """Search for notes in the vault."""
        try:
            params = {"query": query}
            if folder:
                params['folder'] = folder
            
            response = self.session.get(f"{self.api_url}/vault/search", params=params, timeout=self.timeout)
            response.raise_for_status()
            
            results = response.json()
            self.logger.info("Note search completed successfully", SafeLogContext(
                operation="note_search",
                status="success",
                metadata={"query": query, "folder": folder, "result_count": len(results)}
            ))
            return results
            
        except Exception as e:
            self.logger.error("Failed to search notes", SafeLogContext(
                operation="note_search",
                status="failed",
                metadata={"error_type": type(e).__name__, "query": query, "folder": folder}
            ))
            return []
    
    def get_note_links(self, note_path: str) -> List[str]:
        """Get all links from a specific note."""
        try:
            response = self.session.get(f"{self.api_url}/vault/notes/{note_path}/links", timeout=self.timeout)
            response.raise_for_status()
            
            links = response.json()
            self.logger.info("Note links retrieved successfully", SafeLogContext(
                operation="note_links_fetch",
                status="success",
                metadata={"note_path": note_path, "link_count": len(links)}
            ))
            return links
            
        except Exception as e:
            self.logger.error("Failed to get note links", SafeLogContext(
                operation="note_links_fetch",
                status="failed",
                metadata={"error_type": type(e).__name__, "note_path": note_path}
            ))
            return []
    
    def get_note_backlinks(self, note_path: str) -> List[str]:
        """Get all backlinks to a specific note."""
        try:
            response = self.session.get(f"{self.api_url}/vault/notes/{note_path}/backlinks", timeout=self.timeout)
            response.raise_for_status()
            
            backlinks = response.json()
            self.logger.info("Note backlinks retrieved successfully", SafeLogContext(
                operation="note_backlinks_fetch",
                status="success",
                metadata={"note_path": note_path, "backlink_count": len(backlinks)}
            ))
            return backlinks
            
        except Exception as e:
            self.logger.error("Failed to get note backlinks", SafeLogContext(
                operation="note_backlinks_fetch",
                status="failed",
                metadata={"error_type": type(e).__name__, "note_path": note_path}
            ))
            return []
