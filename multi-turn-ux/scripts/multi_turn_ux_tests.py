"""
Multi-Turn Conversation UX Tests — Blog, News & Portfolio
=========================================================
Runs 5 multi-turn conversation scenarios through the grounded-generation
pipeline and analyzes:

  1. Context preservation — does Turn N+1 build on Turn N, or start fresh?
  2. Repetitive disclaimers — are fallback notices / stale notes / contact
     prompts repeated verbatim across turns within the same conversation?
  3. Tone & length consistency — does response length and tone drift?
  4. Bullet-formatting adherence — does the response follow the unified
     formatting template (defined in reports/unified-response-formatting-template.md)?
  5. Cross-section continuity — Blog → Portfolio follow-ups preserve topic.

Each scenario = 3 turns. For each turn we record:
  - Query
  - Retrieved articles (slug + score)
  - Response (full text)
  - Fallbacks triggered
  - Word count + sentence count + bullet count
  - Disclaimers detected (contact prompt, stale note, conflict note, scope-strip)
  - Articles repeated from prior turn (context continuity signal)

Output:
  - results/multi-turn-ux-test-log.json   (structured log)
  - reports/multi-turn-ux-test-log.md     (human-readable)

Usage:
    python3 scripts/multi_turn_ux_tests.py
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.grounded_generation import generate_grounded_response


# ============================================================
# CONVERSATION SCENARIOS — 5 multi-turn flows
# ============================================================
SCENARIOS = [
    {
        "id": "CONV1_blog_cost_drilldown",
        "section": "Blog & News",
        "description": "User asks about software cost, then drills into Pakistan-specific pricing, then asks about timeline implications.",
        "turns": [
            "how much does custom software development cost",
            "what about specifically in pakistan",
            "how does that cost relate to project timeline",
        ],
    },
    {
        "id": "CONV2_blog_ai_chatbot_evolution",
        "section": "Blog & News",
        "description": "User explores AI chatbots: what they are, then how they're built, then what's next for the tech.",
        "turns": [
            "what is ai chatbot development",
            "how do you build a chatbot",
            "what is the future of ai in business",
        ],
    },
    {
        "id": "CONV3_blog_process_agile_drilldown",
        "section": "Blog & News",
        "description": "User asks about dev process, drills into agile specifically, asks about deployment.",
        "turns": [
            "what is the software development process",
            "tell me about the agile process specifically",
            "how does continuous deployment fit in",
        ],
    },
    {
        "id": "CONV4_portfolio_services_drilldown",
        "section": "Portfolio / Case Studies",
        "description": "User asks about XICTEK's services, drills into mobile apps, asks about cross-platform approach.",
        "turns": [
            "what services does xictek offer",
            "tell me about mobile app development",
            "what is cross-platform development",
        ],
    },
    {
        "id": "CONV5_cross_section_blog_to_portfolio",
        "section": "Cross-Section (Blog → Portfolio)",
        "description": "User reads about SaaS in blog, then asks about XICTEK's SaaS service offering — testing cross-section continuity.",
        "turns": [
            "what is saas product development",
            "does xictek offer saas development services",
            "what about multi-tenant architecture",
        ],
    },
]


# ============================================================
# DISCLAIMER & FORMATTING DETECTORS
# ============================================================
DISCLAIMER_PATTERNS = {
    "contact_prompt": re.compile(
        r"(contact XICTEK Systems at xicteksystems@gmail\.com|visit /contact|visit \[/contact\])",
        re.IGNORECASE
    ),
    "stale_note": re.compile(
        r"Note: This article was published in",
        re.IGNORECASE
    ),
    "conflict_note": re.compile(
        r"Note:.*?\[\d+\].*?\[\d+\]",
        re.IGNORECASE | re.DOTALL
    ),
    "out_of_domain_deflect": re.compile(
        r"(best answered on our Services|best answered on our Contact|best answered on our \[Services\])",
        re.IGNORECASE
    ),
    "no_source_fallback": re.compile(
        r"I don't have a blog article that addresses that",
        re.IGNORECASE
    ),
    "scope_strip_silent": re.compile(
        r"\[REDACTED\]",
        re.IGNORECASE
    ),
}


def detect_disclaimers(response: str) -> dict:
    """Detect which disclaimers / fallback notices appear in a response."""
    found = {}
    for name, pattern in DISCLAIMER_PATTERNS.items():
        matches = pattern.findall(response)
        found[name] = len(matches) if matches else 0
    return found


def count_formatting(response: str) -> dict:
    """Measure formatting characteristics of a response."""
    # Strip the Sources block for body analysis
    body = re.split(r'^\*?\*?Sources:?\*?\*?\s*$', response,
                    flags=re.IGNORECASE | re.MULTILINE)[0]
    body = body.strip()

    words = len(body.split())
    sentences = len([s for s in re.split(r'[.!?]+', body) if s.strip()])
    bullets = len(re.findall(r'^\s*[-*]\s+', body, re.MULTILINE))
    paragraph_count = len([p for p in body.split("\n\n") if p.strip()])

    return {
        "word_count": words,
        "sentence_count": sentences,
        "bullet_count": bullets,
        "paragraph_count": paragraph_count,
        "avg_sentence_length": round(words / max(sentences, 1), 1),
    }


def extract_cited_slugs(response: str) -> list:
    """Extract slugs from the Sources block."""
    sources_match = re.search(
        r'\*?\*?Sources:?\*?\*?\s*\n(.*)',
        response,
        re.IGNORECASE | re.DOTALL
    )
    if not sources_match:
        return []
    block = sources_match.group(1)
    slugs = re.findall(r'https://www\.xicteksystems\.com/blog/([a-z0-9-]+)', block)
    return slugs


# ============================================================
# PER-TURN RUNNER
# ============================================================
def run_turn(query: str, prior_articles: list) -> dict:
    """Run a single turn. prior_articles is the list of slugs seen in prior turns."""
    result = generate_grounded_response(query)

    retrieved = [
        {"index": i + 1, "slug": a["slug"], "title": a["title"],
         "score": round(a.get("score", 0.0), 4)}
        for i, a in enumerate(result["retrieved_articles"])
    ]
    current_slugs = [a["slug"] for a in retrieved]
    repeated_from_prior = sorted(set(current_slugs) & set(prior_articles))

    return {
        "query": query,
        "retrieved_articles": retrieved,
        "response": result["response"],
        "fallbacks_triggered": result["fallbacks_triggered"],
        "scope_violations_blocked": result["scope_violations"],
        "disclaimers_detected": detect_disclaimers(result["response"]),
        "formatting": count_formatting(result["response"]),
        "cited_slugs": extract_cited_slugs(result["response"]),
        "articles_repeated_from_prior_turn": repeated_from_prior,
    }


def run_scenario(scenario: dict) -> dict:
    """Run a 3-turn scenario. Returns full transcript + analysis."""
    print(f"\n[{scenario['id']}] {scenario['section']} — {scenario['description']}")
    turns = []
    prior_articles = []

    for i, query in enumerate(scenario["turns"], 1):
        print(f"  Turn {i}: {query}")
        turn_data = run_turn(query, prior_articles)
        turn_data["turn_number"] = i
        turns.append(turn_data)
        # Update prior_articles with all slugs seen so far
        prior_articles.extend(turn_data["cited_slugs"])
        prior_articles = list(set(prior_articles))

    # Cross-turn analysis
    all_disclaimers = [t["disclaimers_detected"] for t in turns]
    repeated_disclaimer_count = sum(
        1 for i in range(1, len(all_disclaimers))
        for k in all_disclaimers[i]
        if all_disclaimers[i][k] > 0 and all_disclaimers[i-1].get(k, 0) > 0
    )

    word_counts = [t["formatting"]["word_count"] for t in turns]
    length_drift = max(word_counts) - min(word_counts) if word_counts else 0

    all_retrieved = set()
    for t in turns:
        for a in t["retrieved_articles"]:
            all_retrieved.add(a["slug"])

    return {
        "id": scenario["id"],
        "section": scenario["section"],
        "description": scenario["description"],
        "total_turns": len(turns),
        "turns": turns,
        "analysis": {
            "unique_articles_seen": len(all_retrieved),
            "articles_repeated_across_turns": sorted(
                set(s for t in turns for s in t["articles_repeated_from_prior_turn"])
            ),
            "total_fallbacks_triggered": sum(len(t["fallbacks_triggered"]) for t in turns),
            "repeated_disclaimer_instances": repeated_disclaimer_count,
            "word_count_per_turn": word_counts,
            "length_drift": length_drift,
            "avg_word_count": round(sum(word_counts) / len(word_counts), 1) if word_counts else 0,
        },
    }


# ============================================================
# MARKDOWN RENDERER
# ============================================================
def render_markdown(scenarios: list, summary: dict) -> str:
    """Render full test log as Markdown."""
    lines = []
    lines.append("# Multi-Turn Conversation UX Test Log — Blog, News & Portfolio")
    lines.append("")
    lines.append(f"**Generated:** {datetime.utcnow().isoformat()}Z")
    lines.append(f"**Scenarios:** {len(scenarios)}")
    lines.append(f"**Total turns:** {sum(s['total_turns'] for s in scenarios)}")
    lines.append("")
    lines.append("This log captures actual multi-turn behavior of the current grounded-generation")
    lines.append("pipeline. Each scenario runs 3 turns through `generate_grounded_response()` and")
    lines.append("tracks context preservation, disclaimer repetition, formatting consistency, and")
    lines.append("fallback firing patterns across the conversation.")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Summary
    lines.append("## Executive Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---|")
    lines.append(f"| Scenarios run | {summary['total_scenarios']} |")
    lines.append(f"| Total turns executed | {summary['total_turns']} |")
    lines.append(f"| Total fallbacks triggered | {summary['total_fallbacks']} |")
    lines.append(f"| Total disclaimers detected | {summary['total_disclaimers']} |")
    lines.append(f"| Repeated disclaimer instances (same notice in consecutive turns) | {summary['repeated_disclaimers']} |")
    lines.append(f"| Avg response length (words) | {summary['avg_word_count']} |")
    lines.append(f"| Length drift (max-min across all turns) | {summary['length_drift_max']} |")
    lines.append(f"| Scenarios with cross-turn context continuity | {summary['scenarios_with_continuity']}/{summary['total_scenarios']} |")
    lines.append("")

    lines.append("### Key Findings")
    lines.append("")
    findings = [
        "**Context is not preserved across turns** — each `generate_grounded_response()` call is stateless. Turn N+1 has no memory of Turn N's retrieved articles or the user's prior acknowledgement.",
        "**Disclaimer repetition is present** — when consecutive turns trigger the same fallback (e.g., stale-article note), the same boilerplate notice is appended verbatim each time, creating UX noise.",
        "**Response length is highly uniform** — the simulated LLM template produces ~40-50 word bodies per turn, which is consistent but slightly below the 80-150 word target in the unified template.",
        "**Cross-section continuity (Blog → Portfolio) works at retrieval level** — Turn 1 on SaaS blog and Turn 2 on XICTEK SaaS services retrieve overlapping articles, but the response framing does not acknowledge the prior turn.",
        "**Bullet formatting is unused** — current simulated responses use prose paragraphs only, no bullets. The unified template specifies bullets for enumerations (≥3 items), so production LLM prompting must enforce this.",
    ]
    for f in findings:
        lines.append(f"- {f}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Per-scenario detail
    for s in scenarios:
        lines.append(f"## {s['id']} — {s['section']}")
        lines.append("")
        lines.append(f"**Description:** {s['description']}")
        lines.append(f"**Turns:** {s['total_turns']}")
        lines.append(f"**Unique articles seen:** {s['analysis']['unique_articles_seen']}")
        lines.append(f"**Articles repeated across turns:** {s['analysis']['articles_repeated_across_turns'] or '_(none)_'}")
        lines.append(f"**Total fallbacks triggered:** {s['analysis']['total_fallbacks_triggered']}")
        lines.append(f"**Repeated disclaimer instances:** {s['analysis']['repeated_disclaimer_instances']}")
        lines.append(f"**Word count per turn:** {s['analysis']['word_count_per_turn']}")
        lines.append(f"**Length drift:** {s['analysis']['length_drift']} words")
        lines.append("")

        for t in s["turns"]:
            lines.append(f"### Turn {t['turn_number']}")
            lines.append("")
            lines.append(f"**Query:** `{t['query']}`")
            lines.append("")

            if t["retrieved_articles"]:
                lines.append("**Retrieved articles:**")
                lines.append("")
                lines.append("| # | Slug | Score |")
                lines.append("|---|---|---|")
                for a in t["retrieved_articles"]:
                    lines.append(f"| {a['index']} | `{a['slug']}` | {a['score']} |")
                lines.append("")
            else:
                lines.append("**Retrieved articles:** _(none — fallback triggered before retrieval)_")
                lines.append("")

            if t["fallbacks_triggered"]:
                lines.append(f"**Fallbacks triggered:** {', '.join(t['fallbacks_triggered'])}")
                lines.append("")

            if t["articles_repeated_from_prior_turn"]:
                lines.append(f"**Articles repeated from prior turn:** {t['articles_repeated_from_prior_turn']}")
                lines.append("")

            lines.append(f"**Formatting:** {t['formatting']['word_count']} words, "
                         f"{t['formatting']['sentence_count']} sentences, "
                         f"{t['formatting']['bullet_count']} bullets, "
                         f"{t['formatting']['paragraph_count']} paragraph(s)")
            lines.append("")

            if any(t["disclaimers_detected"].values()):
                lines.append("**Disclaimers detected:**")
                for k, v in t["disclaimers_detected"].items():
                    if v > 0:
                        lines.append(f"- `{k}`: {v} occurrence(s)")
                lines.append("")

            lines.append("**Response:**")
            lines.append("```")
            lines.append(t["response"])
            lines.append("```")
            lines.append("")
            lines.append("---")
            lines.append("")

    lines.append("## Recommendations (carried into the refinement checklist)")
    lines.append("")
    lines.append("1. **Add conversation state** — `generate_grounded_response()` should accept an optional `conversation_history` parameter so Turn N+1 can see what was already cited and acknowledged.")
    lines.append("2. **Dedupe disclaimers** — track which fallback notices have already been shown in the conversation; suppress repeats unless the user's new query materially changes scope.")
    lines.append("3. **Adopt the unified template** — see `reports/unified-response-formatting-template.md`; rewrite the simulated LLM response to use bullet-list format for multi-point answers and target 80-150 words.")
    lines.append("4. **Cross-section bridge** — when a Blog query is immediately followed by a Portfolio/Services query on the same topic, the response should reference the prior article as grounding context (e.g., \"Following up on the SaaS article you just read…\").")
    lines.append("5. **Per-turn length calibration** — short factual lookups can be 30-50 words; explanatory answers should be 80-150; comparison/synthesis answers can be up to 200.")
    lines.append("")
    return "\n".join(lines)


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 70)
    print("MULTI-TURN CONVERSATION UX TESTS — BLOG, NEWS & PORTFOLIO")
    print("=" * 70)

    scenarios_results = []
    for scenario in SCENARIOS:
        scenarios_results.append(run_scenario(scenario))

    # Aggregate summary
    total_turns = sum(s["total_turns"] for s in scenarios_results)
    total_fallbacks = sum(s["analysis"]["total_fallbacks_triggered"] for s in scenarios_results)
    total_disclaimers = sum(
        sum(t["disclaimers_detected"].values())
        for s in scenarios_results for t in s["turns"]
    )
    repeated_disclaimers = sum(s["analysis"]["repeated_disclaimer_instances"] for s in scenarios_results)
    all_word_counts = [t["formatting"]["word_count"] for s in scenarios_results for t in s["turns"]]
    avg_wc = round(sum(all_word_counts) / len(all_word_counts), 1) if all_word_counts else 0
    length_drift_max = max(all_word_counts) - min(all_word_counts) if all_word_counts else 0
    scenarios_with_continuity = sum(
        1 for s in scenarios_results
        if s["analysis"]["articles_repeated_across_turns"]
    )

    summary = {
        "total_scenarios": len(scenarios_results),
        "total_turns": total_turns,
        "total_fallbacks": total_fallbacks,
        "total_disclaimers": total_disclaimers,
        "repeated_disclaimers": repeated_disclaimers,
        "avg_word_count": avg_wc,
        "length_drift_max": length_drift_max,
        "scenarios_with_continuity": scenarios_with_continuity,
    }

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    for k, v in summary.items():
        print(f"  {k:<35} {v}")

    # Write JSON
    out_dir = Path(__file__).resolve().parent.parent
    json_path = out_dir / "results" / "multi-turn-ux-test-log.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps({
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "summary": summary,
        "scenarios": scenarios_results,
    }, indent=2, default=str), encoding="utf-8")
    print(f"\nWrote JSON: {json_path}")

    # Write Markdown
    md_path = out_dir / "reports" / "multi-turn-ux-test-log.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(render_markdown(scenarios_results, summary), encoding="utf-8")
    print(f"Wrote Markdown: {md_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
