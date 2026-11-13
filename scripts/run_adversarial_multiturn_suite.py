"""Run the focused all-domain safety and multi-turn regression suite."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JUNIT = ROOT / "outputs" / "adversarial_multiturn" / "junit.xml"
TEST_FILES = [
    "tests/xictek_website_assistant/test_guardrails.py",
    "tests/xictek_website_assistant/test_careers_grounding.py",
    "tests/xictek_website_assistant/test_portfolio_grounding.py",
    "tests/xictek_website_assistant/test_adversarial_multiturn.py",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--junitxml", type=Path, default=DEFAULT_JUNIT)
    args = parser.parse_args()
    output = args.junitxml if args.junitxml.is_absolute() else ROOT / args.junitxml
    output.parent.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "--confcutdir=tests/xictek_website_assistant",
        f"--junitxml={output}",
        *TEST_FILES,
    ]
    print("Running focused XICTEK safety/multi-turn regression suite:")
    print(" ".join(command))
    return subprocess.run(command, cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
