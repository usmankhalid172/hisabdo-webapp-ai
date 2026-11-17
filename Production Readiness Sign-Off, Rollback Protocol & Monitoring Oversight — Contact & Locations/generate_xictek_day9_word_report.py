"""
Day 9 Word Report Generator: Department 4 Day 9 Production Readiness Sign-Off
Author: Ali Hassan (Team Lead, Department 4)
Generates: Ali_Hassan_Department4_Day9_Production_Readiness_Signoff_Report.docx
"""

import json, datetime
from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

NOW = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

def rgb(hex_str):
    h = hex_str.lstrip("#")
    return RGBColor(int(h[0:2],16), int(h[2:4],16), int(h[4:6],16))

def set_cell_bg(cell, hex_color):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color.lstrip("#"))
    tcPr.append(shd)

def set_cell_margins(cell, top=60, bottom=60, left=100, right=100):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for side, val in [("top", top), ("bottom", bottom), ("left", left), ("right", right)]:
        m = OxmlElement(f"w:{side}")
        m.set(qn("w:w"), str(val))
        m.set(qn("w:type"), "dxa")
        tcMar.append(m)
    tcPr.append(tcMar)

doc = Document()

for section in doc.sections:
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)

# --- COVER / HEADER ---
doc.add_paragraph()
title_p = doc.add_paragraph()
title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r_title = title_p.add_run("DEPARTMENT 4 — DAY 9 PRODUCTION READINESS SIGN-OFF REPORT")
r_title.bold = True
r_title.font.size = Pt(20)
r_title.font.color.rgb = rgb("123456")

sub_p = doc.add_paragraph()
sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r_sub = sub_p.add_run("Production Readiness Sign-Off, Rollback Protocol & Monitoring Oversight\nContact & Locations Domain (DOM-01) & System-Wide Configuration Freeze")
r_sub.font.size = Pt(13)
r_sub.font.color.rgb = rgb("2C3E50")

doc.add_paragraph()
meta_items = [
    ("Sign-Off Authority", "Ali Hassan (Team Lead, Department 4)"),
    ("Target System", "XICTEK Systems Public Website AI Assistant (POST /api/v1/xictek/chat)"),
    ("Primary Domain Focus", "Contact & Locations (DOM-01) — Final Edge-Case Closure"),
    ("Production Milestone", "Day 9 Final Quality & Configuration Freeze ahead of Day 10 Handover"),
    ("Monitoring & Rollback Target", "Automated Anomaly Detection, Severity Triage, Sub-3min Rollback SLA"),
    ("Audit Date", NOW),
    ("GitHub Branch", "ali-hassan/pipeline-versioning-chunking-audit")
]

for label, val in meta_items:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r1 = p.add_run(f"{label}: ")
    r1.bold = True
    r1.font.size = Pt(10)
    r2 = p.add_run(val)
    r2.font.size = Pt(10)

doc.add_page_break()

def add_section_header(title):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(title)
    r.bold = True
    r.font.size = Pt(13)
    r.font.color.rgb = rgb("123456")
    return p

def add_body_p(text):
    p = doc.add_paragraph(text)
    p.paragraph_format.space_after = Pt(4)
    p.style.font.size = Pt(10)
    return p

# --- 1. EXECUTIVE SUMMARY ---
add_section_header("1. Executive Summary & Readiness Overview")
add_body_p(
    "Ahead of the Day 10 production handover, Ali Hassan (Team Lead, Department 4) has executed the final Production "
    "Readiness Sign-Off, Rollback Protocol Specification, and Monitoring Oversight for the XICTEK Systems Public Website AI "
    "Assistant. All remaining edge cases in the Contact & Locations domain (DOM-01) have been resolved and closed. Comprehensive "
    "real-time monitoring thresholds have been defined across latency, hallucination rate, and security vectors, backed by an "
    "automated 6-step rollback protocol capable of restoring verified checkpoints under 3 minutes. Furthermore, all nine "
    "Department 4 knowledge domains are formally frozen."
)

with open("xictek_day9_production_readiness_log.json", encoding="utf-8") as f:
    day9_json = json.load(f)

sum_data = [
    ("Contact & Locations Edge Cases Closed", "6 / 6 Edge Cases Formally Resolved & Verified"),
    ("Monitoring Thresholds & Alert Rules Defined", "7 Core SLA & Safety Dimensions Configured"),
    ("Rollback Protocol SLA Window", "Under 3 Minutes (< 180s) to Restore Day 8 Frozen Baseline"),
    ("Configuration Freeze Scope", "All 9 Department 4 Knowledge Domains (v9.0.0-freeze)"),
    ("Production Readiness Status", "100.0% CLEARED — ZERO OUTSTANDING BLOCKERS"),
    ("Handover Target", "Day 10 Production Handover to Site Reliability Engineering (SRE)")
]

