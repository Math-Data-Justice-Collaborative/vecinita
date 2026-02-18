import os
from pathlib import Path

# Define the path to the text file relative to this script
# .parent gives us 'src/agent/data', so we just join the filename
RULES_FILE_PATH = Path(__file__).parent / "system_rules.md"

def get_system_rules() -> str:
    """
    Reads the system rules from the external Markdown file.
    This is called dynamically on every request to allow 'hot reloading'.
    """
    try:
        # Open the file and read the contents
        with open(RULES_FILE_PATH, "r", encoding="utf-8") as f:
            return f.read()
            
    except FileNotFoundError:
        # Fallback safety: If the file is accidentally deleted, return a default
        return "System Rule: Answer helpfuly and accurately."
