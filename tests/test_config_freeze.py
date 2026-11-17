"""The production configuration freeze (docs/dept3-production-config-freeze-spec.md): any change to a prompt, rule file,
retrieval constant, the approved KB or the index parameters must come with a new freeze version."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_code_matches_the_frozen_configuration():
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "freeze_config.py"), "--verify"],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stdout[-1500:]


def test_frozen_values_are_the_documented_ones():
    import json
    f = json.loads((ROOT / "config" / "production_freeze_v1.json").read_text(encoding="utf-8"))
    r = f["retrieval"]
    assert (r["hybrid_alpha_dense"], r["relevance_threshold"], r["top_k"], r["margin"], r["candidates"]) == \
        (0.6, 0.566273, 2, 0.05, 20)
    assert f["vector_index"]["dimensions"] == 384 and f["vector_index"]["records"] == 363
    assert f["settings_required_in_production"]["GROUNDED_ANSWERS_ENABLED"] == "true"
