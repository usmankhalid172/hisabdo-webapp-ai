#!/usr/bin/env python3
"""Standalone security and link regression checks for XICTEK Blog outputs.

Input formats: .json, .jsonl, .csv, .txt
- JSON: list of records or one record; records should include a response/answer/text field.
- JSONL: one record per line, or plain response text per line.
- CSV: response/answer/text/output column (first matching column).
- TXT: one chatbot response per blank-line-separated block.

This tool checks injected URLs for HTTPS, approved XICTEK Blog host/path,
reachability, and safe redirects. It also checks baseline security headers on
one or more HTTPS pages. It never changes repository files or application code.
"""
from __future__ import annotations
import argparse
import csv
import json
import re
import sys
from dataclasses import asdict, dataclass
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urljoin, urlsplit
from urllib.request import Request, urlopen

ALLOWED_HOSTS = {"xicteksystems.com", "www.xicteksystems.com"}
BLOG_ROOT = "/blog"
RESPONSE_FIELDS = ("response", "answer", "generated_response", "output", "text", "content", "message")
URL_RE = re.compile(r"https?://[^\s<>\]\[\"'`()]+", re.IGNORECASE)
DEFAULT_SECURITY_HEADERS = (
    "strict-transport-security",
    "x-content-type-options",
    "content-security-policy",
    "referrer-policy",
)

@dataclass
class Finding:
    check: str
    status: str  # PASS, FAIL, WARN
    item: str
    detail: str


def validate_blog_url(raw: str) -> tuple[bool, str]:
    """Validate secure URL and allowed XICTEK Blog path without making a request."""
    raw = unescape(raw.strip()).rstrip(".,;:!?")
    try:
        p = urlsplit(raw)
        if p.scheme.lower() != "https":
            return False, "URL must use HTTPS"
        if p.username or p.password:
            return False, "URL must not contain embedded credentials"
        if p.port not in (None, 443):
            return False, "Unexpected URL port"
        host = (p.hostname or "").lower()
        if host not in ALLOWED_HOSTS:
            return False, f"Host is not an approved XICTEK host: {host or '(missing)'}"
        path = unquote(p.path or "/")
        if "\\" in path or re.search(r"%2f|%5c", p.path, re.I):
            return False, "Encoded or backslash path separator is not allowed"
        if any(part in {".", ".."} for part in path.split("/")):
            return False, "Path traversal segment is not allowed"
        if not (path == BLOG_ROOT or path.startswith(BLOG_ROOT + "/")):
            return False, f"Path is outside the Blog section: {path}"
        return True, "HTTPS URL is on an approved XICTEK Blog path"
    except (ValueError, TypeError) as exc:
        return False, f"Malformed URL: {exc}"


def extract_urls(text: str) -> list[str]:
    # Strip common Markdown punctuation from each URL; URL validation handles the rest.
    found = []
    for m in URL_RE.findall(text):
        url = m.rstrip(".,;:!?")
        if url not in found:
            found.append(url)
    return found


def extract_response(record: Any) -> str:
    if isinstance(record, str):
        return record
    if isinstance(record, dict):
        for field in RESPONSE_FIELDS:
            value = record.get(field)
            if isinstance(value, str):
                return value
        # Handle nested API-style payloads.
        for field in ("data", "result", "choices"):
            nested = record.get(field)
            if isinstance(nested, dict):
                found = extract_response(nested)
                if found:
                    return found
            if isinstance(nested, list):
                for entry in nested:
                    found = extract_response(entry)
                    if found:
                        return found
    return ""


def load_responses(path: Path) -> list[tuple[str, str]]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        records = data if isinstance(data, list) else [data]
        return [(f"record-{i+1}", extract_response(row)) for i, row in enumerate(records)]
    if suffix == ".jsonl":
        rows = []
        for i, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
            if not line.strip():
                continue
            try:
                rows.append((f"line-{i}", extract_response(json.loads(line))))
            except json.JSONDecodeError:
                rows.append((f"line-{i}", line))
        return rows
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            rows = []
            for i, row in enumerate(reader, 2):
                response = extract_response(row)
                rows.append((f"row-{i}", response))
            return rows
    if suffix == ".txt":
        content = path.read_text(encoding="utf-8-sig")
        return [(f"block-{i+1}", block.strip()) for i, block in enumerate(re.split(r"\n\s*\n", content)) if block.strip()]
    raise ValueError("Unsupported input format. Use .json, .jsonl, .csv, or .txt")


