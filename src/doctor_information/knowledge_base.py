import json
from pathlib import Path
from typing import List, Dict


DEFAULT_DOCTOR_DATA_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "sample_doctor_knowledge.json"
)


def load_doctor_knowledge_base(
    file_path: str | Path = DEFAULT_DOCTOR_DATA_PATH,
) -> List[Dict]:
    """Load doctor information from the JSON knowledge base."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Doctor knowledge base not found: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            "Doctor knowledge base must contain a JSON list."
        )

    return data