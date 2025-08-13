import sys
import os
import argparse
import logging
import re
import subprocess
import requests
import urllib.parse
from collections import defaultdict
import ahocorasick
import networkx as nx
from dotenv import load_dotenv
from typing import List, Tuple, Dict, Any

WIKILINK_RE = re.compile(r"\[\[([^|\]]+)")
TIMEOUT_SECONDS = 10


def load_config() -> Tuple[str, str]:
    """Loads configuration and fetches the API key from 1Password."""
    # Look for the .env file inside the .vscode directory
    project_root = os.path.dirname(__file__)
    dotenv_path = os.path.join(project_root, ".vscode", ".env")

    if not os.path.exists(dotenv_path):
        logging.error(f"Configuration file not found at '{dotenv_path}'")
        sys.exit(1)

    load_dotenv(dotenv_path=dotenv_path)

    api_url = os.getenv("OBSIDIAN_API_URL")
    api_key_ref = os.getenv("OBSIDIAN_API_KEY_REF")

    if not all([api_url, api_key_ref]):
        logging.error(
            "OBSIDIAN_API_URL and OBSIDIAN_API_KEY_REF must be set in your .vscode/.env file."
        )
        sys.exit(1)

    api_key = fetch_api_key_from_1password(api_key_ref)
    return api_url, api_key


def fetch_api_key_from_1password(secret_reference: str) -> str:
    """Fetches a secret from 1Password using the op CLI."""
    try:
        result = subprocess.run(
            ["op", "read", secret_reference],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except FileNotFoundError:
        logging.error(
            "1Password CLI ('op') not found. Please install it from https://developer.1password.com/docs/cli/"
        )
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error fetching secret from 1Password:\n{e.stderr}")
        sys.exit(1)


def create_api_session(api_key: str) -> requests.Session:
    """Creates a requests.Session with the necessary auth headers."""
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {api_key}"})
    return session


def verify_connection(session: requests.Session, api_url: str) -> None:
    """Verifies connection to the Obsidian API and prints vault info."""
    try:
        logging.info(f"Connecting to Obsidian API at {api_url}...")
        response = session.get(api_url, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()

        try:
            api_info = response.json()
            # Check for the structure of newer API versions
            if not ("service" in api_info and "versions" in api_info):
                raise ValueError("Missing expected keys in API response.")

            service_name = api_info.get("service")
            obsidian_version = api_info.get("versions", {}).get("obsidian")
            api_version = api_info.get("versions", {}).get("self")

            if not all([service_name, obsidian_version, api_version]):
                raise ValueError("Incomplete version/manifest info in API response.")

            logging.info(f"Successfully connected to service: '{service_name}'")
            logging.info(f"Obsidian v{obsidian_version}, API v{api_version}")

        except (requests.exceptions.JSONDecodeError, ValueError):
            logging.error("The API response from the root endpoint was not in the expected format.")
            logging.error("Please ensure the Obsidian Local REST API plugin is up-to-date and enabled correctly.")
            logging.error(f"Received response body: {response.text}")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        logging.error(f"Error during vault connection: {e}")
        logging.error("Please ensure Obsidian is running and the Local REST API plugin is enabled.")
        sys.exit(1)


def fetch_all_notes(session: requests.Session, api_url: str) -> List[str]:
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

            # For subdirectories, the API endpoint needs a trailing slash.
            # The root endpoint is just /vault/
            if encoded_path:
                list_url = f"{api_url}/vault/{encoded_path}/"
            else:
                list_url = f"{api_url}/vault/"

            response = session.get(list_url, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            contents = response.json()
            items = contents.get("files", [])

            for item_path in items:
                # The API returns paths relative to the directory being scanned.
                # We must join them to build the full path from the vault root.
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
    session: requests.Session, api_url: str, markdown_files: List[str]
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
                timeout=TIMEOUT_SECONDS,
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

    # Build the Aho-Corasick automaton once with all possible titles
    auto = ahocorasick.Automaton()
    for title in all_titles:
        # Store the canonical title as the value for the keyword
        auto.add_word(title, title)
    auto.make_automaton()

    for source_note_path in notes:
        source_content = graph.nodes[source_note_path].get('content', '')
        if not source_content:
            continue

        # Find all titles mentioned in the current note's content
        found_titles = {value for end_index, value in auto.iter(source_content, case_insensitive=True)}

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
            if (graph.out_degree(note_path) / word_count) < link_density_threshold:
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


def main() -> None:
    """Main function to orchestrate the vault analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze an Obsidian vault for orphans and stubs."
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG) logging output.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Path to the output markdown file. Defaults to recommendations.md.",
    )
    parser.add_argument(
        "--hub-threshold",
        type=int,
        default=10,
        help="Minimum outbound links for a note to be considered a hub. Default: 10.",
    )
    parser.add_argument(
        "--link-density-threshold",
        type=float,
        default=0.02,
        help="Minimum link-to-word ratio to avoid being flagged as low-density. Default: 0.02 (2 links per 100 words).",
    )
    parser.add_argument(
        "--min-word-count",
        type=int,
        default=50,
        help="Minimum word count for a note to be considered for link-density analysis. Default: 50.",
    )
    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )

    api_url, api_key = load_config()
    session = create_api_session(api_key)

    verify_connection(session, api_url)
    markdown_files = fetch_all_notes(session, api_url)
    graph = build_note_graph(session, api_url, markdown_files)
    analysis = analyze_graph(
        graph,
        hub_threshold=args.hub_threshold,
        link_density_threshold=args.link_density_threshold,
        min_word_count=args.min_word_count,
    )

    output_file = args.output if args.output else "recommendations.md"
    logging.info(f"Writing report to {output_file}...")
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            print_report(analysis, hub_threshold=args.hub_threshold, output_stream=f)
        logging.info(f"Report successfully written to {output_file}")
    except IOError as e:
        logging.error(f"Could not write report to file {output_file}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()