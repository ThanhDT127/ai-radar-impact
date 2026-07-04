import pytest
from datetime import datetime, timezone
from app.services.normalizer import clean_html, make_fingerprint, normalize_entry, MAX_CONTENT_LENGTH
from app.connectors.base import ConnectorEntry

def test_clean_html_strips_tags():
    html = "<p>Hello <b>World</b>!</p>"
    assert clean_html(html) == "Hello World !"

def test_clean_html_removes_scripts_and_styles():
    html = """
    <html>
        <head>
            <style>body { color: red; }</style>
            <script>alert('hello');</script>
        </head>
        <body>
            <noscript>JavaScript is disabled</noscript>
            <iframe>Some iframe</iframe>
            <p>Main content</p>
        </body>
    </html>
    """
    cleaned = clean_html(html)
    assert "Main content" in cleaned
    assert "body {" not in cleaned
    assert "alert" not in cleaned
    assert "JavaScript" not in cleaned
    assert "iframe" not in cleaned

def test_clean_html_normalizes_whitespace():
    html = "  Hello   \n\n  World \t  "
    assert clean_html(html) == "Hello World"

def test_clean_html_truncates_length():
    long_content = "a" * (MAX_CONTENT_LENGTH + 100)
    cleaned = clean_html(long_content)
    assert len(cleaned) == MAX_CONTENT_LENGTH
    assert cleaned == "a" * MAX_CONTENT_LENGTH

def test_clean_html_handles_empty():
    assert clean_html("") == ""
    assert clean_html(None) == ""

def test_make_fingerprint_generation():
    url = "https://example.com/Article"
    title = "Test Article"
    fp1 = make_fingerprint(url, title)
    
    # Case insensitivity and whitespace stripping checks
    fp2 = make_fingerprint("  https://EXAMPLE.com/article  ", "  TEST ARTICLE  ")
    assert fp1 == fp2
    assert len(fp1) == 64  # SHA-256 hex digest length

def test_normalize_entry():
    entry = ConnectorEntry(
        source_url="https://example.com/news",
        title="Breaking News",
        raw_content="<p>This is <strong>breaking</strong> news.</p>",
        author="John Doe",
        published_at=datetime.now(timezone.utc)
    )
    
    content, fp = normalize_entry(entry)
    assert content == "This is breaking news."
    assert fp == make_fingerprint("https://example.com/news", "Breaking News")