def _request(url: str, timeout: float = 8.0):
    req = Request(url, headers={"User-Agent": "XICTEK-Blog-Security-Regression/1.0"}, method="GET")
    try:
        return urlopen(req, timeout=timeout)
    except HTTPError as exc:
        return exc  # HTTP errors still expose status, headers, and final URL.



class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        for key, value in attrs:
            if key.lower() == "href" and value:
                self.hrefs.append(value)


def discover_live_blog_urls(timeout: float = 10.0) -> tuple[list[str], list[Finding]]:
    """Fetch the live Blog landing page and discover approved Blog links."""
    landing = "https://www.xicteksystems.com/blog"
    try:
        response = _request(landing, timeout)
        status = getattr(response, "status", response.getcode())
        final_url = response.geturl()
        if not 200 <= status < 400:
            return [], [Finding("blog_discovery", "FAIL", landing, f"Blog landing page returned HTTP {status}")]
        ok, reason = validate_blog_url(final_url)
        if not ok:
            return [], [Finding("blog_discovery", "FAIL", landing, f"Unsafe final URL: {reason}")]
        parser = _LinkParser()
        parser.feed(response.read().decode("utf-8", errors="replace"))
        urls: list[str] = []
        for href in parser.hrefs:
            absolute = urlsplit(urljoin(final_url, href))._replace(fragment="").geturl()
            ok, _ = validate_blog_url(absolute)
            if ok and absolute not in urls:
                urls.append(absolute)
        return urls, [Finding("blog_discovery", "PASS", landing,
                              f"Live Blog page HTTP {status}; discovered {len(urls)} approved Blog links")]
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        return [], [Finding("blog_discovery", "FAIL", landing,
                            f"Live discovery failed: {exc.__class__.__name__}: {exc}")]

def check_live_blog_url(url: str, timeout: float = 8.0) -> tuple[bool, str]:
    try:
        response = _request(url, timeout)
        status = getattr(response, "status", response.getcode())
        final_url = response.geturl()
        if not 200 <= status < 400:
            return False, f"HTTP status {status}"
        ok, reason = validate_blog_url(final_url)
        if not ok:
            return False, f"Redirect ended at an unsafe URL: {reason} ({final_url})"
        return True, f"HTTP {status}; redirect destination remains in approved Blog section"
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        return False, f"Request failed: {exc.__class__.__name__}: {exc}"


def check_security_headers(url: str, timeout: float = 8.0) -> list[Finding]:
    findings: list[Finding] = []
    try:
        p = urlsplit(url)
        if p.scheme.lower() != "https":
            return [Finding("security_headers", "FAIL", url, "Header probe URL must use HTTPS")]
        if not p.hostname or p.hostname.lower() not in ALLOWED_HOSTS:
            return [Finding("security_headers", "FAIL", url, "Header probe must target an approved XICTEK host")]
        response = _request(url, timeout)
        status = getattr(response, "status", response.getcode())
        final_url = response.geturl()
        if not 200 <= status < 400:
            findings.append(Finding("security_headers", "FAIL", url, f"Page returned HTTP {status}"))
        final = urlsplit(final_url)
        if final.scheme.lower() != "https" or (final.hostname or "").lower() not in ALLOWED_HOSTS:
            findings.append(Finding("security_headers", "FAIL", url, f"Unsafe redirect destination: {final_url}"))
        headers = {k.lower(): str(v).strip() for k, v in response.headers.items()}
        for name in DEFAULT_SECURITY_HEADERS:
            if headers.get(name):
                findings.append(Finding("security_header", "PASS", url, f"{name}: present"))
            else:
                findings.append(Finding("security_header", "FAIL", url, f"Missing {name}"))
        # Either CSP frame-ancestors or X-Frame-Options is accepted as anti-clickjacking control.
        csp = headers.get("content-security-policy", "").lower()
        if "frame-ancestors" in csp or headers.get("x-frame-options"):
            findings.append(Finding("clickjacking_protection", "PASS", url, "CSP frame-ancestors or X-Frame-Options is present"))
        else:
            findings.append(Finding("clickjacking_protection", "FAIL", url, "Neither CSP frame-ancestors nor X-Frame-Options is present"))
        # Informational: don't fail solely on this optional header.
        if headers.get("permissions-policy"):
            findings.append(Finding("optional_header", "PASS", url, "permissions-policy: present"))
        else:
            findings.append(Finding("optional_header", "WARN", url, "permissions-policy is not present (review policy requirements)"))
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        findings.append(Finding("security_headers", "FAIL", url, f"Request failed: {exc.__class__.__name__}: {exc}"))
    return findings


