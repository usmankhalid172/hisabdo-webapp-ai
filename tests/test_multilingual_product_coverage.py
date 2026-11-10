"""Regression tests: multilingual (English / Urdu script / Roman Urdu) routing of product questions.

Locked in here (regression): the round-1 cases (multilingual_product_test_cases.json) and
the round-1 held-out cases, which became tuning material in round 2.

Deliberately NOT asserted: data/multilingual_product_test_cases_heldout_v2.json, the current
honest measure. Run `python scripts/evaluate_multilingual_coverage.py --heldout` for it.
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from evaluate_multilingual_coverage import evaluate  # noqa: E402

CASES = [
    case
    for name in ("multilingual_product_test_cases.json", "multilingual_product_test_cases_heldout.json")
    for case in json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))["cases"]
]
ROWS = {r["id"]: r for r in evaluate(CASES)}


@pytest.mark.parametrize("case_id", sorted(ROWS))
def test_routed_to_the_right_place(case_id):
    r = ROWS[case_id]
    assert r["route_ok"], f"{r['text']!r}: expected {r['expect_intent']} ({r['expected_route']}), got {r['got_intent']}"


def test_no_private_question_reaches_a_public_route():
    leaks = [r["text"] for r in ROWS.values() if r["private_leak"]]
    assert leaks == []


def test_every_area_is_covered_in_all_three_languages():
    for area in {r["area"] for r in ROWS.values()}:
        assert {r["language"] for r in ROWS.values() if r["area"] == area} == {"en", "ur", "roman_ur"}, area


def test_urdu_script_questions_get_roman_urdu_replies():
    """Team rule (dialogue/extract.py): Urdu-script messages are answered in Roman Urdu."""
    assert all(r["detected_language"] == "roman_ur" for r in ROWS.values() if r["language"] in ("ur", "roman_ur"))
    assert all(r["detected_language"] == "en" for r in ROWS.values() if r["language"] == "en")
