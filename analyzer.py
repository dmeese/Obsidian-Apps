import sys
import os
import logging
import urllib.parse
import requests
import re
from collections import defaultdict
import ahocorasick
import networkx as nx
from typing import List, Dict, Any

WIKILINK_RE = re.compile(r"\[\[([^|\]]+)")


def fetch_all_notes(session, api_url: str, timeout: int) -> List[str]:
    """Fetches a list of all markdown files by recursively traversing the vault."""
    logging.info("Fetching all notes by recursively traversing the vault...")

    all_markdown_files: set[str] = set()
    # The queue will store directory paths WITHOUT trailing slashes.
    # The root is represented by an empty string.
    dirs_to_scan: list[str] = [""]
    scanned_dirs: set[str] = set()

    while dirs_to_scan:
        current_dir_no_slash = dirs_to_scan.pop(0)
        if current_dir_no_slash in scanned_dirs:
            continue
        scanned_dirs.add(current_dir_no_slash)

        logging.debug(f"Scanning directory: '{current_dir_no_slash if current_dir_no_slash else '/'}'")
        try:
            encoded_path = urllib.parse.quote(current_dir_no_slash)

            if encoded_path:
                list_url = f"{api_url}/vault/{encoded_path}/"
            else:
                list_url = f"{api_url}/vault/"

            response = session.get(list_url, timeout=timeout)
            response.raise_for_status()
            contents = response.json()
            items = contents.get("files", [])

            for item_path in items:
                full_item_path = os.path.join(current_dir_no_slash, item_path).replace("\\", "/")
                if full_item_path.endswith("/"):
                    dirs_to_scan.append(full_item_path.rstrip('/'))
                elif full_item_path.endswith(".md"):
                    all_markdown_files.add(full_item_path)
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching contents of directory '{current_dir_no_slash}/': {e}")
            continue

    if not all_markdown_files:
        logging.warning("No markdown notes found in the vault.")
        sys.exit(0)

    final_list = sorted(list(all_markdown_files))
    logging.info(f"Found {len(final_list)} markdown notes.")
    logging.debug(f"Full list of markdown files found: {final_list}")
    return final_list


def build_note_graph(
    session, api_url: str, markdown_files: List[str], timeout: int
) -> nx.DiGraph:
    """Builds a directed graph of notes and their links."""
    logging.info(f"Building note graph for {len(markdown_files)} files...")
    graph = nx.DiGraph()

    # Map from full link path (e.g., "Folder/Note") to full file path ("Folder/Note.md")
    full_path_map: Dict[str, str] = {}
    # Map from basename (e.g., "Note") to a list of possible full file paths
    basename_map: Dict[str, List[str]] = defaultdict(list)

    for note_path in markdown_files:
        graph.add_node(note_path, type="note")

        link_path = os.path.splitext(note_path)[0]
        full_path_map[link_path] = note_path

        basename = os.path.splitext(os.path.basename(note_path))[0]
        basename_map[basename].append(note_path)

    for i, note_path in enumerate(markdown_files):
        logging.debug(f"Processing note {i + 1}/{len(markdown_files)}: {note_path}")
        try:
            # Per API docs, use the /vault/{filename} endpoint to get note content.
            encoded_note_path = urllib.parse.quote(note_path)
            note_content_response = session.get(
                f"{api_url}/vault/{encoded_note_path}",
                headers={"Accept": "text/markdown"},
                timeout=timeout,
            )
            note_content_response.raise_for_status()
            content = note_content_response.text
            graph.nodes[note_path]['content'] = content

            for link_target in WIKILINK_RE.findall(content):
                target_path = None
                # 1. Try to resolve as a full path (e.g., "Folder/My Note")
                if link_target in full_path_map:
                    target_path = full_path_map[link_target]
                # 2. If not, try as a basename. If multiple notes share a name,
                # this will pick the first one found, which is a reasonable default.
                elif link_target in basename_map:
                    target_path = basename_map[link_target][0]

                if target_path:
                    graph.add_edge(note_path, target_path)
                else:
                    # Link to a non-existent note (a stub)
                    if not graph.has_node(link_target):
                        graph.add_node(link_target, type="stub")
                    graph.add_edge(note_path, link_target)
        except requests.exceptions.RequestException as e:
            logging.warning(f"Could not fetch content for '{note_path}': {e}")

    logging.info("Graph construction complete.")
    return graph


