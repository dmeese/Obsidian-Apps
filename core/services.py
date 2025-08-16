"""
Service Container for ObsidianTools.

This module provides dependency injection and service management
for the application.
"""

from typing import Dict, Any, Optional
from .config.manager import ConfigManager
from .obsidian.client import ObsidianClient
from .llm.gemini_client import GeminiClient


class ServiceContainer:
    """Dependency injection container for ObsidianTools services."""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._configure_services()
    
    def _configure_services(self):
        """Configure all services with their dependencies."""
        try:
            # Configuration service (no dependencies)
            config_manager = ConfigManager()
            self._services['config'] = config_manager
            
            # Obsidian client (depends on config)
            obsidian_client = ObsidianClient(
                config=config_manager.get_config()
            )
            self._services['obsidian'] = obsidian_client
            
            # LLM service (depends on config for API keys)
            try:
                secrets = config_manager.load_secrets()
                gemini_api_key = secrets.get('gemini_api_key', '')
                if gemini_api_key:
                    llm_service = GeminiClient(api_key=gemini_api_key)
                    self._services['llm'] = llm_service
                else:
                    self._services['llm'] = None
            except Exception:
                # If secrets can't be loaded, LLM service won't be available
                self._services['llm'] = None
            
            # Analysis service (depends on obsidian client)
            from .analysis.engine import AnalysisEngine
            analysis_service = AnalysisEngine(
                obsidian_client=obsidian_client
            )
            self._services['analysis'] = analysis_service
            
            # Ingest service (depends on obsidian client and LLM)
            from .ingest.engine import IngestEngine
            ingest_service = IngestEngine(
                obsidian_client=obsidian_client,
                llm_service=self._services.get('llm')
            )
            self._services['ingest'] = ingest_service
            
        except Exception as e:
            # Log error but don't crash - services will be None
            print(f"Warning: Failed to configure services: {e}")
    
    def get_service(self, name: str) -> Optional[Any]:
        """Get a service by name."""
        return self._services.get(name)
    
    def has_service(self, name: str) -> bool:
        """Check if a service is available."""
        return name in self._services and self._services[name] is not None
    
    def get_available_services(self) -> list:
        """Get list of available service names."""
        return [name for name, service in self._services.items() if service is not None]
    
    def reload_services(self):
        """Reload all services (useful after configuration changes)."""
        self._services.clear()
        self._configure_services()