def run_audit(input_path: Path, *, check_live: bool = True, header_urls: Iterable[str] = (), timeout: float = 8.0) -> list[Finding]:
    findings: list[Finding] = []
    records = load_responses(input_path)
    if not records:
        findings.append(Finding("input", "WARN", str(input_path), "No response records found"))
    for label, response in records:
        if not response.strip():
            findings.append(Finding("response_content", "WARN", label, "No response text found in record"))
            continue
        urls = extract_urls(response)
        if not urls:
            findings.append(Finding("source_presence", "WARN", label, "No URLs found; confirm whether this answer should cite Blog sources"))
            continue
        for url in urls:
            ok, detail = validate_blog_url(url)
            findings.append(Finding("url_security", "PASS" if ok else "FAIL", f"{label}: {url}", detail))
            if ok and check_live:
                live, live_detail = check_live_blog_url(url, timeout)
                findings.append(Finding("url_reachability", "PASS" if live else "FAIL", f"{label}: {url}", live_detail))
    for url in header_urls:
        findings.extend(check_security_headers(url, timeout))
    return findings


def write_report(findings: list[Finding], out_path: Path) -> None:
    payload = {
        "summary": {
            "total_checks": len(findings),
            "passed": sum(f.status == "PASS" for f in findings),
            "failed": sum(f.status == "FAIL" for f in findings),
            "warnings": sum(f.status == "WARN" for f in findings),
        },
        "findings": [asdict(f) for f in findings],
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, nargs="?", help="File containing captured Blog Section chatbot outputs")
    parser.add_argument("--discover-blog", action="store_true", help="Fetch the live Blog page, discover Blog links, and check each one")
    parser.add_argument("--no-live-check", action="store_true", help="Skip network checks; validate URL security/path only")
    parser.add_argument("--header-url", action="append", default=[], help="HTTPS XICTEK page to check security headers; can be repeated")
    parser.add_argument("--timeout", type=float, default=8.0, help="HTTP timeout in seconds (default: 8)")
    parser.add_argument("--report", type=Path, default=Path("blog_security_link_regression_report.json"), help="JSON report output path")
    args = parser.parse_args(argv)
    if not args.input and not args.discover_blog:
        parser.error("provide an input file or use --discover-blog")
    if args.input and not args.input.is_file():
        parser.error(f"Input file does not exist: {args.input}")
    try:
        findings = []
        if args.input:
            findings.extend(run_audit(args.input, check_live=not args.no_live_check, header_urls=args.header_url, timeout=args.timeout))
        elif args.header_url:
            for url in args.header_url:
                findings.extend(check_security_headers(url, args.timeout))
        if args.discover_blog:
            discovered, discovery_findings = discover_live_blog_urls(args.timeout)
            findings.extend(discovery_findings)
            for url in discovered:
                live, detail = check_live_blog_url(url, args.timeout)
                findings.append(Finding("discovered_url_reachability", "PASS" if live else "FAIL", url, detail))
            findings.extend(check_security_headers("https://www.xicteksystems.com/blog", args.timeout))
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    write_report(findings, args.report)
    for f in findings:
        print(f"[{f.status}] {f.check} | {f.item} | {f.detail}")
    summary = {s: sum(f.status == s for f in findings) for s in ("PASS", "FAIL", "WARN")}
    print(f"\nSummary: {summary['PASS']} passed, {summary['FAIL']} failed, {summary['WARN']} warnings")
    print(f"JSON report: {args.report.resolve()}")
    return 1 if summary["FAIL"] else 0

if __name__ == "__main__":
    raise SystemExit(main())