def analyze_graph(
    graph: nx.DiGraph, hub_threshold: int, link_density_threshold: float, min_word_count: int
) -> Dict[str, Any]:
    """Analyzes the graph to find orphans, stubs, and their sources."""
    logging.info("Analyzing note graph...")
    all_nodes = list(graph.nodes(data=True))
    notes = [n for n, d in all_nodes if d.get("type") == "note"]
    stubs = [n for n, d in all_nodes if d.get("type") == "stub"]

    in_degrees = graph.in_degree(notes)
    orphans = [node for node, degree in in_degrees if degree == 0]

    out_degrees = graph.out_degree(notes)
    hubs = [node for node, degree in out_degrees if degree >= hub_threshold]
    dead_ends = [
        node for node, degree in out_degrees if degree == 0 and graph.in_degree(node) > 0
    ]

    # --- Untapped Potential Analysis (Aho-Corasick) ---
    untapped_potential: Dict[str, List[str]] = defaultdict(list)
    all_titles = {os.path.splitext(os.path.basename(n))[0] for n in notes}

    # Build the Aho-Corasick automaton for case-insensitive matching.
    # We store the lowercase title as the key and the canonical title as the value.
    auto = ahocorasick.Automaton()
    lower_to_canonical_map = {title.lower(): title for title in all_titles}
    for lower_title, canonical_title in lower_to_canonical_map.items():
        auto.add_word(lower_title, canonical_title)
    auto.make_automaton()

    for source_note_path in notes:
        source_content = graph.nodes[source_note_path].get('content', '')
        if not source_content:
            continue

        # Find all titles mentioned by searching the lowercased content.
        # The automaton will yield the original, canonical title.
        found_titles = {value for end_index, value in auto.iter(source_content.lower())}

        # Determine which of the found titles are potential new links
        existing_link_titles = {os.path.splitext(os.path.basename(target))[0] for target in graph.successors(source_note_path)}
        source_title = os.path.splitext(os.path.basename(source_note_path))[0]
        
        potential_new_links = found_titles - existing_link_titles - {source_title}

        if potential_new_links:
            untapped_potential[source_note_path] = sorted(list(potential_new_links))

    # --- Low Link Density Analysis ---
    low_density_notes = []
    for note_path in notes:
        word_count = len(graph.nodes[note_path].get('content', '').split())
        if word_count >= min_word_count:
            if word_count > 0 and (graph.out_degree(note_path) / word_count) < link_density_threshold:
                low_density_notes.append(note_path)

    stub_sources = {
        stub_name: sorted(list(graph.predecessors(stub_name)))
        for stub_name in stubs
    }

    return {
        "total_notes": len(notes),
        "total_links": graph.number_of_edges(),
        "orphans": sorted(orphans),
        "hubs": sorted(hubs),
        "dead_ends": sorted(dead_ends),
        "low_density_notes": sorted(low_density_notes),
        "untapped_potential": untapped_potential,
        "stubs": sorted(stubs),
        "stub_sources": stub_sources,
    }


def print_report(
    analysis: Dict[str, Any], hub_threshold: int, output_stream=sys.stdout
) -> None:
    """Prints the final analysis report to the console or a file."""

    def write_line(text: str = ""):
        output_stream.write(text + "\n")

    write_line("# Obsidian Vault Analysis Report")
    write_line()
    write_line(f"**Total Notes:** {analysis['total_notes']}")
    write_line(f"**Total Links Found:** {analysis['total_links']}")
    write_line()
    write_line("---")

    orphans = analysis["orphans"]
    write_line()
    write_line(f"## Orphan Notes ({len(orphans)})")
    print("\n".join(f"- `{n}`" for n in orphans) if orphans else "None found.", file=output_stream)

    hubs = analysis["hubs"]
    write_line()
    write_line(f"## Hub Notes (>{hub_threshold-1} outbound links) ({len(hubs)})")
    print("\n".join(f"- `{n}`" for n in hubs) if hubs else "None found.", file=output_stream)

    dead_ends = analysis["dead_ends"]
    write_line()
    write_line(f"## Dead-End Notes (has links in, but no links out) ({len(dead_ends)})")
    print("\n".join(f"- `{n}`" for n in dead_ends) if dead_ends else "None found.", file=output_stream)

    low_density_notes = analysis["low_density_notes"]
    write_line()
    write_line(f"## Low Link Density Notes (potential info silos) ({len(low_density_notes)})")
    print("\n".join(f"- `{n}`" for n in low_density_notes) if low_density_notes else "None found.", file=output_stream)

    untapped_potential = analysis["untapped_potential"]
    write_line()
    write_line(f"## Untapped Potential (unlinked mentions) ({len(untapped_potential)})")
    if untapped_potential:
        for source_note, suggestions in untapped_potential.items():
            write_line(f"\n- In `{source_note}`, consider linking to:")
            for suggestion in suggestions:
                write_line(f"  - `{suggestion}`")
    else:
        write_line("None found.")

    stubs = analysis["stubs"]
    stub_sources = analysis["stub_sources"]
    write_line()
    write_line(f"## Stub Links (to non-existent notes) ({len(stubs)})")
    if stubs:
        for stub_name in stubs:
            write_line(f"\n- `{stub_name}` is linked from:")
            for p in stub_sources.get(stub_name, []):
                write_line(f"  - `{p}`")
    else:
        write_line("None found.")
    write_line("\n---")


def run_analysis_process(
    session,
    api_url: str,
    timeout: int,
    output_file: str,
    hub_threshold: int,
    link_density_threshold: float,
    min_word_count: int,
):
    """Orchestrates the vault analysis and report generation."""
    markdown_files = fetch_all_notes(session, api_url, timeout)
    graph = build_note_graph(session, api_url, markdown_files, timeout)
    analysis = analyze_graph(
        graph, hub_threshold, link_density_threshold, min_word_count
    )

    logging.info(f"Writing report to {output_file}...")
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            print_report(analysis, hub_threshold=hub_threshold, output_stream=f)
        logging.info(f"Report successfully written to {output_file}")
    except IOError as e:
        logging.error(f"Could not write report to file {output_file}: {e}")
        sys.exit(1)