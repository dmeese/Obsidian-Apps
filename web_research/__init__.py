"""
Web Research Module for Obsidian Tools

This module provides intelligent web research capabilities to enhance
Obsidian notes with relevant content from Wikipedia and other public sources.
"""

from web_research.source_handlers.wikipedia_handler import WikipediaHandler
from web_research.research_engine import WebResearchEngine

__version__ = "1.0.0"
__all__ = ["WikipediaHandler", "WebResearchEngine"]
