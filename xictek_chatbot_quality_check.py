"""Quality check for common queries on the public XICTEK chatbot.

Run:
    pip install playwright
    playwright install chromium
    python xictek_chatbot_quality_check.py

The script checks that each response is non-empty, reasonably brief, polite,
and contains at least one official XICTEK link.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright


SITE_URL = "https://www.xicteksystems.com/"
RESULTS_FILE = Path(__file__).with_name("xictek-quality-results.json")
MAX_ANSWER_CHARACTERS = 500

QUERIES = [
    "What services do you offer?",
    "How can I contact you?",
    "What technologies do you use?",
    "Can you build a web application?",
    "Do you build mobile apps?",
    "Do you provide AI solutions?",
    "Can you develop SaaS products?",
    "Can I see your portfolio?",
    "What is your development process?",
    "Do you provide post-launch support?",
    "How long does a typical project take?",
    "Do you work with startups?",
    "Where is XICTEK located?",
    "Can I get a project estimate?",
    "What are your office hours?",
]


def check_query(page, query: str) -> dict[str, object]:
    page.goto(SITE_URL, wait_until="domcontentloaded")
    page.locator("button[aria-label='Open XICTEK AI Assistant']").click()
    input_box = page.get_by_role("textbox", name="Type your message")
    input_box.fill(query)
    input_box.press("Enter")

    text = ""
    links: list[dict[str, str]] = []
    for _ in range(20):
        page.wait_for_timeout(700)
        panel = page.locator("div.fixed").last
        text = panel.inner_text()
        links = panel.locator("a").evaluate_all(
            "(anchors) => anchors.map((a) => ({text: a.innerText, href: a.href}))"
        )
        if "HELPFUL LINKS" in text or links:
            break

    answer = text.split(query, 1)[-1].split("HELPFUL LINKS", 1)[0].strip()
    answer = answer.replace(
        "Explore Services\nBuild My Project\nTechnologies\nView Portfolio\nContact Us",
        "",
    ).strip()
    official_links = [
        link for link in links if "xicteksystems.com" in link["href"]
    ]
    has_error_text = "Unexpected token" in answer or "<!DOCTYPE" in answer
    polite = any(
        phrase in answer.lower()
        for phrase in ("yes", "you can", "we ", "xICTEK".lower(), "contact")
    )
    brief = 0 < len(answer) <= MAX_ANSWER_CHARACTERS

    if not answer:
        status = "BLANK"
    elif has_error_text:
        status = "FORMATTING_OR_API_ERROR"
    elif not official_links:
        status = "MISSING_OFFICIAL_LINK"
    elif not polite or not brief:
        status = "QUALITY_CHECK"
    else:
        status = "PASS"

    return {
        "query": query,
        "answer": answer,
        "returned_links": links,
        "official_xictek_links": official_links,
        "polite": polite,
        "brief": brief,
        "status": status,
    }


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        results = [check_query(page, query) for query in QUERIES]
        browser.close()

    report = {
        "target": SITE_URL,
        "tested_at": datetime.now(timezone.utc).isoformat(),
        "query_count": len(results),
        "results": results,
    }
    RESULTS_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
    for result in results:
        print(f"[{result['status']}] {result['query']}")
    print(f"\nSaved results to {RESULTS_FILE}")


if __name__ == "__main__":
    main()
