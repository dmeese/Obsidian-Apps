"""
Web Research Engine for Obsidian Tools

This module orchestrates web research operations including Wikipedia integration,
content enhancement, and note updating.
"""

import logging
import os
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import json
import re

from web_research.source_handlers.wikipedia_handler import WikipediaHandler, WikipediaArticle


@dataclass
class ResearchResult:
    """Represents the result of researching a note."""
    note_title: str
    original_content: str
    enhanced_content: str
    wikipedia_articles: List[WikipediaArticle]
    citations_added: int
    content_sections_added: int


class WebResearchEngine:
    """
    Main engine for web research operations.
    
    Features:
    - Wikipedia research integration
    - Intelligent content enhancement
    - Citation management
    - Progress tracking
    """
    
    def __init__(self, gemini_model=None, config: Dict = None):
        """
        Initialize the research engine.
        
        Args:
            gemini_model: Gemini model for intelligent processing
            config: Configuration dictionary
        """
        self.gemini_model = gemini_model
        self.config = config or {}
        
        # Initialize Wikipedia handler
        self.wikipedia_handler = WikipediaHandler(
            gemini_model=gemini_model,
            rate_limit_per_minute=self.config.get('rate_limit_per_minute', 100)
        )
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Research statistics
        self.stats = {
            'notes_researched': 0,
            'articles_found': 0,
            'citations_added': 0,
            'content_sections_added': 0
        }
    
    def research_note(self, note_content: str, note_title: str, max_articles: int = 3) -> ResearchResult:
        """
        Research a single note and return enhanced content.
        
        Args:
            note_content: Original note content
            note_title: Title of the note
            max_articles: Maximum Wikipedia articles to include
            
        Returns:
            ResearchResult with enhanced content
        """
        self.logger.info(f"Starting research for note: {note_title}")
        
        # Research Wikipedia for relevant articles
        wikipedia_articles = self.wikipedia_handler.research_note(
            note_content, 
            note_title, 
            max_articles
        )
        
        self.logger.info(f"Found {len(wikipedia_articles)} relevant Wikipedia articles")
        
        # Enhance content with research findings
        enhanced_content = self._enhance_content_with_research(
            note_content, 
            note_title, 
            wikipedia_articles
        )
        
        # Count additions
        citations_added = self._count_citations_added(enhanced_content, note_content)
        content_sections_added = self._count_content_sections_added(enhanced_content, note_content)
        
        # Update statistics
        self.stats['notes_researched'] += 1
        self.stats['articles_found'] += len(wikipedia_articles)
        self.stats['citations_added'] += citations_added
        self.stats['content_sections_added'] += content_sections_added
        
        return ResearchResult(
            note_title=note_title,
            original_content=note_content,
            enhanced_content=enhanced_content,
            wikipedia_articles=wikipedia_articles,
            citations_added=citations_added,
            content_sections_added=content_sections_added
        )
    
    def _enhance_content_with_research(
        self, 
        original_content: str, 
        note_title: str, 
        articles: List[WikipediaArticle]
    ) -> str:
        """
        Enhance note content with Wikipedia research findings.
        
        Args:
            original_content: Original note content
            note_title: Title of the note
            articles: List of relevant Wikipedia articles
            
        Returns:
            Enhanced content with research additions
        """
        if not articles:
            return original_content
        
        enhanced_content = original_content
        
        # Add research context section
        research_section = self._create_research_section(articles)
        enhanced_content += f"\n\n{research_section}"
        
        # Add citations section
        citations_section = self._create_citations_section(articles)
        enhanced_content += f"\n\n{citations_section}"
        
        # Add enhanced wikilinks for discovered concepts
        enhanced_content = self._add_enhanced_wikilinks(enhanced_content, articles)
        
        return enhanced_content
    
    def _create_research_section(self, articles: List[WikipediaArticle]) -> str:
        """Create a research context section with Wikipedia findings."""
        section = "## Research Context\n\n"
        
        for i, article in enumerate(articles, 1):
            section += f"### {article.title}\n\n"
            
            if article.summary:
                # Truncate summary if too long
                summary = article.summary[:300] + "..." if len(article.summary) > 300 else article.summary
                section += f"{summary}\n\n"
            
            # Add relevant content sections
            if article.content_sections:
                section += "**Key Points:**\n"
                for section_data in article.content_sections[:3]:  # Limit to 3 sections
                    section += f"- {section_data['content'][:150]}...\n"
                section += "\n"
            
            # Add categories for context
            if article.categories:
                relevant_categories = [cat for cat in article.categories if not cat.startswith('Wikipedia:')]
                if relevant_categories:
                    section += f"**Categories:** {', '.join(relevant_categories[:5])}\n\n"
            
            section += f"**Source:** [Wikipedia: {article.title}]({article.url})\n\n"
        
        return section
    
    def _create_citations_section(self, articles: List[WikipediaArticle]) -> str:
        """Create a citations section with proper attribution."""
        section = "## Sources\n\n"
        
        for i, article in enumerate(articles, 1):
            section += f"[{i}]: Wikipedia contributors. \"{article.title}.\" "
            section += f"Wikipedia, The Free Encyclopedia. "
            section += f"Wikipedia, The Free Encyclopedia, {self._get_current_year()}. "
            section += f"Web. {article.url}\n\n"
        
        return section
    
    def _add_enhanced_wikilinks(self, content: str, articles: List[WikipediaArticle]) -> str:
        """Add enhanced wikilinks for discovered concepts."""
        enhanced_content = content
        
        # Add wikilinks for article titles and key concepts
        for article in articles:
            # Add wikilink for the main article title
            title_pattern = re.escape(article.title)
            if re.search(rf'\b{title_pattern}\b', enhanced_content, re.IGNORECASE):
                # Replace with wikilink if not already linked
                if not re.search(rf'\[\[{re.escape(article.title)}\]\]', enhanced_content):
                    enhanced_content = re.sub(
                        rf'\b({re.escape(article.title)})\b',
                        r'[[\1]]',
                        enhanced_content,
                        flags=re.IGNORECASE,
                        count=1  # Only replace first occurrence
                    )
            
            # Add wikilinks for key categories
            for category in article.categories[:3]:  # Limit to 3 categories
                if not category.startswith('Wikipedia:'):
                    category_clean = category.replace('Category:', '').strip()
                    if category_clean and len(category_clean) > 3:
                        # Only add if not already linked and not too generic
                        if not re.search(rf'\[\[{re.escape(category_clean)}\]\]', enhanced_content):
                            # Find a good place to add the wikilink
                            if re.search(rf'\b{re.escape(category_clean)}\b', enhanced_content, re.IGNORECASE):
                                enhanced_content = re.sub(
                                    rf'\b({re.escape(category_clean)})\b',
                                    r'[[\1]]',
                                    enhanced_content,
                                    flags=re.IGNORECASE,
                                    count=1
                                )
        
        return enhanced_content
    
    def _count_citations_added(self, enhanced_content: str, original_content: str) -> int:
        """Count how many citations were added."""
        original_citations = len(re.findall(r'\[\d+\]:', original_content))
        enhanced_citations = len(re.findall(r'\[\d+\]:', enhanced_content))
        return max(0, enhanced_citations - original_citations)
    
    def _count_content_sections_added(self, enhanced_content: str, original_content: str) -> int:
        """Count how many content sections were added."""
        original_sections = len(re.findall(r'^##\s+', original_content, re.MULTILINE))
        enhanced_sections = len(re.findall(r'^##\s+', enhanced_content, re.MULTILINE))
        return max(0, enhanced_sections - original_sections)
    
    def _get_current_year(self) -> str:
        """Get current year for citations."""
        from datetime import datetime
        return str(datetime.now().year)
    
    def get_research_statistics(self) -> Dict:
        """Get current research statistics."""
        return self.stats.copy()
    
    def reset_statistics(self):
        """Reset research statistics."""
        self.stats = {
            'notes_researched': 0,
            'articles_found': 0,
            'citations_added': 0,
            'content_sections_added': 0
        }
    
    def research_vault_folder(
        self, 
        vault_path: str, 
        target_folder: str, 
        max_articles_per_note: int = 3,
        progress_callback=None
    ) -> List[ResearchResult]:
        """
        Research all notes in a specific vault folder.
        
        Args:
            vault_path: Path to the Obsidian vault
            target_folder: Folder within the vault to research
            max_articles_per_note: Maximum articles per note
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of research results for all processed notes
        """
        folder_path = Path(vault_path) / target_folder
        
        if not folder_path.exists():
            self.logger.error(f"Target folder does not exist: {folder_path}")
            return []
        
        # Find all markdown files in the folder
        markdown_files = list(folder_path.rglob("*.md"))
        
        if not markdown_files:
            self.logger.info(f"No markdown files found in folder: {target_folder}")
            return []
        
        self.logger.info(f"Found {len(markdown_files)} markdown files to research")
        
        results = []
        
        for i, file_path in enumerate(markdown_files):
            try:
                # Read note content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract title from filename or frontmatter
                title = self._extract_note_title(file_path, content)
                
                # Research the note
                result = self.research_note(content, title, max_articles_per_note)
                results.append(result)
                
                # Update progress
                if progress_callback:
                    progress = (i + 1) / len(markdown_files) * 100
                    progress_callback(progress, f"Researching: {title}")
                
                self.logger.info(f"Completed research for: {title}")
                
            except Exception as e:
                self.logger.error(f"Failed to research file {file_path}: {e}")
                continue
        
        self.logger.info(f"Completed research for {len(results)} notes in folder: {target_folder}")
        return results
    
    def _extract_note_title(self, file_path: Path, content: str) -> str:
        """Extract note title from filename or frontmatter."""
        # Try to extract from YAML frontmatter first
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if frontmatter_match:
            frontmatter = frontmatter_match.group(1)
            title_match = re.search(r'^title:\s*(.+)$', frontmatter, re.MULTILINE)
            if title_match:
                return title_match.group(1).strip()
        
        # Fallback to filename
        return file_path.stem.replace('_', ' ').replace('-', ' ')
    
    def save_enhanced_notes(
        self, 
        research_results: List[ResearchResult], 
        vault_path: str, 
        target_folder: str,
        backup_original: bool = True
    ) -> int:
        """
        Save enhanced notes back to the vault.
        
        Args:
            research_results: List of research results
            vault_path: Path to the Obsidian vault
            target_folder: Folder within the vault
            backup_original: Whether to backup original notes
            
        Returns:
            Number of notes successfully saved
        """
        folder_path = Path(vault_path) / target_folder
        saved_count = 0
        
        for result in research_results:
            try:
                # Find the original file
                filename = f"{result.note_title.replace(' ', '_')}.md"
                file_path = folder_path / filename
                
                # Create backup if requested
                if backup_original and file_path.exists():
                    backup_path = file_path.with_suffix('.md.backup')
                    with open(file_path, 'r', encoding='utf-8') as f:
                        original_content = f.read()
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        f.write(original_content)
                
                # Save enhanced content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(result.enhanced_content)
                
                saved_count += 1
                self.logger.info(f"Saved enhanced note: {result.note_title}")
                
            except Exception as e:
                self.logger.error(f"Failed to save enhanced note {result.note_title}: {e}")
                continue
        
        self.logger.info(f"Successfully saved {saved_count} enhanced notes")
        return saved_count
