import json
from pathlib import Path
from unittest.mock import Mock, patch

import blog_security_link_regression as audit


def test_https_approved_blog_url_passes():
    assert audit.validate_blog_url("https://xicteksystems.com/blog/example-article")[0]


def test_http_url_fails():
    ok, reason = audit.validate_blog_url("http://xicteksystems.com/blog/example")
    assert not ok and "HTTPS" in reason


def test_off_domain_and_non_blog_paths_fail():
    assert not audit.validate_blog_url("https://evil.example/blog/article")[0]
    assert not audit.validate_blog_url("https://xicteksystems.com/about")[0]


def test_traversal_and_encoded_separator_fail():
    assert not audit.validate_blog_url("https://xicteksystems.com/blog/../admin")[0]
    assert not audit.validate_blog_url("https://xicteksystems.com/blog/a%2fb")[0]


def test_credentials_and_unusual_port_fail():
    assert not audit.validate_blog_url("https://user:pass@xicteksystems.com/blog/a")[0]
    assert not audit.validate_blog_url("https://xicteksystems.com:8443/blog/a")[0]


def test_extract_urls_deduplicates():
    urls = audit.extract_urls("Sources: https://xicteksystems.com/blog/a and https://xicteksystems.com/blog/a")
    assert urls == ["https://xicteksystems.com/blog/a"]


def test_json_input_reads_response(tmp_path):
    file = tmp_path / "outputs.json"
    file.write_text(json.dumps([{"query": "q", "answer": "See https://xicteksystems.com/blog/a"}]))
    records = audit.load_responses(file)
    assert records[0][1] == "See https://xicteksystems.com/blog/a"


def test_jsonl_plain_text_fallback(tmp_path):
    file = tmp_path / "outputs.jsonl"
    file.write_text('{"response":"Hello"}\nPlain line\n')
    assert audit.load_responses(file) == [("line-1", "Hello"), ("line-2", "Plain line")]


def test_bad_url_does_not_get_live_checked(tmp_path):
    file = tmp_path / "out.txt"
    file.write_text("Sources: http://xicteksystems.com/blog/not-secure")
    with patch.object(audit, "check_live_blog_url") as live:
        findings = audit.run_audit(file, check_live=True)
    live.assert_not_called()
    assert any(f.check == "url_security" and f.status == "FAIL" for f in findings)


def test_valid_url_live_check_runs(tmp_path):
    file = tmp_path / "out.txt"
    file.write_text("Sources: https://xicteksystems.com/blog/a")
    with patch.object(audit, "check_live_blog_url", return_value=(True, "HTTP 200")) as live:
        findings = audit.run_audit(file, check_live=True)
    live.assert_called_once()
    assert any(f.check == "url_reachability" and f.status == "PASS" for f in findings)


def test_live_url_redirect_outside_blog_fails():
    response = Mock()
    response.status = 200
    response.getcode.return_value = 200
    response.geturl.return_value = "https://xicteksystems.com/login"
    with patch.object(audit, "_request", return_value=response):
        ok, reason = audit.check_live_blog_url("https://xicteksystems.com/blog/a")
    assert not ok and "unsafe URL" in reason


def test_security_headers_detect_missing_headers():
    response = Mock()
    response.status = 200
    response.getcode.return_value = 200
    response.geturl.return_value = "https://xicteksystems.com/"
    response.headers = {"strict-transport-security": "max-age=31536000", "x-content-type-options": "nosniff"}
    with patch.object(audit, "_request", return_value=response):
        findings = audit.check_security_headers("https://xicteksystems.com/")
    assert any(f.status == "FAIL" and "content-security-policy" in f.detail for f in findings)
    assert any(f.status == "FAIL" and "referrer-policy" in f.detail for f in findings)


def test_security_headers_pass_when_expected_headers_present():
    response = Mock()
    response.status = 200
    response.getcode.return_value = 200
    response.geturl.return_value = "https://xicteksystems.com/"
    response.headers = {
        "strict-transport-security": "max-age=31536000; includeSubDomains",
        "x-content-type-options": "nosniff",
        "content-security-policy": "default-src 'self'; frame-ancestors 'self'",
        "referrer-policy": "strict-origin-when-cross-origin",
        "permissions-policy": "camera=()",
    }
    with patch.object(audit, "_request", return_value=response):
        findings = audit.check_security_headers("https://xicteksystems.com/")
    assert all(f.status != "FAIL" for f in findings)


def test_report_summary_counts(tmp_path):
    findings = [audit.Finding("a", "PASS", "one", "ok"), audit.Finding("b", "FAIL", "two", "bad")]
    out = tmp_path / "report.json"
    audit.write_report(findings, out)
    data = json.loads(out.read_text())
    assert data["summary"] == {"total_checks": 2, "passed": 1, "failed": 1, "warnings": 0}


def test_discover_live_blog_urls_parses_only_approved_blog_links():
    response = Mock()
    response.status = 200
    response.getcode.return_value = 200
    response.geturl.return_value = "https://www.xicteksystems.com/blog"
    response.read.return_value = b'''<a href="/blog/article-one">one</a>
<a href="https://www.xicteksystems.com/blog/article-two#section">two</a>
<a href="/about">about</a>'''
    with patch.object(audit, "_request", return_value=response):
        urls, findings = audit.discover_live_blog_urls()
    assert urls == [
        "https://www.xicteksystems.com/blog/article-one",
        "https://www.xicteksystems.com/blog/article-two",
    ]
    assert findings[0].status == "PASS"
