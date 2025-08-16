"""
Analysis engine for ObsidianTools.

This module provides vault analysis functionality.
"""

import re
import json
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from secure_logging import ZeroSensitiveLogger, SafeLogContext
import os
import urllib.parse


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
            
            # Use the working approach from analyzer.py - start at vault root
            # and recursively traverse the structure
            all_notes = self._fetch_all_notes_recursively()
            if not all_notes:
                return self._empty_analysis_result()
            
            # Build note graph and analyze
            note_graph = self._build_note_graph(all_notes)
            analysis_result = self._analyze_graph(note_graph, params)
            
            # Save results to file if specified
            output_file = params.get('output_file', '')
            if output_file:
                self._save_analysis_results(analysis_result, output_file)
            
            self.logger.info("Vault analysis completed successfully", SafeLogContext(
                operation="vault_analysis",
                status="completed",
                metadata={
                    "total_notes": analysis_result['total_notes'],
                    "total_links": analysis_result['total_links']
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
    
    def _fetch_all_notes_recursively(self) -> List[str]:
        """Fetch all markdown files by recursively traversing the vault from root."""
        
        all_markdown_files = set()
        # Start at root (empty string represents root directory)
        dirs_to_scan = [""]
        scanned_dirs = set()
        
        while dirs_to_scan:
            current_dir = dirs_to_scan.pop(0)
            if current_dir in scanned_dirs:
                continue
            scanned_dirs.add(current_dir)
            
            self.logger.debug("Scanning directory", SafeLogContext(
                operation="directory_scan",
                status="scanning",
                metadata={"current_dir": current_dir if current_dir else "/"}
            ))
            
            try:
                # Use the directory listing endpoint (like analyzer.py did)
                if current_dir:
                    # For subdirectories, use /vault/{path}/
                    encoded_path = urllib.parse.quote(current_dir)
                    list_url = f"{self.obsidian_client.api_url}/vault/{encoded_path}/"
                else:
                    # For root, use /vault/
                    list_url = f"{self.obsidian_client.api_url}/vault/"
                
                # Get directory contents
                response = self.obsidian_client.session.get(list_url, timeout=self.obsidian_client.timeout)
                response.raise_for_status()
                contents = response.json()
                items = contents.get("files", [])
                
                for item_path in items:
                    full_item_path = os.path.join(current_dir, item_path).replace("\\", "/")
                    if full_item_path.endswith("/"):
                        # It's a directory, add to scan queue
                        dirs_to_scan.append(full_item_path.rstrip('/'))
                    elif full_item_path.endswith(".md"):
                        # It's a markdown file, add to our collection
                        all_markdown_files.add(full_item_path)
                        
            except Exception as e:
                self.logger.error("Error fetching directory contents", SafeLogContext(
                    operation="directory_fetch",
                    status="failed",
                    metadata={
                        "directory": current_dir,
                        "error_type": type(e).__name__
                    }
                ))
                continue
        
        if not all_markdown_files:
            self.logger.warning("No markdown notes found", SafeLogContext(
                operation="notes_fetch",
                status="completed",
                metadata={"note_count": 0}
            ))
            return []
        
        final_list = sorted(list(all_markdown_files))
        self.logger.info("Notes fetch completed", SafeLogContext(
            operation="notes_fetch",
            status="completed",
            metadata={"note_count": len(final_list)}
        ))
        
        return final_list
    
    def _build_note_graph(self, markdown_files: List[str]) -> Dict[str, Any]:
        """Build a graph representation of notes and their links."""
        
        self.logger.info("Building note graph", SafeLogContext(
            operation="graph_build",
            status="started",
            metadata={"file_count": len(markdown_files)}
        ))
        
        # Map from full link path to full file path
        full_path_map = {}
        # Map from basename to possible full file paths
        basename_map = {}
        
        for note_path in markdown_files:
            link_path = os.path.splitext(note_path)[0]
            full_path_map[link_path] = note_path
            
            basename = os.path.splitext(os.path.basename(note_path))[0]
            if basename not in basename_map:
                basename_map[basename] = []
            basename_map[basename].append(note_path)
        
        # Build the graph structure
        note_links = {}
        note_backlinks = {}
        
        for note_path in markdown_files:
            try:
                # Get note content using the working endpoint from analyzer.py
                content = self.obsidian_client.get_note_content(note_path)
                if not content:
                    continue
                
                # Extract links from content
                links = self._extract_links_from_content(content)
                note_links[note_path] = links
                
                # Count backlinks
                for link in links:
                    target_path = None
                    # Try to resolve as full path first
                    if link in full_path_map:
                        target_path = full_path_map[link]
                    # Fall back to basename matching
                    elif link in basename_map:
                        target_path = basename_map[link][0]
                    
                    if target_path:
                        if target_path not in note_backlinks:
                            note_backlinks[target_path] = []
                        note_backlinks[target_path].append(note_path)
                        
            except Exception as e:
                self.logger.warning("Could not fetch note content", SafeLogContext(
                    operation="note_fetch",
                    status="failed",
                    metadata={
                        "note_path": note_path,
                        "error_type": type(e).__name__
                    }
                ))
                continue
        
        return {
            'notes': markdown_files,
            'note_links': note_links,
            'note_backlinks': note_backlinks,
            'full_path_map': full_path_map,
            'basename_map': basename_map
        }
    
    def _analyze_graph(self, graph: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the note graph to find patterns and issues."""
        notes = graph['notes']
        note_links = graph['note_links']
        note_backlinks = graph['note_backlinks']
        
        # Calculate totals
        total_links = sum(len(links) for links in note_links.values())
        
        # Identify orphan notes (no incoming links)
        orphans = []
        for note_path in notes:
            if note_path not in note_backlinks or not note_backlinks[note_path]:
                orphans.append(note_path)
        
        # Identify hub notes (many outgoing links)
        hub_threshold = params.get('hub_threshold', 10)
        hubs = []
        for note_path, links in note_links.items():
            if len(links) >= hub_threshold:
                hubs.append((note_path, len(links)))
        hubs.sort(key=lambda x: x[1], reverse=True)
        
        # Identify dead-end notes (no outgoing links)
        dead_ends = []
        for note_path in notes:
            if note_path in note_links and not note_links[note_path]:
                if note_path in note_backlinks and note_backlinks[note_path]:
                    dead_ends.append(note_path)
        
        # Identify low link density notes
        link_density_threshold = params.get('link_density_threshold', 0.02)
        min_word_count = params.get('min_word_count', 50)
        low_density_notes = []
        
        for note_path in notes:
            try:
                content = self.obsidian_client.get_note_content(note_path)
                if content:
                    word_count = len(content.split())
                    if word_count >= min_word_count:
                        link_count = len(note_links.get(note_path, []))
                        link_density = link_count / word_count if word_count > 0 else 0
                        if link_density < link_density_threshold:
                            low_density_notes.append((note_path, link_density))
            except:
                continue
        
        low_density_notes.sort(key=lambda x: x[1])
        
        # Identify stub links (links to non-existent notes)
        existing_notes = set(notes)
        stubs = set()
        for links in note_links.values():
            for link in links:
                if link not in existing_notes:
                    stubs.add(link)
        
        # Generate recommendations
        recommendations = self._generate_recommendations({
            'total_notes': len(notes),
            'total_links': total_links,
            'orphans': orphans,
            'hubs': hubs,
            'dead_ends': dead_ends,
            'low_density_notes': low_density_notes,
            'stubs': list(stubs)
        })
        
        return {
            'total_notes': len(notes),
            'total_links': total_links,
            'orphans': sorted(orphans),
            'hubs': hubs,
            'dead_ends': sorted(dead_ends),
            'low_density_notes': low_density_notes,
            'stubs': sorted(list(stubs)),
            'note_statistics': self._generate_note_statistics_from_paths(notes, note_links),
            'link_analysis': self._generate_link_analysis(note_links, note_backlinks),
            'folder_analysis': self._generate_folder_analysis_from_paths(notes),
            'tag_analysis': self._generate_tag_analysis_from_paths(notes),
            'recommendations': recommendations
        }
    
    def _analyze_folder_structure(self, folders: List[str]) -> Dict[str, Any]:
        """Analyze the vault folder structure."""
        folder_analysis = {
            'total_folders': len(folders),
            'folder_hierarchy': {},
            'folder_depths': {},
            'recommendations': []
        }
        
        # Analyze folder structure
        for folder in folders:
            depth = folder.count('/') if '/' in folder else 0
            folder_analysis['folder_depths'][folder] = depth
            
            # Build hierarchy
            parts = folder.split('/')
            current_level = folder_analysis['folder_hierarchy']
            for part in parts:
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]
        
        # Generate recommendations
        if len(folders) == 0:
            folder_analysis['recommendations'].append("No folders found. Consider organizing your vault with a folder structure.")
        elif len(folders) < 5:
            folder_analysis['recommendations'].append("Simple folder structure detected. Consider adding more organizational folders.")
        else:
            folder_analysis['recommendations'].append("Good folder structure detected. Vault appears well-organized.")
        
        return folder_analysis
    
    def _generate_note_statistics_from_paths(self, notes: List[str], note_links: Dict) -> Dict[str, Any]:
        """Generate statistics about notes from file paths."""
        total_words = 0
        total_chars = 0
        note_lengths = []
        
        for note_path in notes:
            try:
                content = self.obsidian_client.get_note_content(note_path)
                if content:
                    word_count = len(content.split())
                    char_count = len(content)
                    
                    total_words += word_count
                    total_chars += char_count
                    note_lengths.append(word_count)
            except:
                continue
        
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
    
    def _generate_folder_analysis_from_paths(self, notes: List[str]) -> Dict[str, Any]:
        """Generate analysis of folder structure from file paths."""
        folder_counts = {}
        folder_notes = {}
        
        for note_path in notes:
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
    
    def _generate_tag_analysis_from_paths(self, notes: List[str]) -> Dict[str, Any]:
        """Generate analysis of tags used in notes from file paths."""
        tag_counts = {}
        tag_notes = {}
        
        for note_path in notes:
            try:
                content = self.obsidian_client.get_note_content(note_path)
                if content:
                    # Extract tags (lines starting with #)
                    tags = re.findall(r'^#(\w+)', content, re.MULTILINE)
                    
                    for tag in tags:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
                        
                        if tag not in tag_notes:
                            tag_notes[tag] = []
                        tag_notes[tag].append(note_path)
            except:
                continue
        
        # Sort tags by usage count
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'tag_usage_counts': sorted_tags,
            'tag_notes': tag_notes,
            'total_unique_tags': len(tag_counts)
        }
    
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
