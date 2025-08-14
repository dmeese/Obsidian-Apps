import sys
import os
import logging
import re
import json
import urllib.parse
import requests
import google.generativeai as genai
from pypdf import PdfReader
from typing import List, Dict, TypedDict, Literal


class Note(TypedDict):
    """Represents a note with title, content, and type."""
    title: str
    content: str
    type: Literal["atomic", "structure"]


def read_file_content(file_path: str) -> str:
    """Reads content from a .txt or .pdf file."""
    logging.info(f"Reading content from {file_path}...")
    try:
        if file_path.lower().endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        elif file_path.lower().endswith(".pdf"):
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        else:
            logging.warning(f"Unsupported file type: {file_path}. Skipping.")
            return ""
    except Exception as e:
        logging.error(f"Failed to read file {file_path}: {e}")
        return ""


def clean_wikilinks(content: str) -> str:
    """
    Clean wikilinks by removing surrounding quotes and ensuring proper format.
    Fixes issues like '[[Note Title]]' -> [[Note Title]]
    """
    import re
    
    # Remove single quotes around wikilinks
    content = re.sub(r"'\[\[([^\]]+)\]\]'", r'[[\1]]', content)
    
    # Remove double quotes around wikilinks
    content = re.sub(r'"\[\[([^\]]+)\]\]"', r'[[\1]]', content)
    
    # Remove backticks around wikilinks
    content = re.sub(r'`\[\[([^\]]+)\]\]`', r'[[\1]]', content)
    
    # Clean up extra spaces in wikilinks - use a more comprehensive approach
    def clean_spaces_in_wikilink(match):
        # Extract the content between brackets and strip all whitespace
        inner_content = match.group(1).strip()
        return f'[[{inner_content}]]'
    
    # Apply the cleaning function to all wikilinks
    content = re.sub(r'\[\[([^\]]+)\]\]', clean_spaces_in_wikilink, content)
    
    return content


def analyze_with_gemini(model, text_content: str) -> List[Note]:
    """
    Sends text to Gemini to be decomposed into an interconnected set of
    evergreen-style notes for Obsidian.
    """
    if not text_content.strip():
        logging.warning("Skipping Gemini analysis for empty content.")
        return []

    logging.info("Sending content to Gemini for analysis. This may take a moment...")

    # --- START OF REVISED PROMPT ---
    prompt = f"""
    You are a digital knowledge architect. Your expertise is in Zettelkasten, evergreen notes, and building robust personal knowledge management (PKM) systems. Your goal is to transform the provided text into a rich, interconnected network of notes.

    **Core Task:**
    Analyze the following text and decompose it into a series of notes. Critically, you must then establish connections BETWEEN these notes by embedding `[[wikilinks]]` in their content.

    **Guidelines:**
    1.  **Note Types:**
        -   **Atomic Notes:** The majority of notes should be 'atomic,' focusing on a single, core idea.
        -   **Structure Notes:** If the text covers a broad topic with several distinct sub-concepts, you MUST generate a "Structure Note." This note serves as a hub or Map of Content (MOC). Its content should be a brief summary of the topic and a list of `[[wikilinks]]` pointing to the relevant atomic notes you are creating.

    2.  **Connectivity is Key:**
        -   For every note you generate, actively look for concepts that are mentioned in other notes from this same batch.
        -   When you find a connection, embed a markdown wikilink, like `[[Title of the Other Note]]`, directly into the content.
        -   **CRITICAL: Wikilinks must be in the exact format [[Note Title]] with NO quotes, backticks, or other characters around the brackets.**
        -   The link text MUST EXACTLY match the title of the note you are linking to.

    3.  **Note Content:**
        -   Titles must be concise, declarative statements of the core concept.
        -   Content should be written in your own words, in clear, simple language, as if explaining the concept to an intelligent peer.
        -   Use standard markdown for formatting (e.g., lists, bolding).

    **Output Format:**
    You MUST return your response as a single, valid JSON array `[]`. Do not include markdown fences (\`\`\`json) or any other text outside the array. Each object in the array represents one note and must have the following structure:
    `{{ "title": "A Concise, Declarative Title", "content": "The full markdown content of the note, including [[wikilinks]] to other notes.", "type": "atomic" or "structure" }}`

    **Text to Analyze:**
    ---
    {text_content}
    ---
    """
    # --- END OF REVISED PROMPT ---

    try:
        response = model.generate_content(prompt)
        # Modern models are better at strict JSON output, so complex cleaning is often less necessary.
        # A simple strip is usually sufficient if the prompt is strong.
        cleaned_response = response.text.strip()

        # Handle cases where the model might still wrap the output in markdown fences
        if cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[7:-3].strip()
        elif cleaned_response.startswith("`"):
            cleaned_response = cleaned_response.strip("`")

        try:
            return json.loads(cleaned_response)
        except json.JSONDecodeError:
            logging.error("Failed to parse JSON response from Gemini.")
            logging.debug(f"Invalid JSON received: {cleaned_response}")
            return []

    except Exception as e:
        logging.error(f"An error occurred during Gemini API call: {e}")
        return []


