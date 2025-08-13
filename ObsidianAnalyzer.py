import sys
import os
import re
import requests
import networkx as nx
from dotenv import load_dotenv
from typing import List, Tuple, Dict, Any

WIKILINK_RE = re.compile(r"\[\[([^|\]]+)")
TIMEOUT_SECONDS = 10


def load_config() -> Tuple[str, str]:
    """Loads API configuration from .env file and exits if not found."""
    load_dotenv()
    api_url = os.getenv("OBSIDIAN_API_URL")
    api_key = os.getenv("OBSIDIAN_API_KEY")

    if not api_url or not api_key:
        print(
            "Error: OBSIDIAN_API_URL and OBSIDIAN_API_KEY must be set in your .env file.",
            file=sys.stderr,
        )
        sys.exit(1)
    return api_url, api_key


def create_api_session(api_key: str) -> requests.Session:
    """Creates a requests.Session with the necessary auth headers."""
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {api_key}"})
    return session


def verify_connection(session: requests.Session, api_url: str) -> None:
    """Verifies connection to the Obsidian API and prints vault info."""
    try:
        print(f"Connecting to Obsidian API at {api_url}...")
        response = session.get(api_url, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()  # Raises an HTTPError for bad responses

        vault_info = response.json()
        print(f"Successfully connected to vault: '{vault_info.get('name')}'")
        print(
            f"Obsidian version: {vault_info.get('obsidianVersion')}, "
            f"API version: {vault_info.get('version')}"
        )
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to the Obsidian API: {e}", file=sys.stderr)
        print(
            "Please ensure Obsidian is running and the Local REST API plugin is enabled.",
            file=sys.stderr,
        )
        sys.exit(1)


def fetch_all_notes(session: requests.Session, api_url: str) -> List[str]:
    """Fetches a list of all markdown files from the vault."""
    print("\nFetching all notes from the vault...")
    try:
        notes_response = session.get(f"{api_url}/vault/", timeout=TIMEOUT_SECONDS)
        notes_response.raise_for_status()
        all_files = notes_response.json().get("files", [])

        markdown_files = [path for path in all_files if path.endswith(".md")]
        if not markdown_files:
            print("No markdown notes found in the vault.")
            sys.exit(0)

        print(f"Found {len(markdown_files)} markdown notes.")
        return markdown_files
    except requests.exceptions.RequestException as e:
        print(f"Error fetching notes: {e}", file=sys.stderr)
        sys.exit(1)
    except (KeyError, TypeError):
        print(
            "Error: Unexpected response format from API when fetching notes.",
            file=sys.stderr,
        )
        print(
            "Expected a JSON object with a 'files' key containing a list.",
            file=sys.stderr,
        )
        sys.exit(1)


def build_note_graph(
    session: requests.Session, api_url: str, markdown_files: List[str]
) -> nx.DiGraph:
    """Builds a directed graph of notes and their links."""
    print("Building note graph (this may take a moment)...")
    graph = nx.DiGraph()
    note_basenames: Dict[str, str] = {}  # Map basenames (without .md) to full paths

    for note_path in markdown_files:
        basename = os.path.splitext(os.path.basename(note_path))[0]
        graph.add_node(note_path, type="note")
        note_basenames[basename] = note_path

    for i, note_path in enumerate(markdown_files):
        print(
            f"  Processing note {i + 1}/{len(markdown_files)}: {os.path.basename(note_path)}...",
            end="\r",
            flush=True,
        )
        try:
            note_content_response = session.get(
                f"{api_url}/vault/{note_path}",
                headers={"Accept": "text/markdown"},
                timeout=TIMEOUT_SECONDS,
            )
            note_content_response.raise_for_status()
            content = note_content_response.text

            for link_basename in WIKILINK_RE.findall(content):
                target_path = note_basenames.get(link_basename)
                if target_path:
                    graph.add_edge(note_path, target_path)
                else:
                    # Link to a non-existent note (a stub)
                    if not graph.has_node(link_basename):
                        graph.add_node(link_basename, type="stub")
                    graph.add_edge(note_path, link_basename)
        except requests.exceptions.RequestException as e:
            print(" " * 80, end="\r")  # Clear the line
            print(f"\nWarning: Could not fetch content for '{note_path}': {e}")

    print(" " * 80, end="\r")  # Clear the final progress line
    print("Graph construction complete.")
    return graph


def analyze_graph(graph: nx.DiGraph) -> Dict[str, Any]:
    """Analyzes the graph to find orphans, stubs, and their sources."""
    print("Analyzing note graph...")
    all_nodes = list(graph.nodes(data=True))
    notes = [n for n, d in all_nodes if d.get("type") == "note"]
    stubs = [n for n, d in all_nodes if d.get("type") == "stub"]

    in_degrees = graph.in_degree(notes)
    orphans = [node for node, degree in in_degrees if degree == 0]

    stub_sources: Dict[str, List[str]] = {}
    for stub_name in stubs:
        stub_sources[stub_name] = sorted(list(graph.predecessors(stub_name)))

    return {
        "total_notes": len(notes),
        "total_links": graph.number_of_edges(),
        "orphans": sorted(orphans),
        "stubs": sorted(stubs),
        "stub_sources": stub_sources,
    }


def print_report(analysis: Dict[str, Any]) -> None:
    """Prints the final analysis report to the console."""
    print("\n--- Obsidian Vault Analysis Report ---")
    print(f"Total Notes: {analysis['total_notes']}")
    print(f"Total Links Found: {analysis['total_links']}")
    print("-" * 35)

    orphans = analysis["orphans"]
    print(f"Orphan Notes ({len(orphans)}):")
    print("\n".join(f"  - {n}" for n in orphans) if orphans else "  None found.")

    stubs = analysis["stubs"]
    stub_sources = analysis["stub_sources"]
    print(f"\nStub Links (to non-existent notes) ({len(stubs)}):")
    if stubs:
        for stub_name in stubs:
            print(f"  - '{stub_name}' is linked from:")
            for p in stub_sources.get(stub_name, []):
                print(f"    - {p}")
    else:
        print("  None found.")
    print("\n--- End of Report ---")


def main() -> None:
    """Main function to orchestrate the vault analysis."""
    api_url, api_key = load_config()
    session = create_api_session(api_key)

    verify_connection(session, api_url)
    markdown_files = fetch_all_notes(session, api_url)
    graph = build_note_graph(session, api_url, markdown_files)
    analysis = analyze_graph(graph)
    print_report(analysis)


if __name__ == "__main__":
    main()