"""
Wikipedia Handler for Web Research

This module provides intelligent Wikipedia integration using the MediaWiki API
with rate limiting, LLM-powered query generation, and content extraction.
"""

import requests
import time
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import quote
import json
import re


@dataclass
class WikipediaSearchResult:
    """Represents a Wikipedia search result."""
    title: str
    page_id: int
    snippet: str
    url: str
    relevance_score: float = 0.0


@dataclass
class WikipediaArticle:
    """Represents a Wikipedia article with extracted content."""
    title: str
    page_id: int
    url: str
    summary: str
    categories: List[str]
    references: List[str]
    citations: List[Dict[str, str]]
    content_sections: List[Dict[str, str]]


class WikipediaHandler:
    """
    Handles Wikipedia research using MediaWiki API with rate limiting.
    
    Features:
    - Rate limiting (100 requests/minute to be respectful)
    - LLM-powered query generation
    - Content extraction and relevance scoring
    - Citation generation
    """
    
    def __init__(self, gemini_model=None, rate_limit_per_minute: int = 100):
        """
        Initialize Wikipedia handler.
        
        Args:
            gemini_model: Gemini model for intelligent query generation
            rate_limit_per_minute: Maximum requests per minute (default: 100)
        """
        self.gemini_model = gemini_model
        self.rate_limit_per_minute = rate_limit_per_minute
        self.request_times = []
        self.base_url = "https://en.wikipedia.org/api/rest_v1"
        self.search_url = "https://en.wikipedia.org/w/api.php"
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
    def _rate_limit_check(self):
        """Ensure we don't exceed rate limits."""
        current_time = time.time()
        
        # Remove requests older than 1 minute
        self.request_times = [t for t in self.request_times if current_time - t < 60]
        
        # If we've made too many requests, wait
        if len(self.request_times) >= self.rate_limit_per_minute:
            sleep_time = 60 - (current_time - self.request_times[0])
            if sleep_time > 0:
                self.logger.info(f"Rate limit reached, waiting {sleep_time:.1f} seconds")
                time.sleep(sleep_time)
        
        # Record this request
        self.request_times.append(current_time)
    
    def _make_request(self, url: str, params: Dict = None) -> Optional[requests.Response]:
        """Make a rate-limited request to Wikipedia."""
        self._rate_limit_check()
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            return None
    
    def generate_search_queries(self, note_content: str, note_title: str) -> List[str]:
        """
        Generate intelligent search queries using LLM.
        
        Args:
            note_content: Content of the note to research
            note_title: Title of the note
            
        Returns:
            List of search queries for Wikipedia
        """
        if not self.gemini_model:
            # Fallback to simple keyword extraction
            return self._fallback_query_generation(note_content, note_title)
        
        try:
            prompt = f"""
            You are a research assistant helping to find relevant Wikipedia articles.
            
            Note Title: {note_title}
            Note Content: {note_content[:1000]}...
            
            Generate 3-5 specific, focused search queries for Wikipedia that would help
            expand and contextualize this note. Focus on:
            - Core concepts and terminology
            - Related theories or methods
            - Historical context
            - Applications or examples
            
            Return ONLY a JSON array of strings, no other text:
            ["query1", "query2", "query3"]
            """
            
            response = self.gemini_model.generate_content(prompt)
            queries = json.loads(response.text.strip())
            
            # Validate and clean queries
            if isinstance(queries, list) and all(isinstance(q, str) for q in queries):
                return [q.strip() for q in queries if q.strip()]
            
        except Exception as e:
            self.logger.warning(f"LLM query generation failed: {e}")
        
        # Fallback to simple keyword extraction
        return self._fallback_query_generation(note_content, note_title)
    
    def _fallback_query_generation(self, note_content: str, note_title: str) -> List[str]:
        """Fallback method for query generation without LLM."""
        # Extract key terms from title and content
        key_terms = []
        
        # Add title terms
        title_terms = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', note_title)
        key_terms.extend(title_terms)
        
        # Add content terms (capitalized words, technical terms)
        content_terms = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', note_content)
        key_terms.extend(content_terms)
        
        # Remove duplicates and limit length
        unique_terms = list(set(key_terms))
        queries = []
        
        for term in unique_terms[:5]:
            if len(term) > 3:  # Avoid very short terms
                queries.append(term)
        
        return queries if queries else [note_title]
    
    def search_wikipedia(self, query: str, max_results: int = 5) -> List[WikipediaSearchResult]:
        """
        Search Wikipedia for a given query.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of search results
        """
        params = {
            'action': 'query',
            'format': 'json',
            'list': 'search',
            'srsearch': query,
            'srlimit': max_results,
            'srnamespace': 0,  # Main namespace only
            'srqiprofile': 'classic'  # Better relevance
        }
        
        response = self._make_request(self.search_url, params)
        if not response:
            return []
        
        try:
            data = response.json()
            results = []
            
            for item in data.get('query', {}).get('search', []):
                result = WikipediaSearchResult(
                    title=item.get('title', ''),
                    page_id=item.get('pageid', 0),
                    snippet=item.get('snippet', ''),
                    url=f"https://en.wikipedia.org/wiki/{quote(item.get('title', ''))}"
                )
                results.append(result)
            
            return results
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Failed to parse search results: {e}")
            return []
    
    def get_article_content(self, page_id: int) -> Optional[WikipediaArticle]:
        """
        Extract content from a Wikipedia article.
        
        Args:
            page_id: Wikipedia page ID
            
        Returns:
            WikipediaArticle object with extracted content
        """
        # Get article summary
        summary_url = f"{self.base_url}/page/summary/{page_id}"
        summary_response = self._make_request(summary_url)
        
        if not summary_response:
            return None
        
        try:
            summary_data = summary_response.json()
            
            # Get full article content
            content_url = f"{self.base_url}/page/html/{page_id}"
            content_response = self._make_request(content_url)
            
            article = WikipediaArticle(
                title=summary_data.get('title', ''),
                page_id=page_id,
                url=summary_data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                summary=summary_data.get('extract', ''),
                categories=summary_data.get('categories', []),
                references=[],
                citations=[],
                content_sections=[]
            )
            
            # Extract content sections if available
            if content_response:
                article.content_sections = self._extract_content_sections(content_response.text)
            
            # Extract references and citations
            article.references, article.citations = self._extract_references_and_citations(page_id)
            
            return article
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Failed to parse article content: {e}")
            return None
    
    def _extract_content_sections(self, html_content: str) -> List[Dict[str, str]]:
        """Extract content sections from HTML content."""
        sections = []
        
        # Simple HTML parsing for sections
        # This is a basic implementation - could be enhanced with BeautifulSoup
        section_pattern = r'<h[2-6][^>]*>(.*?)</h[2-6]>.*?(?=<h[2-6]|$)'
        matches = re.findall(section_pattern, html_content, re.DOTALL)
        
        for i, match in enumerate(matches[:10]):  # Limit to 10 sections
            # Clean HTML tags
            clean_content = re.sub(r'<[^>]+>', '', match)
            if clean_content.strip():
                sections.append({
                    'title': f'Section {i+1}',
                    'content': clean_content.strip()[:500]  # Limit content length
                })
        
        return sections
    
    def _extract_references_and_citations(self, page_id: int) -> Tuple[List[str], List[Dict[str, str]]]:
        """Extract references and citations from a Wikipedia page."""
        # Get page content for references
        params = {
            'action': 'query',
            'format': 'json',
            'prop': 'revisions',
            'pageids': page_id,
            'rvprop': 'content',
            'rvslots': 'main'
        }
        
        response = self._make_request(self.search_url, params)
        if not response:
            return [], []
        
        try:
            data = response.json()
            content = data.get('query', {}).get('pages', {}).get(str(page_id), {}).get('revisions', [{}])[0].get('slots', {}).get('main', {}).get('content', '')
            
            # Extract references (basic pattern matching)
            references = re.findall(r'<ref[^>]*>(.*?)</ref>', content)
            citations = []
            
            # Extract external links that might be citations
            external_links = re.findall(r'\[(https?://[^\s\]]+)\s+([^\]]+)\]', content)
            for url, title in external_links[:20]:  # Limit to 20 citations
                citations.append({
                    'url': url,
                    'title': title.strip(),
                    'type': 'external_link'
                })
            
            return references, citations
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Failed to extract references: {e}")
            return [], []
    
    def calculate_relevance_score(self, article: WikipediaArticle, note_content: str) -> float:
        """
        Calculate relevance score between article and note content.
        
        Args:
            article: Wikipedia article
            note_content: Original note content
            
        Returns:
            Relevance score (0.0 to 1.0)
        """
        if not article.summary or not note_content:
            return 0.0
        
        # Simple relevance scoring based on term overlap
        note_words = set(re.findall(r'\b\w+\b', note_content.lower()))
        article_words = set(re.findall(r'\b\w+\b', article.summary.lower()))
        
        # Calculate Jaccard similarity
        intersection = len(note_words.intersection(article_words))
        union = len(note_words.union(article_words))
        
        if union == 0:
            return 0.0
        
        base_score = intersection / union
        
        # Boost score for title matches
        title_words = set(re.findall(r'\b\w+\b', article.title.lower()))
        title_overlap = len(note_words.intersection(title_words))
        if title_overlap > 0:
            base_score += 0.2
        
        # Boost score for category relevance
        category_boost = 0.1 * min(len(article.categories), 3)
        base_score += category_boost
        
        return min(base_score, 1.0)
    
    def research_note(self, note_content: str, note_title: str, max_articles: int = 3) -> List[WikipediaArticle]:
        """
        Research a note and return relevant Wikipedia articles.
        
        Args:
            note_content: Content of the note to research
            note_title: Title of the note
            max_articles: Maximum number of articles to return
            
        Returns:
            List of relevant Wikipedia articles
        """
        self.logger.info(f"Researching note: {note_title}")
        
        # Generate search queries
        queries = self.generate_search_queries(note_content, note_title)
        self.logger.info(f"Generated queries: {queries}")
        
        all_articles = []
        
        # Search for each query
        for query in queries:
            search_results = self.search_wikipedia(query, max_results=5)
            
            for result in search_results:
                article = self.get_article_content(result.page_id)
                if article:
                    # Calculate relevance score
                    relevance = self.calculate_relevance_score(article, note_content)
                    article.relevance_score = relevance
                    
                    if relevance > 0.1:  # Only include relevant articles
                        all_articles.append(article)
        
        # Sort by relevance and return top results
        all_articles.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Remove duplicates based on page_id
        seen_ids = set()
        unique_articles = []
        for article in all_articles:
            if article.page_id not in seen_ids:
                seen_ids.add(article.page_id)
                unique_articles.append(article)
        
        return unique_articles[:max_articles]
