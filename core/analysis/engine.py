"""
Analysis engine for ObsidianTools.

This module provides vault analysis functionality.
"""

import re
import json
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from secure_logging import ZeroSensitiveLogger, SafeLogContext


class AnalysisEngine:
    """Engine for analyzing Obsidian vaults."""
    
    def __init__(self, obsidian_client):
        self.obsidian_client = obsidian_client
        self.logger = ZeroSensitiveLogger("analysis_engine")
    
    def analyze_vault(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the vault and return comprehensive results."""
        try:
            self.logger.info("Starting comprehensive vault analysis", SafeLogContext(
                operation="vault_analysis",
                status="started",
                metadata={"params": params}
            ))
            
            # Get all notes from the vault
            notes = self.obsidian_client.get_notes()
            if not notes:
                return self._empty_analysis_result()
            
            # Analyze notes
            analysis_result = {
                'total_notes': len(notes),
                'total_links': 0,
                'orphans': [],
                'hubs': [],
                'dead_ends': [],
                'low_density_notes': [],
                'stubs': [],
                'note_statistics': {},
                'link_analysis': {},
                'folder_analysis': {},
                'tag_analysis': {},
                'recommendations': []
            }
            
            # Analyze each note
            note_links = {}
            note_backlinks = {}
            
            for note in notes:
                note_path = note.get('path', '')
                note_content = note.get('content', '')
                
                # Extract links from note content
                links = self._extract_links_from_content(note_content)
                note_links[note_path] = links
                analysis_result['total_links'] += len(links)
                
                # Count backlinks
                for link in links:
                    if link not in note_backlinks:
                        note_backlinks[link] = []
                    note_backlinks[link].append(note_path)
            
            # Identify orphan notes (no incoming links)
            analysis_result['orphans'] = self._identify_orphan_notes(notes, note_backlinks)
            
            # Identify hub notes (many outgoing links)
            hub_threshold = params.get('hub_threshold', 10)
            analysis_result['hubs'] = self._identify_hub_notes(note_links, hub_threshold)
            
            # Identify dead-end notes (no outgoing links)
            analysis_result['dead_ends'] = self._identify_dead_end_notes(note_links)
            
            # Identify low link density notes
            link_density_threshold = params.get('link_density_threshold', 0.02)
            min_word_count = params.get('min_word_count', 50)
            analysis_result['low_density_notes'] = self._identify_low_density_notes(
                notes, note_links, link_density_threshold, min_word_count
            )
            
            # Identify stub links (links to non-existent notes)
            analysis_result['stubs'] = self._identify_stub_links(note_links, notes)
            
            # Generate note statistics
            analysis_result['note_statistics'] = self._generate_note_statistics(notes, note_links)
            
            # Generate link analysis
            analysis_result['link_analysis'] = self._generate_link_analysis(note_links, note_backlinks)
            
            # Generate folder analysis
            analysis_result['folder_analysis'] = self._generate_folder_analysis(notes)
            
            # Generate tag analysis
            analysis_result['tag_analysis'] = self._generate_tag_analysis(notes)
            
            # Generate recommendations
            analysis_result['recommendations'] = self._generate_recommendations(analysis_result)
            
            # Save results to file if specified
            output_file = params.get('output_file', '')
            if output_file:
                self._save_analysis_results(analysis_result, output_file)
            
            self.logger.info("Vault analysis completed successfully", SafeLogContext(
                operation="vault_analysis",
                status="completed",
                metadata={
                    "total_notes": analysis_result['total_notes'],
                    "total_links": analysis_result['total_links'],
                    "orphans_found": len(analysis_result['orphans']),
                    "hubs_found": len(analysis_result['hubs'])
                }
            ))
            
            return analysis_result
            
        except Exception as e:
            self.logger.error("Vault analysis failed", SafeLogContext(
                operation="vault_analysis",
                status="failed",
                metadata={"error_type": type(e).__name__}
            ))
            raise
    
    def _extract_links_from_content(self, content: str) -> List[str]:
        """Extract all wiki-style links from note content."""
        # Match [[link]] and [[link|display text]] patterns
        link_pattern = r'\[\[([^|\]]+)(?:\|[^\]]+)?\]\]'
        links = re.findall(link_pattern, content)
        
        # Clean up links
        cleaned_links = []
        for link in links:
            link = link.strip()
            if link and not link.startswith('#'):  # Exclude heading links
                cleaned_links.append(link)
        
        return cleaned_links
    
    def _identify_orphan_notes(self, notes: List[Dict], note_backlinks: Dict) -> List[str]:
        """Identify notes with no incoming links."""
        orphan_notes = []
        
        for note in notes:
            note_path = note.get('path', '')
            # Skip notes that are linked to by other notes
            if note_path not in note_backlinks or not note_backlinks[note_path]:
                orphan_notes.append(note_path)
        
        return orphan_notes
    
    def _identify_hub_notes(self, note_links: Dict, threshold: int) -> List[Tuple[str, int]]:
        """Identify notes with many outgoing links (hub notes)."""
        hub_notes = []
        
        for note_path, links in note_links.items():
            if len(links) >= threshold:
                hub_notes.append((note_path, len(links)))
        
        # Sort by number of links (descending)
        hub_notes.sort(key=lambda x: x[1], reverse=True)
        return hub_notes
    
    def _identify_dead_end_notes(self, note_links: Dict) -> List[str]:
        """Identify notes with no outgoing links."""
        dead_end_notes = []
        
        for note_path, links in note_links.items():
            if not links:
                dead_end_notes.append(note_path)
        
        return dead_end_notes
    
    def _identify_low_density_notes(self, notes: List[Dict], note_links: Dict, 
                                   threshold: float, min_word_count: int) -> List[Tuple[str, float]]:
        """Identify notes with low link density."""
        low_density_notes = []
        
        for note in notes:
            note_path = note.get('path', '')
            content = note.get('content', '')
            
            # Calculate word count
            word_count = len(content.split())
            if word_count < min_word_count:
                continue
            
            # Calculate link density
            link_count = len(note_links.get(note_path, []))
            link_density = link_count / word_count if word_count > 0 else 0
            
            if link_density < threshold:
                low_density_notes.append((note_path, link_density))
        
        # Sort by link density (ascending)
        low_density_notes.sort(key=lambda x: x[1])
        return low_density_notes
    
    def _identify_stub_links(self, note_links: Dict, notes: List[Dict]) -> List[str]:
        """Identify links to non-existent notes."""
        existing_notes = {note.get('path', '') for note in notes}
        stub_links = set()
        
        for links in note_links.values():
            for link in links:
                if link not in existing_notes:
                    stub_links.add(link)
        
        return list(stub_links)
    
    def _generate_note_statistics(self, notes: List[Dict], note_links: Dict) -> Dict[str, Any]:
        """Generate statistics about notes."""
        total_words = 0
        total_chars = 0
        note_lengths = []
        
        for note in notes:
            content = note.get('content', '')
            word_count = len(content.split())
            char_count = len(content)
            
            total_words += word_count
            total_chars += char_count
            note_lengths.append(word_count)
        
        note_lengths.sort()
        
        return {
            'total_words': total_words,
            'total_characters': total_chars,
            'average_words_per_note': total_words / len(notes) if notes else 0,
            'average_chars_per_note': total_chars / len(notes) if notes else 0,
            'shortest_note': note_lengths[0] if note_lengths else 0,
            'longest_note': note_lengths[-1] if note_lengths else 0,
            'median_note_length': note_lengths[len(note_lengths)//2] if note_lengths else 0
        }
    
    def _generate_link_analysis(self, note_links: Dict, note_backlinks: Dict) -> Dict[str, Any]:
        """Generate analysis of links between notes."""
        link_counts = {}
        backlink_counts = {}
        
        # Count outgoing links
        for links in note_links.values():
            for link in links:
                link_counts[link] = link_counts.get(link, 0) + 1
        
        # Count incoming links
        for note_path, backlinks in note_backlinks.items():
            backlink_counts[note_path] = len(backlinks)
        
        # Find most linked notes
        most_linked = sorted(link_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Find notes with most backlinks
        most_backlinked = sorted(backlink_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'most_linked_notes': most_linked,
            'most_backlinked_notes': most_backlinked,
            'link_distribution': self._calculate_link_distribution(note_links),
            'backlink_distribution': self._calculate_link_distribution(note_backlinks)
        }
    
    def _calculate_link_distribution(self, link_data: Dict) -> Dict[str, int]:
        """Calculate distribution of link counts."""
        distribution = {}
        for links in link_data.values():
            count = len(links)
            distribution[str(count)] = distribution.get(str(count), 0) + 1
        return distribution
    
    def _generate_folder_analysis(self, notes: List[Dict]) -> Dict[str, Any]:
        """Generate analysis of folder structure."""
        folder_counts = {}
        folder_notes = {}
        
        for note in notes:
            note_path = note.get('path', '')
            folder = str(Path(note_path).parent) if Path(note_path).parent != Path('.') else 'root'
            
            folder_counts[folder] = folder_counts.get(folder, 0) + 1
            
            if folder not in folder_notes:
                folder_notes[folder] = []
            folder_notes[folder].append(note_path)
        
        # Sort folders by note count
        sorted_folders = sorted(folder_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'folder_note_counts': sorted_folders,
            'folder_notes': folder_notes,
            'total_folders': len(folder_counts)
        }
    
    def _generate_tag_analysis(self, notes: List[Dict]) -> Dict[str, Any]:
        """Generate analysis of tags used in notes."""
        tag_counts = {}
        tag_notes = {}
        
        for note in notes:
            content = note.get('content', '')
            note_path = note.get('path', '')
            
            # Extract tags (lines starting with #)
            tags = re.findall(r'^#(\w+)', content, re.MULTILINE)
            
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
                
                if tag not in tag_notes:
                    tag_notes[tag] = []
                tag_notes[tag].append(note_path)
        
        # Sort tags by usage count
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'tag_usage_counts': sorted_tags,
            'tag_notes': tag_notes,
            'total_unique_tags': len(tag_counts)
        }
    
    def _generate_recommendations(self, analysis_result: Dict) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        # Orphan notes
        orphan_count = len(analysis_result['orphans'])
        if orphan_count > 0:
            recommendations.append(f"Consider linking {orphan_count} orphan notes to improve connectivity")
        
        # Hub notes
        hub_count = len(analysis_result['hubs'])
        if hub_count > 0:
            recommendations.append(f"You have {hub_count} hub notes - consider expanding these as central knowledge nodes")
        
        # Dead-end notes
        dead_end_count = len(analysis_result['dead_ends'])
        if dead_end_count > 0:
            recommendations.append(f"Add outgoing links to {dead_end_count} dead-end notes to improve navigation")
        
        # Low density notes
        low_density_count = len(analysis_result['low_density_notes'])
        if low_density_count > 0:
            recommendations.append(f"Consider adding more internal links to {low_density_count} low-density notes")
        
        # Stub links
        stub_count = len(analysis_result['stubs'])
        if stub_count > 0:
            recommendations.append(f"Create {stub_count} missing notes for stub links to improve completeness")
        
        # General recommendations
        total_notes = analysis_result['total_notes']
        total_links = analysis_result['total_links']
        
        if total_notes > 0:
            link_density = total_links / total_notes
            if link_density < 2:
                recommendations.append("Consider increasing internal linking to improve knowledge connectivity")
            elif link_density > 10:
                recommendations.append("Your vault has high connectivity - consider organizing into topic clusters")
        
        return recommendations
    
    def _save_analysis_results(self, results: Dict, output_file: str) -> None:
        """Save analysis results to a markdown file."""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("# Obsidian Vault Analysis Report\n\n")
                
                # Summary
                f.write("## Summary\n")
                f.write(f"- Total Notes: {results['total_notes']}\n")
                f.write(f"- Total Links: {results['total_links']}\n")
                f.write(f"- Orphan Notes: {len(results['orphans'])}\n")
                f.write(f"- Hub Notes: {len(results['hubs'])}\n")
                f.write(f"- Dead-End Notes: {len(results['dead_ends'])}\n")
                f.write(f"- Low Density Notes: {len(results['low_density_notes'])}\n")
                f.write(f"- Stub Links: {len(results['stubs'])}\n\n")
                
                # Detailed sections
                if results['orphans']:
                    f.write("## Orphan Notes\n")
                    for orphan in results['orphans']:
                        f.write(f"- {orphan}\n")
                    f.write("\n")
                
                if results['hubs']:
                    f.write("## Hub Notes\n")
                    for hub, link_count in results['hubs']:
                        f.write(f"- {hub} ({link_count} links)\n")
                    f.write("\n")
                
                if results['recommendations']:
                    f.write("## Recommendations\n")
                    for rec in results['recommendations']:
                        f.write(f"- {rec}\n")
                    f.write("\n")
            
            self.logger.info("Analysis results saved to file", SafeLogContext(
                operation="results_save",
                status="success",
                metadata={"output_file": output_file}
            ))
            
        except Exception as e:
            self.logger.error("Failed to save analysis results", SafeLogContext(
                operation="results_save",
                status="failed",
                metadata={"error_type": type(e).__name__, "output_file": output_file}
            ))
    
    def _empty_analysis_result(self) -> Dict[str, Any]:
        """Return empty analysis result structure."""
        return {
            'total_notes': 0,
            'total_links': 0,
            'orphans': [],
            'hubs': [],
            'dead_ends': [],
            'low_density_notes': [],
            'stubs': [],
            'note_statistics': {},
            'link_analysis': {},
            'folder_analysis': {},
            'tag_analysis': {},
            'recommendations': ['No notes found in vault']
        }
