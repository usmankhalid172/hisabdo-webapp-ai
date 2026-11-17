"""Release gate: every CRITICAL acceptance case must pass (factual, privacy, security).

Runs scripts/release_acceptance.py in its own process, because it configures the
service token and environment itself, separately from this test session.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_all_critical_acceptance_cases_pass():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "release_acceptance.py")],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600,
    )
    failures = [line for line in result.stdout.splitlines() if line.startswith("FAIL") and "critical" in line]
    assert result.returncode == 0, "Critical acceptance failures:\n" + "\n".join(failures or [result.stderr[-2000:]])