t_sum = doc.add_table(rows=1, cols=2)
t_sum.style = "Table Grid"
hrow = t_sum.rows[0]
for ci, label in enumerate(["Readiness Dimension", "Status & Evaluation Metric"]):
    c = hrow.cells[ci]
    c.text = label
    c.paragraphs[0].runs[0].bold = True
    c.paragraphs[0].runs[0].font.color.rgb = rgb("FFFFFF")
    c.paragraphs[0].runs[0].font.size = Pt(10)
    set_cell_bg(c, "123456")
    set_cell_margins(c)

for ri, (dim, res) in enumerate(sum_data):
    row = t_sum.add_row()
    bg = "EAF2FB" if ri % 2 == 0 else "FFFFFF"
    for ci, val in enumerate([dim, res]):
        c = row.cells[ci]
        c.text = val
        c.paragraphs[0].runs[0].font.size = Pt(9.5)
        if ci == 0:
            c.paragraphs[0].runs[0].bold = True
        set_cell_bg(c, bg)
        set_cell_margins(c)
t_sum.columns[0].width = Inches(3.2)
t_sum.columns[1].width = Inches(3.3)

doc.add_paragraph()

# --- 2. CONTACT & LOCATIONS CLOSURE LOG ---
add_section_header("2. Contact & Locations Remaining Edge-Case Closure Log")
add_body_p(
    "The final 6 edge cases for DOM-01 were audited, resolved with strict negative fallback rules, and validated with "
    "authentic URL citations. All six cases are formally marked as CLOSED."
)

cases = day9_json["contact_locations_closure_log"]
t_cls = doc.add_table(rows=1, cols=5)
t_cls.style = "Table Grid"
hrow_cls = t_cls.rows[0]
for ci, h in enumerate(["Case ID", "Edge-Case Scenario", "Resolution Strategy & Fallback Rule", "Citation", "Status"]):
    c = hrow_cls.cells[ci]
    c.text = h
    c.paragraphs[0].runs[0].bold = True
    c.paragraphs[0].runs[0].font.color.rgb = rgb("FFFFFF")
    c.paragraphs[0].runs[0].font.size = Pt(9)
    set_cell_bg(c, "123456")
    set_cell_margins(c)
    c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

for ri, c in enumerate(cases):
    row = t_cls.add_row()
    bg = "EAF2FB" if ri % 2 == 0 else "FFFFFF"
    vals = [
        c["case_id"],
        c["edge_case_description"],
        c["resolution_strategy"][:65] + "...",
        c["citation"].replace("https://www.", ""),
        c["status"]
    ]
    for ci, val in enumerate(vals):
        cell = row.cells[ci]
        cell.text = val
        run = cell.paragraphs[0].runs[0]
        run.font.size = Pt(8.5)
        if ci in (0, 3, 4):
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        if ci == 4:
            run.bold = True
            run.font.color.rgb = rgb("1E8449")
        set_cell_bg(cell, bg)
        set_cell_margins(cell, top=35, bottom=35)

t_cls_widths = [0.8, 1.8, 2.3, 1.0, 0.6]
for i, w in enumerate(t_cls_widths):
    t_cls.columns[i].width = Inches(w)

doc.add_paragraph()

# --- 3. SYSTEM-WIDE MONITORING THRESHOLDS & ALERTS ---
add_section_header("3. System-Wide Monitoring Thresholds & Latency Alerts")
add_body_p(
    "Production telemetry will continuously monitor seven core system dimensions via Prometheus, OpenTelemetry, and "
    "WAF middleware. Configured alert triggers and automated remediation policies ensure immediate containment of performance dips."
)

mon_items = day9_json["monitoring_thresholds"]
t_mon = doc.add_table(rows=1, cols=5)
t_mon.style = "Table Grid"
hrow_mon = t_mon.rows[0]
for ci, h in enumerate(["Metric Dimension", "Target Baseline", "Warning Alert", "Critical P1 Alert", "Automated Action"]):
    c = hrow_mon.cells[ci]
    c.text = h
    c.paragraphs[0].runs[0].bold = True
    c.paragraphs[0].runs[0].font.color.rgb = rgb("FFFFFF")
    c.paragraphs[0].runs[0].font.size = Pt(8.5)
    set_cell_bg(c, "123456")
    set_cell_margins(c)
    c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

for ri, m in enumerate(mon_items):
    row = t_mon.add_row()
    bg = "EAF2FB" if ri % 2 == 0 else "FFFFFF"
    vals = [
        m["metric_name"],
        m["target_baseline"],
        m["warning_threshold"],
        m["critical_alert"],
        m["automated_action"][:50] + "..."
    ]
    for ci, val in enumerate(vals):
        cell = row.cells[ci]
        cell.text = val
        run = cell.paragraphs[0].runs[0]
        run.font.size = Pt(8.5)
        if ci in (1, 2, 3):
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_cell_bg(cell, bg)
        set_cell_margins(cell, top=35, bottom=35)

for i, w in enumerate([1.5, 1.1, 1.3, 1.3, 1.3]):
    t_mon.columns[i].width = Inches(w)

doc.add_paragraph()

# --- 4. STEP-BY-STEP ROLLBACK PROTOCOL ---
add_section_header("4. Step-by-Step Rollback Protocol Specification")
add_body_p(
    "In the event of a Critical P1 alert or persistent SLA breach in production, the following deterministic 6-phase "
    "rollback protocol is executed by SRE and Department 4 leads, restoring service to the Day 8 verified baseline in under 3 minutes."
)

