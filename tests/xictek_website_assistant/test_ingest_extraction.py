from src.xictek_website_assistant.ingest import _extract_page


def test_extract_page_preserves_service_table_and_policy_list_blocks():
    html = """
    <html>
      <head><title>About XICTEK</title></head>
      <body>
        <nav>Navigation must not be indexed</nav>
        <main>
          <h1>About Us</h1>
          <div>Unwrapped company summary text.</div>
          <p>We build software for growing businesses.</p>
          <h2>Core Services</h2>
          <table>
            <thead><tr><th>Service</th><th>Description</th></tr></thead>
            <tbody>
              <tr><td>Web development</td><td>Custom sites and applications</td></tr>
              <tr><td>AI solutions</td><td>Automation and machine learning</td></tr>
            </tbody>
          </table>
          <h2>Privacy Policy</h2>
          <ul>
            <li>Collect only information needed to provide the service.</li>
            <li>Protect information from unauthorized access.</li>
          </ul>
        </main>
      </body>
    </html>
    """

    page = _extract_page("https://example.test/about", html)

    assert page.title == "About XICTEK"
    assert "Navigation must not be indexed" not in page.text
    assert "About Us" in page.text
    assert "We build software for growing businesses." in page.text
    assert "Unwrapped company summary text." in page.text
    assert (
        "Service | Description\n"
        "Web development | Custom sites and applications\n"
        "AI solutions | Automation and machine learning"
    ) in page.text
    assert (
        "- Collect only information needed to provide the service.\n"
        "- Protect information from unauthorized access."
    ) in page.text
