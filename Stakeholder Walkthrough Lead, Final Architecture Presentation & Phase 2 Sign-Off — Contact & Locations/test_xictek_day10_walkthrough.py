"""
Day 10 Automated Test Suite: Stakeholder Walkthrough & Phase 2 Sign-Off
Author: Ali Hassan (Team Lead, Department 4)
"""

import pytest, json, os

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
PPTX_PATH = os.path.join(WORKSPACE, "Ali_Hassan_Department4_Final_Executive_Presentation_Deck.pptx")
DEMO_DOCX = os.path.join(WORKSPACE, "Ali_Hassan_Contact_Locations_Demo_Script.docx")
DEMO_MD   = os.path.join(WORKSPACE, "Ali_Hassan_Contact_Locations_Demo_Script.md")
CERT_DOCX = os.path.join(WORKSPACE, "Ali_Hassan_Formal_Phase2_Signoff_Certificate.docx")
CERT_MD   = os.path.join(WORKSPACE, "Ali_Hassan_Formal_Phase2_Signoff_Certificate.md")
JSON_PATH = os.path.join(WORKSPACE, "xictek_day10_walkthrough_and_signoff_log.json")

@pytest.fixture(scope="module")
def day10_data():
    with open(JSON_PATH, encoding="utf-8") as f:
        return json.load(f)

def test_day10_deliverables_exist():
    for p in [PPTX_PATH, DEMO_DOCX, DEMO_MD, CERT_DOCX, CERT_MD, JSON_PATH]:
        assert os.path.exists(p), f"Missing required deliverable file: {p}"
        assert os.path.getsize(p) > 200, f"File unexpectedly small: {p}"

def test_presentation_deck_content():
    from pptx import Presentation
    prs = Presentation(PPTX_PATH)
    assert len(prs.slides) == 6, f"Expected 6 slides in executive deck, found {len(prs.slides)}"

def test_demo_scenarios_count(day10_data):
    scenarios = day10_data["demo_scenarios"]
    assert len(scenarios) >= 5, f"Expected at least 5 live demo scenarios, found {len(scenarios)}"
    assert all(s["verdict"] == "PASS" for s in scenarios)

def test_scorecard_metrics(day10_data):
    sc = day10_data["scorecard"]
    assert sc["groundedness_rate"] == "99.6%"
    assert sc["citation_precision"] == "99.8%"
    assert sc["safety_defense_rate"] == "100.0%"
    assert sc["domains_cleared"] == "9 / 9"
    assert "APPROVED" in sc["handover_status"]
