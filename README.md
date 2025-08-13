# Obsidian Tools

This project contains a Python script, `ObsidianAnalyzer.py`, that helps you manage and grow your Obsidian vault. It has two primary modes:

-   **Analyze Mode**: Analyzes the structure of your vault to find linking opportunities and structural issues.
-   **Ingest Mode**: Uses a Gemini LLM to read documents (`.txt`, `.pdf`) and automatically decompose them into atomic, Zettelkasten-style notes.

## Features

- Connects to a running Obsidian instance via the **Local REST API** plugin.
- Securely fetches the API key from **1Password** using its CLI.
- Builds a complete graph of all notes and their `[[wikilinks]]`.
- Generates a report identifying:
  - **Orphan Notes**: Notes that have no incoming links.
  - **Hub Notes**: Highly-connected notes that serve as entry points to topics.
  - **Dead-End Notes**: Notes that have incoming links but no outbound links.
  - **Low-Density Notes**: Notes that may be information silos, with few links for their size.
  - **Untapped Potential**: Unlinked mentions of other note titles.
  - **Stub Links**: Links that point to notes that do not yet exist.

## Setup

This script has a few prerequisites for connecting to your vault and securely managing credentials.

### 1. Install Python Dependencies

It is recommended to use a virtual environment.

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
pip install -r requirements.txt
```

### 2. 1Password CLI

This tool uses the [1Password CLI](https://developer.1password.com/docs/cli/get-started/) to securely fetch your Obsidian API key. You must have it installed and configured on your system.

You can test your setup by running `op account list`.

### 3. Gemini API Key

The `ingest` feature requires an API key for the Google Gemini LLM.
1.  Obtain an API key from Google AI Studio.
2.  Store this key securely in 1Password, just like your Obsidian API key.

### 4. Obsidian Local REST API Plugin

You must have the "Local REST API" community plugin installed and enabled in Obsidian.

### 5. Storing the API Key in 1Password

1.  In your 1Password vault, create a new item (e.g., an "API Credential" or "Login").
2.  Save your Obsidian Local REST API key in a field within this item.
3.  Right-click on the secret field and select **Copy Secret Reference**. This will copy a URI that looks like `op://<vault>/<item>/<field>`.

### 6. Environment Configuration

The script requires a `.env` file located inside the `.vscode` directory. This file is ignored by Git.

1.  Create a file named `.env` inside the `.vscode` folder.
2.  Add the following content, pasting the Secret Reference you copied from 1Password:

    ```.env
    OBSIDIAN_API_URL="http://127.0.0.1:27123"
    OBSIDIAN_API_KEY_REF="op://your-vault/your-item/your-secret-field"
    GEMINI_API_KEY_REF="op://your-vault/your-gemini-item/your-secret-field"

    # Default folder for new notes created by the ingest process
    NEW_NOTES_FOLDER="Inbox/Generated"
    ```

## Usage

The script operates in two modes: `analyze` and `ingest`.

### Analyze Mode

To run the existing vault analysis:

```bash
python ObsidianAnalyzer.py analyze
```

Or, if you are using VS Code, simply open the project and press `F5` to run the debugger.
