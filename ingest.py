import sys
import os
import logging
import re
import json
import urllib.parse
import requests
import google.generativeai as genai
from pypdf import PdfReader
from typing import List, Dict


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


def analyze_with_gemini(model, text_content: str) -> List[Dict[str, str]]:
    """Sends text to Gemini for analysis and decomposition into atomic notes."""
    if not text_content.strip():
        logging.warning("Skipping Gemini analysis for empty content.")
        return []

    logging.info("Sending content to Gemini for analysis. This may take a moment...")
    try:
        prompt = f"""
        You are an expert in knowledge management, specializing in Zettelkasten and evergreen note-taking principles.
        Your task is to analyze the following text and decompose it into a series of atomic, concept-oriented notes.

        **Guidelines:**
        1.  **Atomicity:** Each note must focus on a single, core idea.
        2.  **Clarity:** Write notes in clear, simple language. The title should be a concise statement of the core concept.
        3.  **Connectivity:** The content should be written to encourage future linking. Do not add `[[wikilinks]]` yourself.
        4.  **Formatting:** Use standard markdown for the note content.

        **Output Format:**
        Return your response as a valid JSON array `[]` where each object in the array represents a single note and has the following structure:
        `{{ "title": "A Concise, Declarative Title for the Note", "content": "The full markdown content of the note." }}`

        Do not include any text or explanation outside of the JSON array.

        **Text to Analyze:**
        ---
        {text_content}
        ---
        """

        response = model.generate_content(prompt)
        # Clean up the response to ensure it's valid JSON
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
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
    notes_to_create: List[Dict[str, str]],
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

        if not title or not content:
            logging.warning(f"Skipping note with missing title or content: {note}")
            continue

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