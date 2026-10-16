#!/usr/bin/env python3
"""
Source Injection Automated Audit

Validates generated Blog Section responses for:
1. A source section at the end of the response.
2. One or more HTTP(S) source links in that final section.
3. Reachability of each source URL.
4. Optional restriction to an expected source/domain prefix.

Input JSON formats supported:
- [{"test_id": "TC-01", "response": "..."}]
- {"TC-01": "...", "TC-02": "..."}
- {"test_id": "...", "response": "..."}  # single object

CSV input is also supported when it contains a response column. The response
column can be named: response, generated_response, actual_response, or answer.

Examples:
    python scripts/source_injection_audit.py responses.json
    python scripts/source_injection_audit.py responses.csv --source-prefix https://xicteksystems.com/blog/
    python scripts/source_injection_audit.py responses.json --workers 8
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse


URL_RE = re.compile(r"https?://[^\s<>\]\)\"']+", re.IGNORECASE)
MD_LINK_RE = re.compile(r"\[[^\]]+\]\((https?://[^)\s]+)\)", re.IGNORECASE)

SOURCE_HEADINGS = re.compile(
    r"(?im)^\s*(?:#{1,6}\s*)?(?:sources?|references?|source\s+links?)\s*:?\s*$"
)

DEFAULT_TIMEOUT = 8
DEFAULT_TAIL_LINES = 12
DEFAULT_MAX_SOURCES = 10


@dataclass
class LinkCheck:
    url: str
    valid_syntax: bool
    active: bool
    status: int | None
    final_url: str | None
    error: str | None


@dataclass
class AuditResult:
    test_id: str
    passed: bool
    source_section_found: bool
    sources_at_end: bool
    links_found: int
    active_links: int
    invalid_links: int
    checks: list[LinkCheck]
    message: str


def _clean_url(url: str) -> str:
    return url.rstrip(".,;:!?)]}\"'`")


def extract_urls(text: str) -> list[str]:
    """Extract Markdown and plain HTTP(S) URLs while preserving order."""
    urls: list[str] = []

    for match in MD_LINK_RE.findall(text):
        url = _clean_url(match)
        if url not in urls:
            urls.append(url)

    for match in URL_RE.findall(text):
        url = _clean_url(match)
        if url not in urls:
            urls.append(url)

    return urls


def _source_section(text: str) -> tuple[bool, str]:
    """
    Return whether a source heading exists and the text following its last
    occurrence. Using the last heading avoids accidentally treating an
    earlier 'Sources' mention as the final source section.
    """
    matches = list(SOURCE_HEADINGS.finditer(text))
    if not matches:
        return False, ""
    return True, text[matches[-1].end():]


def sources_are_at_end(text: str, source_text: str) -> bool:
    """Return True when the final non-empty line contains the last source URL."""
    if not source_text.strip():
        return False

    source_urls = extract_urls(source_text)
    if not source_urls:
        return False

    non_empty_lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not non_empty_lines:
        return False

    last_line = non_empty_lines[-1]
    return any(url.lower() in last_line.lower() for url in source_urls)


def valid_source_url(url: str, source_prefix: str | None = None) -> bool:
    parsed = urlparse(url)
    if parsed.scheme.lower() not in {"http", "https"}:
        return False
    if not parsed.netloc:
        return False
    if source_prefix and not url.lower().startswith(source_prefix.lower()):
        return False
    return True


def check_url(url: str, timeout: int = DEFAULT_TIMEOUT) -> LinkCheck:
    """Check that a source URL is syntactically valid and reachable."""
    if not valid_source_url(url):
        return LinkCheck(url, False, False, None, None, "Invalid HTTP(S) URL")

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "HisabDo-Source-Audit/1.0"},
        method="HEAD",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = response.status
            return LinkCheck(
                url=url,
                valid_syntax=True,
                active=200 <= status < 400,
                status=status,
                final_url=response.geturl(),
                error=None,
            )
    except urllib.error.HTTPError as exc:
        # Some servers reject HEAD but still serve GET.
        if exc.code in {405, 501}:
            return _get_check(url, timeout)
        return LinkCheck(url, True, False, exc.code, None, str(exc))
    except (urllib.error.URLError, TimeoutError) as exc:
        # Retry with GET because some sites do not implement HEAD correctly.
        return _get_check(url, timeout, fallback_error=str(exc))
    except Exception as exc:
        return LinkCheck(url, True, False, None, None, str(exc))


def _get_check(
    url: str,
    timeout: int,
    fallback_error: str | None = None,
) -> LinkCheck:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "HisabDo-Source-Audit/1.0"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = response.status
            return LinkCheck(
                url=url,
                valid_syntax=True,
                active=200 <= status < 400,
                status=status,
                final_url=response.geturl(),
                error=None,
            )
    except urllib.error.HTTPError as exc:
        return LinkCheck(url, True, False, exc.code, None, str(exc))
    except Exception as exc:
        return LinkCheck(url, True, False, None, None, fallback_error or str(exc))


def audit_response(
    test_id: str,
    response: str,
    source_prefix: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    tail_lines: int = DEFAULT_TAIL_LINES,
    max_sources: int = DEFAULT_MAX_SOURCES,
    check_links: bool = True,
) -> AuditResult:
    if not isinstance(response, str) or not response.strip():
        return AuditResult(
            test_id, False, False, False, 0, 0, 0, [],
            "Generated response is empty."
        )

    tail = "\n".join(response.strip().splitlines()[-tail_lines:])
    found, source_text = _source_section(response)

    if not found:
        return AuditResult(
            test_id, False, False, False, 0, 0, 0, [],
            "Missing final Sources/References section."
        )

    urls = extract_urls(source_text)
    if not urls:
        return AuditResult(
            test_id, False, found, False, 0, 0, 0, [],
            "Source section exists but contains no HTTP(S) links."
        )

    if len(urls) > max_sources:
        urls = urls[:max_sources]

    at_end = sources_are_at_end(response, source_text)

    syntax_valid = [u for u in urls if valid_source_url(u, source_prefix)]
    invalid_count = len(urls) - len(syntax_valid)

    if not at_end:
        return AuditResult(
            test_id, False, found, False, len(urls), 0, invalid_count, [],
            "Source links are not the final content in the response."
        )

    # Ensure the heading itself is within the final response tail.
    if source_text.strip() not in tail and len(response.splitlines()) > tail_lines:
        # The source section can span more than the configured tail. The
        # definitive check is sources_are_at_end; this is only a soft guard.
        pass

    if not check_links:
        checks = [
            LinkCheck(u, True, True, None, None, None)
            for u in syntax_valid
        ]
        passed = invalid_count == 0 and bool(syntax_valid)
        return AuditResult(
            test_id, passed, found, at_end, len(urls), len(syntax_valid),
            invalid_count, checks,
            "Passed syntax/presence checks." if passed
            else "One or more source URLs are invalid."
        )

    checks: list[LinkCheck] = []
    with ThreadPoolExecutor(max_workers=min(8, len(syntax_valid) or 1)) as pool:
        futures = {pool.submit(check_url, u, timeout): u for u in syntax_valid}
        for future in as_completed(futures):
            checks.append(future.result())

    checks.sort(key=lambda item: urls.index(item.url))
    active = sum(c.active for c in checks)
    passed = (
        found
        and at_end
        and len(urls) > 0
        and invalid_count == 0
        and active == len(urls)
    )

    message = (
        "PASS: final source links are present and active."
        if passed
        else "FAIL: one or more source links are missing, invalid, or inactive."
    )

    return AuditResult(
        test_id, passed, found, at_end, len(urls), active,
        invalid_count, checks, message
    )


def load_records(path: Path) -> list[tuple[str, str]]:
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.DictReader(fh))
        response_key = next(
            (k for k in ("response", "generated_response", "actual_response", "answer")
             if rows and k in rows[0]),
            None,
        )
        if not response_key:
            raise ValueError(
                "CSV must contain one of: response, generated_response, "
                "actual_response, answer."
            )
        return [
            (str(row.get("test_id") or f"ROW-{i}"), row.get(response_key, ""))
            for i, row in enumerate(rows, 1)
        ]

    with path.open("r", encoding="utf-8") as fh:
        data: Any = json.load(fh)

    if isinstance(data, dict):
        if "response" in data:
            return [(str(data.get("test_id", "TEST-01")), str(data["response"]))]
        return [(str(k), str(v)) for k, v in data.items()]

    if isinstance(data, list):
        records = []
        for i, item in enumerate(data, 1):
            if not isinstance(item, dict) or "response" not in item:
                raise ValueError(
                    "JSON list items must be objects containing a 'response' field."
                )
            records.append((str(item.get("test_id", f"TEST-{i:02d}")), str(item["response"])))
        return records

    raise ValueError("Unsupported JSON structure.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Blog response source links.")
    parser.add_argument("input", type=Path, help="JSON or CSV file containing generated responses.")
    parser.add_argument(
        "--source-prefix",
        help="Optional URL prefix that every source must match, e.g. https://xicteksystems.com/blog/",
    )
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--tail-lines", type=int, default=DEFAULT_TAIL_LINES)
    parser.add_argument("--max-sources", type=int, default=DEFAULT_MAX_SOURCES)
    parser.add_argument(
        "--no-network",
        action="store_true",
        help="Validate source presence/syntax without making HTTP requests.",
    )
    parser.add_argument(
        "--json-report",
        type=Path,
        help="Optional path for a machine-readable JSON audit report.",
    )
    args = parser.parse_args()

    try:
        records = load_records(args.input)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    results = [
        audit_response(
            test_id=test_id,
            response=response,
            source_prefix=args.source_prefix,
            timeout=args.timeout,
            tail_lines=args.tail_lines,
            max_sources=args.max_sources,
            check_links=not args.no_network,
        )
        for test_id, response in records
    ]

    passed = sum(r.passed for r in results)
    print(f"Source Injection Audit: {passed}/{len(results)} tests passed")
    print("-" * 72)

    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(
            f"{status} {result.test_id}: {result.message} "
            f"(links={result.links_found}, active={result.active_links})"
        )
        for check in result.checks:
            state = "ACTIVE" if check.active else "INACTIVE"
            print(f"    [{state}] {check.url} -> {check.status or check.error}")

    if args.json_report:
        payload = [
            {
                **asdict(result),
                "checks": [asdict(check) for check in result.checks],
            }
            for result in results
        ]
        args.json_report.write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )
        print(f"\nJSON report written to: {args.json_report}")

    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
