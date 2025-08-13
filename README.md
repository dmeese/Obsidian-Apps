# Obsidian Tools

This project contains a Python script, `ObsidianAnalyzer.py`, that analyzes the structure of an Obsidian vault to help with knowledge base maintenance.

## Features

- Connects to a running Obsidian instance via the **Local REST API** plugin.
- Securely fetches the API key from **1Password** using its CLI.
- Builds a complete graph of all notes and their `[[wikilinks]]`.
- Generates a report identifying:
  - **Orphan Notes**: Notes that have no incoming links.
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

### 3. Obsidian Local REST API Plugin

You must have the "Local REST API" community plugin installed and enabled in Obsidian.

### 4. Storing the API Key in 1Password

1.  In your 1Password vault, create a new item (e.g., an "API Credential" or "Login").
2.  Save your Obsidian Local REST API key in a field within this item.
3.  Right-click on the secret field and select **Copy Secret Reference**. This will copy a URI that looks like `op://<vault>/<item>/<field>`.

### 5. Environment Configuration

The script requires a `.env` file located inside the `.vscode` directory. This file is ignored by Git.

1.  Create a file named `.env` inside the `.vscode` folder.
2.  Add the following content, pasting the Secret Reference you copied from 1Password:

    ```
    OBSIDIAN_API_URL="http://127.0.0.1:27123"
    OBSIDIAN_API_KEY_REF="op://your-vault/your-item/your-secret-field"
    ```

## Usage

Once setup is complete, you can run the analyzer from your terminal:

```bash
python ObsidianAnalyzer.py
```

Or, if you are using VS Code, simply open the project and press `F5` to run the debugger.