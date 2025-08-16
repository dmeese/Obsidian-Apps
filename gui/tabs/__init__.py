"""
Tabs package for ObsidianTools GUI.

This package contains the individual tab implementations
for analysis, ingest, configuration, and research.
"""

from .analysis_tab import AnalysisTab
from .ingest_tab import IngestTab
from .config_tab import ConfigTab
from .research_tab import ResearchTab

__all__ = [
    'AnalysisTab',
    'IngestTab', 
    'ConfigTab',
    'ResearchTab'
]
