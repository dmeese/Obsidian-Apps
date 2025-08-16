import sys
import os
import logging
import subprocess
import requests
from dotenv import load_dotenv
from typing import Tuple, Dict

# Import secure logging from centralized module
from secure_logging import secure_log


def load_config() -> Tuple[str, str, str, str]:
    """Loads configuration and fetches the API key from 1Password."""
    # Look for the .env file inside the .vscode directory
    project_root = os.path.dirname(__file__)
    dotenv_path = os.path.join(project_root, ".vscode", ".env")

    if not os.path.exists(dotenv_path):
        secure_log("error", f"Configuration file not found at '{dotenv_path}'")
        sys.exit(1)

    load_dotenv(dotenv_path=dotenv_path)

    api_url = os.getenv("OBSIDIAN_API_URL")
    api_key_ref = os.getenv("OBSIDIAN_API_KEY_REF")
    gemini_key_ref = os.getenv("GEMINI_API_KEY_REF")
    new_notes_folder = os.getenv("NEW_NOTES_FOLDER", "GeneratedNotes")

    required_vars = {
        "OBSIDIAN_API_URL": api_url,
        "OBSIDIAN_API_KEY_REF": api_key_ref,
        "GEMINI_API_KEY_REF": gemini_key_ref,
    }
    missing_vars = [var for var, value in required_vars.items() if not value]
    if missing_vars:
        secure_log("error", "The following required environment variables are missing from your .vscode/.env file:")
        for var in missing_vars:
            secure_log("error", f"  - {var}")
        sys.exit(1)

    obsidian_api_key = fetch_api_key_from_1password(api_key_ref)
    gemini_api_key = fetch_api_key_from_1password(gemini_key_ref)

    return api_url, obsidian_api_key, gemini_api_key, new_notes_folder


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
        secure_log("error",
            "1Password CLI ('op') not found. Please install it from https://developer.1password.com/docs/cli/"
        )
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        secure_log("error", f"Error fetching secret from 1Password:\n{e.stderr}")
        sys.exit(1)


def create_api_session(api_key: str) -> requests.Session:
    """Creates a requests.Session with the necessary auth headers."""
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {api_key}"})
    return session


def verify_connection(session: requests.Session, api_url: str, timeout: int) -> None:
    """Verifies connection to the Obsidian API and prints vault info."""
    try:
        secure_log("info", f"Connecting to Obsidian API at {api_url}...")
        response = session.get(api_url, timeout=timeout)
        response.raise_for_status()

        try:
            api_info = response.json()
            if not ("service" in api_info and "versions" in api_info):
                raise ValueError("Missing expected keys in API response.")

            service_name = api_info.get("service")
            obsidian_version = api_info.get("versions", {}).get("obsidian")
            api_version = api_info.get("versions", {}).get("self")

            if not all([service_name, obsidian_version, api_version]):
                raise ValueError("Incomplete version/manifest info in API response.")

            secure_log("info", f"Successfully connected to service: '{service_name}'")
            secure_log("info", f"Obsidian v{obsidian_version}, API v{api_version}")

        except (requests.exceptions.JSONDecodeError, ValueError):
            secure_log("error", "The API response from the root endpoint was not in the expected format.")
            secure_log("error", "Please ensure the Obsidian Local REST API plugin is up-to-date and enabled correctly.")
            # Redact response body to avoid logging sensitive content
            secure_log("error", f"Received response body: [REDACTED - {len(response.text)} characters]")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        secure_log("error", f"Error during vault connection: {e}")
        secure_log("error", "Please ensure Obsidian is running and the Local REST API plugin is enabled.")
        sys.exit(1)