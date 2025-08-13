import sys
import os
import argparse
import logging
import re
from utils import (
    load_config,
    create_api_session,
    verify_connection,
)
from analyzer import (
    fetch_all_notes,
    build_note_graph,
    analyze_graph,
    print_report,
    run_analysis_process,
)
from ingest import run_ingest_process

TIMEOUT_SECONDS = 10


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

    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # --- Analyze Command ---
    parser_analyze = subparsers.add_parser("analyze", help="Analyze the structure of the vault.")
    parser_analyze.add_argument(
        "-o", "--output", type=str, help="Path to the output markdown file. Defaults to recommendations.md."
    )
    parser_analyze.add_argument(
        "--hub-threshold", type=int, default=10, help="Minimum outbound links for a note to be considered a hub. Default: 10."
    )
    parser_analyze.add_argument(
        "--link-density-threshold", type=float, default=0.02, help="Minimum link-to-word ratio. Default: 0.02."
    )
    parser_analyze.add_argument(
        "--min-word-count", type=int, default=50, help="Minimum word count for density analysis. Default: 50."
    )

    # --- Ingest Command ---
    parser_ingest = subparsers.add_parser("ingest", help="Decompose documents into new notes using an LLM.")
    parser_ingest.add_argument(
        "--ingest-folder", type=str, default="ingest", help="Folder containing documents to process. Default: 'ingest'."
    )
    parser_ingest.add_argument(
        "--notes-folder", type=str, help="Obsidian vault folder to save new notes. Overrides .env setting."
    )
    parser_ingest.add_argument(
        "--keep-files", action="store_true", help="Keep original files in ingest folder after processing. Default: files are deleted."
    )

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )

    api_url, obsidian_api_key, gemini_api_key, default_notes_folder = load_config()
    session = create_api_session(obsidian_api_key)
    verify_connection(session, api_url, TIMEOUT_SECONDS)

    if args.command == "analyze":
        output_file = args.output if args.output else "recommendations.md"
        run_analysis_process(
            session,
            api_url,
            TIMEOUT_SECONDS,
            output_file,
            args.hub_threshold,
            args.link_density_threshold,
            args.min_word_count,
        )

    elif args.command == "ingest":
        # Set the output folder for new notes, preferring the command-line arg
        notes_folder = args.notes_folder if args.notes_folder else default_notes_folder
        # Delete files after ingestion unless --keep-files flag is set
        delete_after_ingest = not args.keep_files
        run_ingest_process(
            args.ingest_folder,
            notes_folder,
            session,
            api_url,
            gemini_api_key,
            TIMEOUT_SECONDS,
            delete_after_ingest,
        )


if __name__ == "__main__":
    main()