protocols = day9_json["rollback_protocol"]
t_rb = doc.add_table(rows=1, cols=5)
t_rb.style = "Table Grid"
hrow_rb = t_rb.rows[0]
for ci, h in enumerate(["Step", "Phase", "Trigger Condition", "Required Execution Action", "SLA Window"]):
    c = hrow_rb.cells[ci]
    c.text = h
    c.paragraphs[0].runs[0].bold = True
    c.paragraphs[0].runs[0].font.color.rgb = rgb("FFFFFF")
    c.paragraphs[0].runs[0].font.size = Pt(8.5)
    set_cell_bg(c, "123456")
    set_cell_margins(c)
    c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

for ri, p in enumerate(protocols):
    row = t_rb.add_row()
    bg = "EAF2FB" if ri % 2 == 0 else "FFFFFF"
    vals = [
        p["step_number"],
        p["phase"],
        p["trigger_condition"][:40] + "...",
        p["action_required"][:55] + "...",
        p["sla_window"]
    ]
    for ci, val in enumerate(vals):
        cell = row.cells[ci]
        cell.text = val
        run = cell.paragraphs[0].runs[0]
        run.font.size = Pt(8.5)
        if ci in (0, 4):
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_cell_bg(cell, bg)
        set_cell_margins(cell, top=35, bottom=35)

for i, w in enumerate([0.7, 1.4, 1.6, 2.0, 0.8]):
    t_rb.columns[i].width = Inches(w)

doc.add_paragraph()

# --- 5. DEPARTMENT 4 CONFIGURATION FREEZE REGISTER ---
add_section_header("5. Department 4 Configuration Freeze Register (All 9 Domains)")
add_body_p(
    "All knowledge corpora, chunk index versions, and prompt templates across Department 4 have been frozen at release "
    "milestone v9.0.0-freeze. No further prompt modifications or vector indexing updates will occur ahead of Day 10 handover."
)

freeze_items = day9_json["freeze_register"]
t_frz = doc.add_table(rows=1, cols=6)
t_frz.style = "Table Grid"
hrow_frz = t_frz.rows[0]
for ci, h in enumerate(["Domain ID", "Knowledge Domain", "Lead", "Corpus Version", "Prompt Hash", "Readiness Verdict"]):
    c = hrow_frz.cells[ci]
    c.text = h
    c.paragraphs[0].runs[0].bold = True
    c.paragraphs[0].runs[0].font.color.rgb = rgb("FFFFFF")
    c.paragraphs[0].runs[0].font.size = Pt(8.5)
    set_cell_bg(c, "123456")
    set_cell_margins(c)
    c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

for ri, f in enumerate(freeze_items):
    row = t_frz.add_row()
    bg = "EAF2FB" if ri % 2 == 0 else "FFFFFF"
    vals = [
        f["domain_id"],
        f["domain_name"],
        f["lead"],
        f["corpus_version"],
        f["prompt_hash"],
        f["freeze_signoff"]
    ]
    for ci, val in enumerate(vals):
        cell = row.cells[ci]
        cell.text = val
        run = cell.paragraphs[0].runs[0]
        run.font.size = Pt(8.5)
        if ci in (0, 3, 4, 5):
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        if ci == 5:
            run.bold = True
            run.font.color.rgb = rgb("1E8449")
        set_cell_bg(cell, bg)
        set_cell_margins(cell, top=35, bottom=35)

for i, w in enumerate([0.8, 1.8, 1.2, 1.1, 1.0, 0.6]):
    t_frz.columns[i].width = Inches(w)

doc.add_paragraph()

# --- 6. FORMAL PRODUCTION READINESS SIGN-OFF ---
add_section_header("6. Formal Lead Production Readiness Sign-Off")
add_body_p(
    "I, Ali Hassan, Team Lead of Department 4, hereby declare that the XICTEK Systems AI Assistant pipeline has successfully "
    "completed all production readiness audits. With all contact edge cases closed, monitoring thresholds and automated "
    "rollback protocols established, and configurations across all nine domains frozen, Department 4 is fully prepared for "
    "the Day 10 production handover."
)
doc.add_paragraph()

sign_p = doc.add_paragraph()
sign_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r_sign = sign_p.add_run("FINAL VERDICT: ✅ APPROVED & FROZEN — 100% PRODUCTION READY FOR DAY 10 HANDOVER")
r_sign.bold = True
r_sign.font.size = Pt(11)
r_sign.font.color.rgb = rgb("1E8449")

meta_p = doc.add_paragraph()
meta_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r_m = meta_p.add_run(f"Signed by Ali Hassan (Team Lead, Department 4) | Timestamp: {NOW}")
r_m.font.size = Pt(9)
r_m.font.color.rgb = rgb("555555")

doc.save("Ali_Hassan_Department4_Day9_Production_Readiness_Signoff_Report.docx")
print("Saved Ali_Hassan_Department4_Day9_Production_Readiness_Signoff_Report.docx")
