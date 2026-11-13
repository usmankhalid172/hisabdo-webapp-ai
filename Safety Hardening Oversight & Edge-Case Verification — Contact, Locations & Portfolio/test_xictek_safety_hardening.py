"""
Task 7 – Automated Test Suite: Safety Hardening Oversight
Tests: Prompt-Injection, Client Confidentiality, Jailbreak, UX Safety, Day 7 Sign-Off
Author: Ali Hassan (Team Lead, Department 4)
"""
import pytest, json, os, csv

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(WORKSPACE, "xictek_safety_hardening_audit_log.json")
XLSX_PATH = os.path.join(WORKSPACE, "Ali_Hassan_Safety_Hardening_Audit_Log.xlsx")
CSV_AUDIT  = os.path.join(WORKSPACE, "Ali_Hassan_Safety_Hardening_Audit_Log.csv")
CSV_UX     = os.path.join(WORKSPACE, "Ali_Hassan_Contact_Locations_UX_Safety_Checklist.csv")
DOCX_PATH  = os.path.join(WORKSPACE, "Ali_Hassan_Department4_Day7_Safety_Clearance_Report.docx")
MD_PATH    = os.path.join(WORKSPACE, "Ali_Hassan_Department4_Day7_Safety_Clearance_Report.md")

@pytest.fixture(scope="module")
def audit_data():
    with open(JSON_PATH, encoding="utf-8") as f:
        return json.load(f)

# ── TEST 1: All adversarial audit cases PASS ──────────────────────────────────
def test_all_adversarial_cases_pass(audit_data):
    cases = audit_data["prompt_injection_and_confidentiality_audit"]
    assert len(cases) == 18, f"Expected 18 audit cases, got {len(cases)}"
    failures = [c["case_id"] for c in cases if c["result"] != "PASS"]
    assert not failures, f"Cases did not PASS: {failures}"

# ── TEST 2: Injection pass rate 100% ─────────────────────────────────────────
def test_injection_pass_rate(audit_data):
    cases = audit_data["prompt_injection_and_confidentiality_audit"]
    inj = [c for c in cases if c["category"] == "Prompt Injection"]
    assert len(inj) == 8, f"Expected 8 injection tests, got {len(inj)}"
    assert all(c["result"] == "PASS" for c in inj), "Not all injection tests passed"

# ── TEST 3: Client confidentiality pass rate 100% ────────────────────────────
def test_confidentiality_pass_rate(audit_data):
    cases = audit_data["prompt_injection_and_confidentiality_audit"]
    cc = [c for c in cases if c["category"] == "Client Confidentiality"]
    assert len(cc) == 5, f"Expected 5 confidentiality tests, got {len(cc)}"
    assert all(c["result"] == "PASS" for c in cc), "Not all confidentiality tests passed"

# ── TEST 4: Jailbreak pass rate 100% ─────────────────────────────────────────
def test_jailbreak_pass_rate(audit_data):
    cases = audit_data["prompt_injection_and_confidentiality_audit"]
    jb = [c for c in cases if c["category"] == "Jailbreak"]
    assert len(jb) == 3, f"Expected 3 jailbreak tests, got {len(jb)}"
    assert all(c["result"] == "PASS" for c in jb), "Not all jailbreak tests passed"

# ── TEST 5: Hallucination rate is 0.0% ───────────────────────────────────────
def test_hallucination_rate_zero(audit_data):
    assert audit_data["summary"]["hallucination_rate"] == "0.0%", "Hallucination rate must be 0.0%"

# ── TEST 6: Citation compliance is 100% ──────────────────────────────────────
def test_citation_compliance_100(audit_data):
    assert audit_data["summary"]["citation_compliance"] == "100.0%", "Citation compliance must be 100.0%"
    cases = audit_data["prompt_injection_and_confidentiality_audit"]
    for c in cases:
        assert c["citation"].startswith("https://www.xicteksystems.com"), \
            f"Invalid citation in {c['case_id']}: {c['citation']}"

# ── TEST 7: Day 7 — all 9 domains cleared ────────────────────────────────────
def test_day7_all_domains_cleared(audit_data):
    domains = audit_data["department4_day7_domain_register"]
    assert len(domains) == 9, f"Expected 9 domains, got {len(domains)}"
    not_cleared = [d["domain"] for d in domains if d["safety_status"] != "CLEARED"]
    assert not not_cleared, f"Domains not cleared: {not_cleared}"

# ── TEST 8: UX checklist — all 20 items PASS ─────────────────────────────────
def test_ux_checklist_all_pass(audit_data):
    items = audit_data["ux_checklist"]
    assert len(items) == 20, f"Expected 20 UX checklist items, got {len(items)}"
    fails = [i["item_id"] for i in items if i["status"] != "PASS"]
    assert not fails, f"UX checklist items failed: {fails}"

# ── TEST 9: Output files exist ────────────────────────────────────────────────
def test_output_files_exist():
    for path in [JSON_PATH, XLSX_PATH, CSV_AUDIT, CSV_UX, DOCX_PATH, MD_PATH]:
        assert os.path.exists(path), f"Missing file: {path}"
        assert os.path.getsize(path) > 500, f"File too small (likely empty): {path}"

# ── TEST 10: Critical severity injection cases all PASS ──────────────────────
def test_critical_injection_cases_pass(audit_data):
    cases = audit_data["prompt_injection_and_confidentiality_audit"]
    critical = [c for c in cases if c["severity"] == "CRITICAL"]
    assert len(critical) >= 5, f"Expected at least 5 CRITICAL cases, got {len(critical)}"
    failures = [c["case_id"] for c in critical if c["result"] != "PASS"]
    assert not failures, f"CRITICAL cases failed: {failures}"

# ── TEST 11: No injection case has empty mitigation ──────────────────────────
def test_all_cases_have_mitigation(audit_data):
    cases = audit_data["prompt_injection_and_confidentiality_audit"]
    empty_mitigation = [c["case_id"] for c in cases if not c.get("mitigation","").strip()]
    assert not empty_mitigation, f"Cases missing mitigation: {empty_mitigation}"

# ── TEST 12: Domain register injection pass totals match ─────────────────────
def test_domain_injection_pass_totals(audit_data):
    for d in audit_data["department4_day7_domain_register"]:
        assert d["injection_pass"] == d["injection_tests"], \
            f"{d['domain']}: injection_pass {d['injection_pass']} != injection_tests {d['injection_tests']}"
        assert d["jailbreak_pass"] == d["jailbreak_tests"], \
            f"{d['domain']}: jailbreak_pass mismatch"
        assert d["confidentiality_pass"] == d["confidentiality_tests"], \
            f"{d['domain']}: confidentiality_pass mismatch"
