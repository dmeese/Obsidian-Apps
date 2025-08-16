import sys
import os
import logging
import subprocess
import requests
from dotenv import load_dotenv
from typing import Tuple, Dict

# Import secure logging from centralized module
from secure_logging import ZeroSensitiveLogger, SafeLogContext

# Initialize zero-sensitive logger
logger = ZeroSensitiveLogger("utils")


def load_config() -> Tuple[str, str, str, str]:
    """Loads configuration and fetches the API key from 1Password."""
    # Look for the .env file inside the .vscode directory
    project_root = os.path.dirname(__file__)
    dotenv_path = os.path.join(project_root, ".vscode", ".env")

    if not os.path.exists(dotenv_path):
        logger.error("Configuration file not found", SafeLogContext(
            operation="config_load",
            status="failed",
            metadata={"file_path": dotenv_path, "error_type": "file_not_found"}
        ))
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
        logger.error("Required environment variables missing", SafeLogContext(
            operation="config_validate",
            status="failed",
            metadata={"missing_vars": missing_vars, "config_file": dotenv_path}
        ))
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
        logger.error("1Password CLI not found", SafeLogContext(
            operation="1password_fetch",
            status="failed",
            metadata={"error_type": "FileNotFoundError", "cli_tool": "op"}
        ))
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        logger.error("Error fetching secret from 1Password", SafeLogContext(
            operation="1password_fetch",
            status="failed",
            metadata={"error_type": "CalledProcessError", "stderr_length": len(e.stderr) if e.stderr else 0}
        ))
        sys.exit(1)


def create_api_session(api_key: str) -> requests.Session:
    """Creates a requests.Session with the necessary auth headers."""
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {api_key}"})
    return session


def verify_connection(session: requests.Session, api_url: str, timeout: int) -> None:
    """Verifies connection to the Obsidian API and prints vault info."""
    try:
        logger.log_api_operation("GET", api_url, "connecting", has_auth=True)
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

            logger.log_api_operation("GET", api_url, "success", has_auth=True, response_size=len(response.text))
            logger.info("Successfully connected to Obsidian API", SafeLogContext(
                operation="connection_verify",
                status="success",
                metadata={
                    "service_name": service_name,
                    "obsidian_version": obsidian_version,
                    "api_version": api_version
                }
            ))

        except (requests.exceptions.JSONDecodeError, ValueError):
            logger.error("API response format invalid", SafeLogContext(
                operation="connection_verify",
                status="failed",
                metadata={
                    "error_type": "InvalidResponseFormat",
                    "response_size": len(response.text),
                    "endpoint": api_url
                }
            ))
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        logger.error("Vault connection failed", SafeLogContext(
            operation="connection_verify",
            status="failed",
            metadata={
                "error_type": type(e).__name__,
                "endpoint": api_url,
                "timeout": timeout
            }
        ))
        sys.exit(1)