"""
Day 9 Automated Test Suite: Production Readiness, Rollback Protocol & Monitoring Oversight
Author: Ali Hassan (Team Lead, Department 4)
"""

import pytest, json, os

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(WORKSPACE, "xictek_day9_production_readiness_log.json")
XLSX_PATH = os.path.join(WORKSPACE, "Ali_Hassan_Monitoring_and_Rollback_Protocol_Spec.xlsx")
CSV_CLOSURE = os.path.join(WORKSPACE, "Ali_Hassan_Contact_Locations_Closure_Log.csv")
CSV_SPEC    = os.path.join(WORKSPACE, "Ali_Hassan_Monitoring_and_Rollback_Protocol_Spec.csv")
DOCX_PATH   = os.path.join(WORKSPACE, "Ali_Hassan_Department4_Day9_Production_Readiness_Signoff_Report.docx")
MD_PATH     = os.path.join(WORKSPACE, "Ali_Hassan_Department4_Day9_Production_Readiness_Signoff_Report.md")

@pytest.fixture(scope="module")
def day9_data():
    with open(JSON_PATH, encoding="utf-8") as f:
        return json.load(f)

def test_day9_deliverable_files_exist():
    for p in [JSON_PATH, XLSX_PATH, CSV_CLOSURE, CSV_SPEC, DOCX_PATH, MD_PATH]:
        assert os.path.exists(p), f"Missing required file: {p}"
        assert os.path.getsize(p) > 200, f"File unexpectedly empty: {p}"

def test_contact_locations_closure_log(day9_data):
    cases = day9_data["contact_locations_closure_log"]
    assert len(cases) == 6, f"Expected 6 edge-case closures, got {len(cases)}"
    assert all(c["status"] == "CLOSED" for c in cases), "All edge cases must be CLOSED"
    for c in cases:
        assert c["citation"].startswith("https://www.xicteksystems.com"), f"Invalid citation in {c['case_id']}"

def test_monitoring_thresholds_configuration(day9_data):
    thresholds = day9_data["monitoring_thresholds"]
    assert len(thresholds) >= 7, f"Expected at least 7 monitoring dimensions, got {len(thresholds)}"
    metrics = [t["metric_name"] for t in thresholds]
    assert any("Latency (P50)" in m for m in metrics), "Missing P50 latency metric"
    assert any("Latency (P95)" in m for m in metrics), "Missing P95 latency metric"
    assert any("Hallucination" in m for m in metrics), "Missing Hallucination rate metric"
    assert any("Prompt-Injection" in m for m in metrics), "Missing Prompt-Injection metric"
    assert any("Quarantine" in m for m in metrics), "Missing Cross-Product Quarantine metric"

def test_rollback_protocols_steps(day9_data):
    steps = day9_data["rollback_protocol"]
    assert len(steps) == 6, f"Expected 6 rollback protocol steps, got {len(steps)}"
    step_numbers = [s["step_number"] for s in steps]
    assert step_numbers == ["STEP-01", "STEP-02", "STEP-03", "STEP-04", "STEP-05", "STEP-06"]

def test_configuration_freeze_register(day9_data):
    domains = day9_data["freeze_register"]
    assert len(domains) == 9, f"Expected 9 frozen domains, got {len(domains)}"
    assert all(d["corpus_version"] == "v9.0.0-freeze" for d in domains), "All corpora must be frozen at v9.0.0-freeze"
    assert all("FROZEN" in d["freeze_signoff"] for d in domains), "All domains must have freeze signoff"

def test_day9_summary_metrics(day9_data):
    summary = day9_data["summary"]
    assert summary["edge_cases_closed"] == 6
    assert summary["monitoring_thresholds_defined"] >= 7
    assert summary["rollback_protocol_steps"] == 6
    assert summary["domains_frozen_and_cleared"] == 9
    assert "100.0%" in summary["production_readiness_status"]
