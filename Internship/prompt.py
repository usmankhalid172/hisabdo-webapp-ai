
import json
from pathlib import Path

PROMPT_VERSION = "1.0"

PROMPT_FILE = Path(__file__).parent / "prompt_v1.txt"


def build_system_prompt(business_profile=None):
    # Read the versioned system prompt
    base_prompt = PROMPT_FILE.read_text(encoding="utf-8")

    # Handle missing or empty business profile
    if not isinstance(business_profile, dict):
        business_profile = {}

    profile = {
        "name": business_profile.get("name") or "Not provided",
        "type": business_profile.get("type") or "Not provided",
        "products": business_profile.get("products") or [],
        "services": business_profile.get("services") or [],
        "tone": business_profile.get("tone") or "Professional"
    }

    profile_text = json.dumps(
        profile,
        ensure_ascii=False,
        indent=2
    )

    return (
        f"{base_prompt}\n\n"
        f"ACTIVE BUSINESS PROFILE:\n{profile_text}\n\n"
        "Use only the available profile information. "
        "Do not invent missing details."
    )
