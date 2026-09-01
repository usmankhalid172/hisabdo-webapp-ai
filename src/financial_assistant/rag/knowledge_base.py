import json
from pathlib import Path
from typing import List, Dict


def load_knowledge_base(file_path: str) -> List[Dict]:
    """Load knowledge-base documents from a JSON file."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Knowledge base not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("Knowledge base must contain a JSON list.")

    return data