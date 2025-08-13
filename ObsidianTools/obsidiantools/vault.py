import os

class Note:
    """A simple container for note data."""
    def __init__(self, path):
        self.path = path
        self.name = os.path.basename(path)

class Vault:
    def __init__(self, path):
        # Resolve to an absolute path for consistency
        self.path = os.path.abspath(path)

    def create(self):
        os.makedirs(self.path, exist_ok=True)
        os.makedirs(os.path.join(self.path, ".obsidian"), exist_ok=True)

    def create_note(self, title, content="", overwrite=False):
        note_path = os.path.join(self.path, f"{title}.md")

        if not overwrite and os.path.exists(note_path):
            raise FileExistsError(
                f"Note '{note_path}' already exists. Use overwrite=True to replace it."
            )

        # Specify UTF-8 encoding, which is standard for Markdown files.
        with open(note_path, "w", encoding="utf-8") as f:
            f.write(content)
        return Note(note_path)