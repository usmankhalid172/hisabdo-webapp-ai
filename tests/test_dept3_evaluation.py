"""
EVAL-xx: the Department 3 evaluation sets run as a regression gate.

Every fix in docs/dept3-chatbot-evaluation-and-fixes.md must keep these numbers.
Uses the mock LLM (deterministic), so it checks routing, retrieval, attribution and privacy.
"""
import importlib.util
from pathlib import Path

import pytest

RUNNER = Path(__file__).resolve().parent / "evaluation" / "dept3" / "run_dept3_eval.py"
spec = importlib.util.spec_from_file_location("run_dept3_eval", RUNNER)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


@pytest.mark.parametrize("case_file, minimum", [
    ("dept3_eval_set.json", 62),        # 62/62 after fixes (baseline 20/62)
    ("dept3_team_cases.json", 8),       # team's test_cases.csv: 8/8 (baseline 4/8)
    ("dept3_heldout_set.json", 25),     # 25/28 (baseline 3/28)
    ("dept3_heldout_round2.json", 21),  # 21/22 (baseline 3/22)
])
def test_EVAL_01_pass_counts_do_not_regress(case_file, minimum, tmp_path):
    result = runner.run("pytest", case_file, out_dir=tmp_path)    # results go to a temp folder, not the repo
    assert result["summary"]["passed"] >= minimum, [r["id"] for r in result["rows"] if not r["pass"]]


@pytest.mark.parametrize("case_file", ["dept3_eval_set.json", "dept3_heldout_set.json",
                                       "dept3_heldout_round2.json", "dept3_team_cases.json"])
def test_EVAL_02_privacy_is_never_broken(case_file, tmp_path):
    result = runner.run("pytest", case_file, out_dir=tmp_path)
    assert all(r["checks"]["privacy"] for r in result["rows"])
    assert all(r["pass"] for r in result["rows"] if r["behavior"] == "refuse")
