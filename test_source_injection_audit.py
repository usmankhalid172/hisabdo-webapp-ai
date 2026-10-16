import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from scripts.source_injection_audit import audit_response, extract_urls


class LocalHTTPHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        if self.path == "/blog/good":
            self.send_response(200)
        else:
            self.send_response(404)
        self.end_headers()

    def do_GET(self):
        if self.path == "/blog/good":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html>OK</html>")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


def run_server():
    server = HTTPServer(("127.0.0.1", 0), LocalHTTPHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def test_extract_urls():
    text = "[Source](https://example.com/blog/a) and https://example.com/blog/b."
    assert extract_urls(text) == [
        "https://example.com/blog/a",
        "https://example.com/blog/b",
    ]


def test_passes_when_final_source_link_is_active():
    server = run_server()
    try:
        url = f"http://127.0.0.1:{server.server_port}/blog/good"
        response = f"Answer about the blog.\n\n## Sources\n- [HisabDo Blog]({url})"
        result = audit_response("TC-01", response)
        assert result.passed
        assert result.active_links == 1
    finally:
        server.shutdown()


def test_fails_when_sources_are_not_at_end():
    response = (
        "Answer.\n\n## Sources\n- [Blog](https://example.com/blog/a)\n\n"
        "Extra generated text after sources."
    )
    result = audit_response("TC-02", response, check_links=False)
    assert not result.passed
    assert not result.sources_at_end


def test_fails_when_source_section_has_no_link():
    response = "Answer.\n\n## Sources\nNo source was provided."
    result = audit_response("TC-03", response, check_links=False)
    assert not result.passed
    assert result.links_found == 0


def test_fails_for_wrong_source_prefix():
    response = (
        "Answer.\n\n## Sources\n"
        "- [Other](https://example.com/article)"
    )
    result = audit_response(
        "TC-04",
        response,
        source_prefix="https://xicteksystems.com/blog/",
        check_links=False,
    )
    assert not result.passed
    assert result.invalid_links == 1
