import sys
import os
import requests
from dotenv import load_dotenv

def main():
    """
    Connects to the Obsidian Local REST API, verifies the connection,
    and prepares for vault analysis.
    """
    # Load environment variables from .env file
    load_dotenv()

    # --- 1. Load Configuration ---
    api_url = os.getenv("OBSIDIAN_API_URL")
    api_key = os.getenv("OBSIDIAN_API_KEY")

    if not api_url or not api_key:
        print(
            "Error: OBSIDIAN_API_URL and OBSIDIAN_API_KEY must be set in your .env file.",
            file=sys.stderr,
        )
        sys.exit(1)

    # --- 2. Prepare API Client ---
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "text/markdown",
    }

    # --- 3. Verify Connection ---
    try:
        print(f"Connecting to Obsidian API at {api_url}...")
        response = requests.get(api_url, headers=headers, timeout=5)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)

        # The base endpoint returns a JSON object with vault info
        vault_info = response.json()
        print(f"Successfully connected to vault: {vault_info.get('name')}")
        print(f"Obsidian version: {vault_info.get('obsidianVersion')}, API version: {vault_info.get('version')}")

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to the Obsidian API: {e}", file=sys.stderr)
        print("Please ensure Obsidian is running and the Local REST API plugin is enabled.", file=sys.stderr)
        sys.exit(1)

    # --- 4. Future Analysis Steps (as per PRD) ---
    # TODO: Fetch all notes using a GET request to /vault/
    # TODO: Build in-memory graph of notes and links.
    # TODO: Perform link analysis (orphans, stubs, etc.).
    # TODO: Generate and print the final report.

if __name__ == "__main__":
    main()