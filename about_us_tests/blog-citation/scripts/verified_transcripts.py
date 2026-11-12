"""
Verified Example Transcripts — Blog & News Grounded Generation
==============================================================
Runs 10 curated queries through the grounded-generation pipeline, validates
each response with the citation validator, and emits:

  - results/verified_transcripts.json   (structured log)
  - reports/verified_transcripts.md     (human-readable transcripts)

Transcript mix:
  T1–T7  — real queries through the pipeline (positive cases)
  T8–T10 — manually crafted bad responses (negative controls to prove the
           validator catches orphan markers, padded sources, and bad URLs)

Usage:
    python3 scripts/verified_transcripts.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Make the task folder importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.grounded_generation import generate_grounded_response
from src.citation_validator import validate_citations


# ============================================================
# POSITIVE TRANSCRIPTS — real queries through the pipeline
# ============================================================
POSITIVE_QUERIES = [
    {
        "id": "T1",
        "query": "how much does custom software cost in pakistan",
        "scenario": "Normal citation — should retrieve cost article and cite [1]",
    },
    {
        "id": "T2",
        "query": "custom software development guide",
        "scenario": "Multi-source synthesis — top-2 scores likely trigger synthesis",
    },
    {
        "id": "T3",
        "query": "what is the agile software development process",
        "scenario": "Normal citation — agile process article",
    },
    {
        "id": "T4",
        "query": "tell me about ai chatbot development",
        "scenario": "Normal citation — chatbot article",
    },
    {
        "id": "T5",
        "query": "explain progressive web apps",
        "scenario": "Normal citation — PWA article",
    },
    {
        "id": "T6",
        "query": "how much do you charge for software development services",
        "scenario": "Out-of-domain — should trigger Fallback 5.2 (deflect to /services)",
    },
    {
        "id": "T7",
        "query": "best recipe for chicken biryani",
        "scenario": "Off-topic — should trigger Fallback 5.1 (no source above threshold)",
    },
]


# ============================================================
# NEGATIVE CONTROL TRANSCRIPTS — manually crafted bad responses
# These prove the validator catches each failure mode.
# ============================================================
NEGATIVE_TRANSCRIPTS = [
    {
        "id": "T8",
        "query": "custom software development cost",
        "scenario": "NEGATIVE CONTROL — orphan marker [3] in body with no Sources entry",
        "fake_response": (
            "Custom software development cost depends on scope and complexity [1]. "
            "The article also mentions team composition as a factor [3].\n\n"
            "**Sources:**\n"
            "[1] Custom Software Development Guide — https://www.xicteksystems.com/blog/custom-software-development-guide\n"
        ),
        "fake_articles": [
            {"slug": "custom-software-development-guide",
             "title": "Custom Software Development Guide",
             "body": "cost depends on scope and complexity team composition"},
            {"slug": "software-development-cost-pakistan",
             "title": "Software Development Cost in Pakistan",
             "body": "cost price budget scope complexity"},
        ],
    },
    {
        "id": "T9",
        "query": "custom software development cost",
        "scenario": "NEGATIVE CONTROL — padded Sources entry [2] never cited in body",
        "fake_response": (
            "Custom software development cost depends on scope and complexity [1].\n\n"
            "**Sources:**\n"
            "[1] Custom Software Development Guide — https://www.xicteksystems.com/blog/custom-software-development-guide\n"
            "[2] Software Development Cost in Pakistan — https://www.xicteksystems.com/blog/software-development-cost-pakistan\n"
        ),
        "fake_articles": [
            {"slug": "custom-software-development-guide",
             "title": "Custom Software Development Guide",
             "body": "cost depends on scope and complexity"},
            {"slug": "software-development-cost-pakistan",
             "title": "Software Development Cost in Pakistan",
             "body": "cost price budget"},
        ],
    },
    {
        "id": "T10",
        "query": "tell me about hisabdo expense management app",
        "scenario": "NEGATIVE CONTROL — non-blog URL in Sources (scope violation)",
        "fake_response": (
            "Hisabdo is an expense management application [1].\n\n"
            "**Sources:**\n"
            "[1] Hisabdo Features — https://hisabdo.app/features\n"
        ),
        "fake_articles": [
            {"slug": "hisabdo-features",
             "title": "Hisabdo Features",
             "body": "expense management application"},
        ],
    },
]


# ============================================================
# RUNNER
# ============================================================
def run_positive(t: dict) -> dict:
    """Run a positive query through the real pipeline + validator."""
    print(f"[{t['id']}] Running: {t['query']}")
    result = generate_grounded_response(t["query"])
    report = validate_citations(result["response"], result["retrieved_articles"])

    return {
        "id": t["id"],
        "type": "positive",
        "query": t["query"],
        "scenario": t["scenario"],
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "retrieved_articles": [
            {
                "index": i + 1,
                "slug": a["slug"],
                "title": a["title"],
                "score": round(a.get("score", 0.0), 4),
                "publish_date": a["publish_date"].strftime("%Y-%m-%d") if a.get("publish_date") else None,
                "category": a.get("category"),
            }
            for i, a in enumerate(result["retrieved_articles"])
        ],
        "fallbacks_triggered": result["fallbacks_triggered"],
        "scope_violations_blocked": result["scope_violations"],
        "response": result["response"],
        "validation": {
            "overall_pass": report["overall_pass"],
            "errors": report["errors"],
            "warnings": report["warnings"],
            "checks": {
                name: {k: v for k, v in chk.items() if k != "rule"}
                for name, chk in report["checks"].items()
            },
            "markers_in_body": report["markers_in_body"],
            "sources_entries": report["sources_entries"],
        },
        "expected_pass": True,  # positive cases should always pass
    }


def run_negative(t: dict) -> dict:
    """Run a negative control — manually crafted bad response + validator."""
    print(f"[{t['id']}] Negative control: {t['scenario']}")
    report = validate_citations(t["fake_response"], t["fake_articles"])

    return {
        "id": t["id"],
        "type": "negative_control",
        "query": t["query"],
        "scenario": t["scenario"],
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "retrieved_articles": [
            {"index": i + 1, "slug": a["slug"], "title": a["title"]}
            for i, a in enumerate(t["fake_articles"])
        ],
        "fallbacks_triggered": [],
        "scope_violations_blocked": [],
        "response": t["fake_response"],
        "validation": {
            "overall_pass": report["overall_pass"],
            "errors": report["errors"],
            "warnings": report["warnings"],
            "checks": {
                name: {k: v for k, v in chk.items() if k != "rule"}
                for name, chk in report["checks"].items()
            },
            "markers_in_body": report["markers_in_body"],
            "sources_entries": report["sources_entries"],
        },
        "expected_pass": False,  # negative controls MUST fail
    }


def render_markdown(transcripts: list) -> str:
    """Render transcripts as Markdown for human review."""
    lines = []
    lines.append("# Verified Example Transcripts — Blog & News Grounded Generation")
    lines.append("")
    lines.append(f"**Generated:** {datetime.utcnow().isoformat()}Z")
    lines.append(f"**Total transcripts:** {len(transcripts)}")
    lines.append(f"**Positive cases:** {sum(1 for t in transcripts if t['type'] == 'positive')}")
    lines.append(f"**Negative controls:** {sum(1 for t in transcripts if t['type'] == 'negative_control')}")
    lines.append("")
    lines.append("Each transcript shows: query, retrieved articles, full response, "
                 "and a per-check validation report.")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Summary table
    lines.append("## Summary")
    lines.append("")
    lines.append("| ID | Type | Query | Expected | Actual | Result |")
    lines.append("|---|---|---|---|---|---|")
    for t in transcripts:
        expected = "PASS" if t["expected_pass"] else "FAIL"
        actual = "PASS" if t["validation"]["overall_pass"] else "FAIL"
        verdict = "OK" if expected == actual else "MISMATCH"
        query_short = t["query"][:50] + ("..." if len(t["query"]) > 50 else "")
        lines.append(f"| {t['id']} | {t['type']} | {query_short} | {expected} | {actual} | {verdict} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Per-transcript detail
    for t in transcripts:
        lines.append(f"## {t['id']} — {t['scenario']}")
        lines.append("")
        lines.append(f"**Type:** {t['type']}")
        lines.append(f"**Query:** `{t['query']}`")
        lines.append(f"**Timestamp:** {t['timestamp']}")
        lines.append("")

        # Retrieved articles
        if t["retrieved_articles"]:
            lines.append("### Retrieved Articles")
            lines.append("")
            lines.append("| # | Slug | Title | Score | Published |")
            lines.append("|---|---|---|---|---|")
            for a in t["retrieved_articles"]:
                score = a.get("score", "—")
                pub = a.get("publish_date") or "—"
                lines.append(f"| {a['index']} | `{a['slug']}` | {a['title']} | {score} | {pub} |")
            lines.append("")
        else:
            lines.append("### Retrieved Articles")
            lines.append("")
            lines.append("_(none — fallback triggered before retrieval)_")
            lines.append("")

        # Fallbacks
        if t["fallbacks_triggered"]:
            lines.append(f"**Fallbacks triggered:** {', '.join(t['fallbacks_triggered'])}")
            lines.append("")

        # Response
        lines.append("### Response")
        lines.append("")
        lines.append("```")
        lines.append(t["response"])
        lines.append("```")
        lines.append("")

        # Validation report
        lines.append("### Validation Report")
        lines.append("")
        v = t["validation"]
        verdict = "PASS" if v["overall_pass"] else "FAIL"
        lines.append(f"**Overall:** {verdict}")
        lines.append("")
        lines.append("| Check | Rule | Passed | Details |")
        lines.append("|---|---|---|---|")
        for name, chk in v["checks"].items():
            rule = {
                "check_1_orphan_markers": "Every [n] in body has a Sources entry",
                "check_2_padded_sources": "Every Sources entry has a [n] in body",
                "check_3_fabricated_index": "Every cited index <= len(retrieved)",
                "check_4_url_allowlist": "Every URL matches /blog/ regex",
                "check_5_verbatim_quotes": "Every \"...\"[n] quote found in article body",
            }.get(name, name)
            passed = "YES" if chk["passed"] else "NO"
            # Pick the most informative detail field
            detail_keys = [k for k in chk if k not in ("passed",)]
            detail_parts = []
            for k in detail_keys:
                val = chk[k]
                if isinstance(val, list) and val:
                    detail_parts.append(f"{k}={val}")
                elif isinstance(val, (str, int, float)) and val:
                    detail_parts.append(f"{k}={val}")
            detail = "; ".join(detail_parts) if detail_parts else "—"
            if len(detail) > 120:
                detail = detail[:117] + "..."
            lines.append(f"| {name} | {rule} | {passed} | {detail} |")
        lines.append("")

        if v["errors"]:
            lines.append("**Errors:**")
            for e in v["errors"]:
                lines.append(f"- {e}")
            lines.append("")

        if v["warnings"]:
            lines.append("**Warnings:**")
            for w in v["warnings"]:
                lines.append(f"- {w}")
            lines.append("")

        lines.append("---")
        lines.append("")

    # Final summary block
    n_pos = sum(1 for t in transcripts if t["type"] == "positive")
    n_neg = sum(1 for t in transcripts if t["type"] == "negative_control")
    pos_pass = sum(1 for t in transcripts if t["type"] == "positive" and t["validation"]["overall_pass"])
    neg_fail = sum(1 for t in transcripts if t["type"] == "negative_control" and not t["validation"]["overall_pass"])
    lines.append("## Final Result")
    lines.append("")
    lines.append(f"- Positive cases passed: **{pos_pass}/{n_pos}**")
    lines.append(f"- Negative controls correctly failed: **{neg_fail}/{n_neg}**")
    lines.append(f"- Overall verdict: **{'PASS' if pos_pass == n_pos and neg_fail == n_neg else 'FAIL'}**")
    lines.append("")
    return "\n".join(lines)


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 70)
    print("VERIFIED EXAMPLE TRANSCRIPTS — BLOG & NEWS")
    print("=" * 70)
    print()

    transcripts = []

    # Positive
    for t in POSITIVE_QUERIES:
        transcripts.append(run_positive(t))

    # Negative controls
    for t in NEGATIVE_TRANSCRIPTS:
        transcripts.append(run_negative(t))

    # Summary
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    pos_pass = sum(1 for t in transcripts if t["type"] == "positive" and t["validation"]["overall_pass"])
    neg_fail = sum(1 for t in transcripts if t["type"] == "negative_control" and not t["validation"]["overall_pass"])
    n_pos = sum(1 for t in transcripts if t["type"] == "positive")
    n_neg = sum(1 for t in transcripts if t["type"] == "negative_control")
    print(f"  Positive cases passed:          {pos_pass}/{n_pos}")
    print(f"  Negative controls failed:       {neg_fail}/{n_neg}")
    overall = (pos_pass == n_pos and neg_fail == n_neg)
    print(f"  Overall verdict:                {'PASS' if overall else 'FAIL'}")
    print()

    # Write JSON
    out_dir = Path(__file__).resolve().parent.parent
    json_path = out_dir / "results" / "verified_transcripts.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps({
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_transcripts": len(transcripts),
        "positive_count": n_pos,
        "negative_count": n_neg,
        "positive_passed": pos_pass,
        "negative_failed": neg_fail,
        "overall_pass": overall,
        "transcripts": transcripts,
    }, indent=2, default=str), encoding="utf-8")
    print(f"Wrote JSON: {json_path}")

    # Write Markdown
    md_path = out_dir / "reports" / "verified_transcripts.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(render_markdown(transcripts), encoding="utf-8")
    print(f"Wrote Markdown: {md_path}")

    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
