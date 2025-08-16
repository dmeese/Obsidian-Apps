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
from urllib.parse import quote, unquote
import json
import re

# Import secure logging from centralized module
from secure_logging import secure_log


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
                secure_log("info", f"Rate limit reached, waiting {sleep_time:.1f} seconds")
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
            secure_log("error", f"Request failed: {e}")
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
            secure_log("warning", f"LLM query generation failed: {e}")
        
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
            secure_log("error", f"Failed to parse search results: {e}")
            return []
    
    def get_article_content(self, page_id: int) -> Optional[WikipediaArticle]:
        """
        Extract content from a Wikipedia article using MediaWiki Action API.
        
        Args:
            page_id: Wikipedia page ID
            
        Returns:
            WikipediaArticle object with extracted content
        """
        # Get article content using MediaWiki Action API
        params = {
            'action': 'query',
            'format': 'json',
            'pageids': page_id,
            'prop': 'extracts|info|categories|links',
            'exintro': 1,  # Get introduction only
            'explaintext': 1,  # Return plain text instead of HTML
            'inprop': 'url',
            'cllimit': 20,  # Limit categories
            'lllimit': 50   # Limit links
        }
        
        response = self._make_request(self.search_url, params)
        if not response:
            return None
        
        try:
            data = response.json()
            pages = data.get('query', {}).get('pages', {})
            page_data = pages.get(str(page_id))
            
            if not page_data:
                secure_log("warning", f"No page data found for page ID {page_id}")
                return None
            
            # Extract basic information
            title = page_data.get('title', '')
            extract = page_data.get('extract', '')
            url = page_data.get('fullurl', f"https://en.wikipedia.org/wiki/{quote(title)}")
            
            # Extract categories
            categories = []
            for cat in page_data.get('categories', []):
                cat_title = cat.get('title', '')
                if cat_title.startswith('Category:'):
                    categories.append(cat_title[9:])  # Remove 'Category:' prefix
            
            # Extract links (potential references)
            links = []
            for link in page_data.get('links', []):
                link_title = link.get('title', '')
                if not link_title.startswith('Category:') and not link_title.startswith('File:'):
                    links.append(link_title)
            
            # Create article object
            article = WikipediaArticle(
                title=title,
                page_id=page_id,
                url=url,
                summary=extract[:1000] if extract else '',  # Limit summary length
                categories=categories[:10],  # Limit categories
                references=links[:20],  # Use links as references
                citations=[],  # Will be populated separately
                content_sections=[]
            )
            
            # Try to get more detailed content for sections
            article.content_sections = self._get_content_sections(page_id)
            
            # Get citations/references
            article.references, article.citations = self._extract_references_and_citations(page_id)
            
            return article
            
        except (json.JSONDecodeError, KeyError) as e:
            secure_log("error", f"Failed to parse article content: {e}")
            return None
    
    def _get_content_sections(self, page_id: int) -> List[Dict[str, str]]:
        """Get content sections using MediaWiki Action API."""
        params = {
            'action': 'query',
            'format': 'json',
            'pageids': page_id,
            'prop': 'revisions',
            'rvprop': 'content',
            'rvslots': 'main'
        }
        
        response = self._make_request(self.search_url, params)
        if not response:
            return []
        
        try:
            data = response.json()
            pages = data.get('query', {}).get('pages', {})
            page_data = pages.get(str(page_id))
            
            if not page_data:
                return []
            
            content = page_data.get('revisions', [{}])[0].get('slots', {}).get('main', {}).get('content', '')
            
            # Parse MediaWiki markup to extract sections
            sections = []
            current_section = {'title': 'Introduction', 'content': ''}
            
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                
                # Check for section headers (== Header ==)
                if line.startswith('==') and line.endswith('=='):
                    # Save previous section if it has content
                    if current_section['content'].strip():
                        sections.append(current_section)
                    
                    # Start new section
                    section_title = line.strip('= ').strip()
                    current_section = {'title': section_title, 'content': ''}
                
                # Add content to current section
                elif line and not line.startswith('{{') and not line.startswith('|'):
                    current_section['content'] += line + ' '
            
            # Add the last section
            if current_section['content'].strip():
                sections.append(current_section)
            
            # Clean and limit sections
            cleaned_sections = []
            for section in sections[:8]:  # Limit to 8 sections
                content = section['content'].strip()
                if len(content) > 50:  # Only include sections with substantial content
                    cleaned_sections.append({
                        'title': section['title'],
                        'content': content[:500]  # Limit content length
                    })
            
            return cleaned_sections
            
        except Exception as e:
            secure_log("error", f"Failed to extract content sections: {e}")
            return []
    
    def _extract_references_and_citations(self, page_id: int) -> Tuple[List[str], List[Dict[str, str]]]:
        """Extract references and citations from a Wikipedia page using MediaWiki Action API."""
        # Get page content for references
        params = {
            'action': 'query',
            'format': 'json',
            'pageids': page_id,
            'prop': 'revisions|links|extlinks',
            'rvprop': 'content',
            'rvslots': 'main',
            'lllimit': 50,  # Limit internal links
            'ellimit': 50   # Limit external links
        }
        
        response = self._make_request(self.search_url, params)
        if not response:
            return [], []
        
        try:
            data = response.json()
            pages = data.get('query', {}).get('pages', {})
            page_data = pages.get(str(page_id))
            
            if not page_data:
                return [], []
            
            # Extract internal links (potential references)
            references = []
            for link in page_data.get('links', []):
                link_title = link.get('title', '')
                if not link_title.startswith('Category:') and not link_title.startswith('File:'):
                    references.append(link_title)
            
            # Extract external links (citations)
            citations = []
            for ext_link in page_data.get('extlinks', []):
                url = ext_link.get('*', '')
                if url and url.startswith('http'):
                    # Try to extract a meaningful title from the URL
                    title = url.split('/')[-1] if url.split('/')[-1] else url.split('/')[-2] if len(url.split('/')) > 2 else 'External Link'
                    title = title.replace('_', ' ').replace('-', ' ').title()
                    
                    citations.append({
                        'url': url,
                        'title': title,
                        'type': 'external_link'
                    })
            
            # Also try to extract references from the content if we have it
            if 'revisions' in page_data:
                content = page_data.get('revisions', [{}])[0].get('slots', {}).get('main', {}).get('content', '')
                
                # Extract reference tags
                ref_matches = re.findall(r'<ref[^>]*>(.*?)</ref>', content, re.DOTALL)
                for ref in ref_matches:
                    # Clean the reference content
                    clean_ref = re.sub(r'<[^>]+>', '', ref).strip()
                    if clean_ref and len(clean_ref) > 10:  # Only include substantial references
                        references.append(clean_ref[:200])  # Limit length
                
                # Extract citation patterns
                citation_patterns = [
                    r'\[(https?://[^\s\]]+)\s+([^\]]+)\]',  # [url title]
                    r'\[(https?://[^\s\]]+)\]',  # [url]
                ]
                
                for pattern in citation_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        if isinstance(match, tuple):
                            url, title = match
                        else:
                            url = match
                            title = url.split('/')[-1] if url.split('/')[-1] else 'External Link'
                        
                        if url not in [c['url'] for c in citations]:  # Avoid duplicates
                            citations.append({
                                'url': url,
                                'title': title.strip(),
                                'type': 'citation'
                            })
            
            # Limit results to avoid overwhelming
            references = references[:30]  # Limit to 30 references
            citations = citations[:20]   # Limit to 20 citations
            
            return references, citations
            
        except Exception as e:
            secure_log("error", f"Failed to extract references: {e}")
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
        secure_log("info", f"Researching note: {note_title}")
        
        # Generate search queries
        queries = self.generate_search_queries(note_content, note_title)
        secure_log("info", f"Generated queries: {queries}")
        
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