def create_notes_in_vault(
    session: requests.Session,
    api_url: str,
    notes_to_create: List[Note],
    output_folder: str,
    timeout: int,
):
    """Creates new notes in the Obsidian vault using the API."""
    if not notes_to_create:
        logging.info("No new notes to create.")
        return

    logging.info(f"Creating {len(notes_to_create)} new notes in vault...")
    for note in notes_to_create:
        title = note.get("title")
        content = note.get("content")
        note_type = note.get("type", "atomic")  # Default to atomic if type is missing

        if not title or not content:
            logging.warning(f"Skipping note with missing title or content: {note}")
            continue

        # Clean wikilinks to remove quotes and ensure proper format
        original_content = content
        content = clean_wikilinks(content)
        
        # Log if any wikilinks were cleaned
        if original_content != content:
            logging.info(f"Cleaned wikilinks in note '{title}'")
        
        logging.info(f"Creating {note_type} note: {title}")

        # Sanitize title to create a valid filename
        sanitized_title = re.sub(r'[\\/*?:"<>|]', "", title)
        note_path = os.path.join(output_folder, f"{sanitized_title}.md").replace("\\", "/")

        try:
            logging.info(f"Creating note: {note_path}")
            encoded_path = urllib.parse.quote(note_path)
            response = session.put(
                f"{api_url}/vault/{encoded_path}",
                data=content.encode("utf-8"),
                headers={"Content-Type": "text/markdown"},
                timeout=timeout,
            )
            response.raise_for_status()
            
            # Log connectivity information
            wikilinks = re.findall(r'\[\[([^\]]+)\]\]', content)
            if wikilinks:
                logging.info(f"Note '{title}' contains {len(wikilinks)} wikilinks: {', '.join(wikilinks)}")
            else:
                logging.info(f"Note '{title}' has no wikilinks")
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to create note '{note_path}': {e}")


def run_ingest_process(
    ingest_folder: str,
    notes_folder: str,
    session,
    api_url: str,
    gemini_api_key: str,
    timeout: int,
    delete_after_ingest: bool = True,
    model_name: str = "gemini-2.5-flash",
):
    """Orchestrates the file ingestion and note creation process."""
    # Configure the Gemini API and create the model once.
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel(model_name)
    
    logging.info(f"Using Gemini model: {model_name}")

    if not os.path.isdir(ingest_folder):
        logging.error(f"Ingest folder not found: {ingest_folder}")
        sys.exit(1)

    processed_files = []
    failed_files = []

    for filename in os.listdir(ingest_folder):
        file_path = os.path.join(ingest_folder, filename)
        if os.path.isfile(file_path):
            try:
                logging.info(f"Processing file: {filename}")
                content = read_file_content(file_path)
                if not content:
                    logging.warning(f"Skipping {filename} due to empty content")
                    failed_files.append(file_path)
                    continue
                
                decomposed_notes = analyze_with_gemini(model, content)
                if decomposed_notes:
                    # Log note generation summary
                    atomic_count = sum(1 for note in decomposed_notes if note.get("type") == "atomic")
                    structure_count = sum(1 for note in decomposed_notes if note.get("type") == "structure")
                    total_wikilinks = sum(len(re.findall(r'\[\[([^\]]+)\]\]', note.get("content", ""))) for note in decomposed_notes)
                    
                    logging.info(f"Generated {len(decomposed_notes)} notes from {filename}:")
                    logging.info(f"  - {atomic_count} atomic notes")
                    logging.info(f"  - {structure_count} structure notes")
                    logging.info(f"  - {total_wikilinks} total wikilinks for connectivity")
                    
                    create_notes_in_vault(session, api_url, decomposed_notes, notes_folder, timeout)
                    processed_files.append(file_path)
                    logging.info(f"Successfully processed {filename}")
                else:
                    logging.warning(f"No notes generated from {filename}")
                    failed_files.append(file_path)
            except Exception as e:
                logging.error(f"Failed to process {filename}: {e}")
                failed_files.append(file_path)

    # Delete successfully processed files if requested
    if delete_after_ingest and processed_files:
        logging.info(f"Deleting {len(processed_files)} successfully processed files...")
        for file_path in processed_files:
            try:
                os.remove(file_path)
                logging.debug(f"Deleted: {file_path}")
            except OSError as e:
                logging.error(f"Failed to delete {file_path}: {e}")
        
        logging.info(f"Successfully deleted {len(processed_files)} files from ingest folder")
    
    if failed_files:
        logging.warning(f"{len(failed_files)} files failed processing and were not deleted")
        for file_path in failed_files:
            logging.debug(f"Failed file: {file_path}")