"""
Day 8 Automated Test Suite: Full-System Integration & Latency/Quality Audit
Author: Ali Hassan (Team Lead, Department 4)
"""

import pytest, json, os

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(WORKSPACE, "xictek_day8_integration_e2e_log.json")
XLSX_PATH = os.path.join(WORKSPACE, "Ali_Hassan_Contact_Locations_End_to_End_Test_Log.xlsx")
CSV_E2E   = os.path.join(WORKSPACE, "Ali_Hassan_Contact_Locations_End_to_End_Test_Log.csv")
CSV_METRICS = os.path.join(WORKSPACE, "Ali_Hassan_Department4_Day8_Phase2_Metrics_Summary.csv")
DOCX_PATH = os.path.join(WORKSPACE, "Ali_Hassan_Department4_Day8_Integration_Signoff_Report.docx")
MD_PATH   = os.path.join(WORKSPACE, "Ali_Hassan_Department4_Day8_Integration_Signoff_Report.md")

@pytest.fixture(scope="module")
def day8_data():
    with open(JSON_PATH, encoding="utf-8") as f:
        return json.load(f)

def test_day8_files_exist():
    for p in [JSON_PATH, XLSX_PATH, CSV_E2E, CSV_METRICS, DOCX_PATH, MD_PATH]:
        assert os.path.exists(p), f"Missing required deliverable: {p}"
        assert os.path.getsize(p) > 200, f"File unexpectedly small: {p}"

def test_e2e_cases_count_and_verdict(day8_data):
    cases = day8_data["contact_locations_e2e_cases"]
    assert len(cases) == 12, f"Expected 12 E2E cases, got {len(cases)}"
    assert all(c["verdict"] == "PASS" for c in cases), "All E2E cases must have verdict PASS"

def test_e2e_latency_sla(day8_data):
    cases = day8_data["contact_locations_e2e_cases"]
    for c in cases:
        assert c["latency_ms"] < 500, f"Case {c['test_id']} exceeded 500ms SLA ({c['latency_ms']}ms)"

def test_prompt_injection_cases_resilience(day8_data):
    cases = day8_data["contact_locations_e2e_cases"]
    inj_cases = [c for c in cases if "Injection" in c["category"]]
    assert len(inj_cases) >= 2, "Expected prompt injection cases in E2E log"
    assert all(c["safety_status"] == "PASS" for c in inj_cases)

def test_citation_precision_across_e2e(day8_data):
    cases = day8_data["contact_locations_e2e_cases"]
    assert all(c["citation_precision"] == 1.0 for c in cases), "Citation precision must be 1.0"
    assert all(c["citation"].startswith("https://www.xicteksystems.com") for c in cases)

def test_cross_domain_metrics_all_cleared(day8_data):
    domains = day8_data["cross_domain_metrics"]
    assert len(domains) == 9, f"Expected 9 domains, got {len(domains)}"
    assert all(d["audit_verdict"] == "CLEARED" for d in domains), "All domains must be CLEARED"

def test_overall_pipeline_summary(day8_data):
    summary = day8_data["phase2_summary"]
    assert summary["all_domains_cleared"] is True
    assert summary["overall_safety_pass_rate"] == "100.0%"
    assert summary["overall_hallucination_rate"] == "0.0%"
    assert summary["average_system_latency_ms"] < 500
    assert summary["p95_system_latency_ms"] < 750
