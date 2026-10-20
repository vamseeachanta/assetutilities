"""HTML inventory tests with hand-enumerated local fixtures.

Elements follow HTML Living Standard, sections 4.2.2, 4.2.3 and 4.2.5 (2026).
Relative links follow RFC 3986 (2005), section 5.2. Expected findings below
are literal missing files/elements in each synthetic fixture, not SEO limits.
"""

import pytest

from assetutilities.common.website_audit import audit_site


def page(root, name="index.html", body="", title="Guide", description="Guide summary"):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"<html><head><title>{title}</title>"
        f'<meta name="description" content="{description}"></head>'
        f"<body><h1>Engineering guide</h1>{body}</body></html>",
        encoding="utf-8",
    )
    return path


def codes(report, path="index.html"):
    return {
        item["code"]
        for item in report["pages"]
        if item["path"] == path
        for item in item["findings"]
    }


def test_inventory_and_literal_missing_elements(tmp_path):
    """One file has one title, description, heading and internal link.

    The other has none of the three metadata elements. Its missing title,
    description and h1 produce exactly three editorial findings.
    """
    page(tmp_path, body='<a href="empty.html">More</a>')
    (tmp_path / "empty.html").write_text("<p>Draft</p>", encoding="utf-8")
    report = audit_site(tmp_path)
    assert report["page_count"] == 2
    assert [p["path"] for p in report["pages"]] == ["empty.html", "index.html"]
    assert codes(report, "empty.html") == {
        "missing_title",
        "missing_description",
        "missing_h1",
    }
    entry = report["pages"][1]
    assert entry["title"] == "Guide"
    assert entry["description"] == "Guide summary"
    assert entry["h1_count"] == 1
    assert entry["internal_links"] == 1
    assert entry["findings"] == []
    assert report["external_links"] == "NOT_EVALUATED"
    assert report["rendered_content"] == "NOT_EVALUATED"


def test_duplicate_titles_are_grouped_for_editorial_review(tmp_path):
    """Two matching stripped titles form one group containing two paths."""
    page(tmp_path, title=" Guide ")
    page(tmp_path, "other.htm", title="Guide")
    assert audit_site(tmp_path)["duplicate_titles"] == [
        {"title": "Guide", "paths": ["index.html", "other.htm"]}
    ]


def test_resolves_relative_root_query_fragment_encoded_and_directory_links(tmp_path):
    """Six local references all resolve; query and fragment do not name files.

    RFC 3986 (2005), section 5.2, resolves ../ and leading slash references.
    This utility explicitly maps directory URLs to index.html for static exports.
    """
    page(tmp_path)
    page(tmp_path, "guide/index.html")
    page(tmp_path, "space name.html")
    page(
        tmp_path,
        "guide/topic.html",
        body="""
        <a href="../index.html?source=guide#intro">Root</a>
        <a href="/index.html">Absolute</a>
        <a href="../guide/">Directory</a>
        <a href="../space%20name.html">Encoded</a>
        <a href="#local">Fragment</a><a href="?v=revision">Query</a>
    """,
    )
    report = audit_site(tmp_path)
    entry = next(p for p in report["pages"] if p["path"] == "guide/topic.html")
    assert entry["internal_links"] == 6
    assert entry["findings"] == []
    assert all(p["path"][0] != "/" for p in report["pages"])


def test_reports_missing_target_and_path_escape(tmp_path):
    page(
        tmp_path,
        body='<a href="missing.html">Missing</a><a href="../outside.html">Up</a>',
    )
    report = audit_site(tmp_path)
    assert codes(report) == {"broken_local_link", "outside_root_link"}
    assert report["pages"][0]["internal_links"] == 2


def test_external_and_non_web_links_are_not_fetched(tmp_path, monkeypatch):
    """Three nonlocal hrefs stay unevaluated; none are broken local files."""
    import urllib.request

    def forbidden(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(urllib.request, "urlopen", forbidden)
    page(
        tmp_path,
        body="""
        <a href="https://example.org/">External</a>
        <a href="//example.org/">Protocol relative</a>
        <a href="tel:example">Contact</a>
    """,
    )
    entry = audit_site(tmp_path)["pages"][0]
    assert entry["nonlocal_links"] == 3
    assert entry["internal_links"] == 0
    assert entry["findings"] == []


def test_base_element_marks_all_link_resolution_unevaluated(tmp_path):
    page(
        tmp_path,
        body='<base href="https://example.org/"><a href="missing.html">More</a>',
    )
    report = audit_site(tmp_path)
    assert codes(report) == {"base_links_not_evaluated"}
    assert report["pages"][0]["link_resolution"] == "NOT_EVALUATED"


def test_parses_case_entities_nested_heading_and_ignores_comments(tmp_path):
    (tmp_path / "INDEX.HTML").write_text(
        """
        <HTML><HEAD><TITLE>Design &amp; analysis</TITLE>
        <META NAME="Description" CONTENT="A &amp; B"></HEAD>
        <BODY><H1><span>Title</span></H1><!-- <a href="missing"> -->
        <script>const example = '<a href="missing">';</script></BODY></HTML>
    """,
        encoding="utf-8",
    )
    entry = audit_site(tmp_path)["pages"][0]
    assert entry["title"] == "Design & analysis"
    assert entry["description"] == "A & B"
    assert entry["h1_count"] == 1
    assert entry["internal_links"] == 0
    assert entry["findings"] == []


def test_reports_blank_metadata_and_multiple_headings_as_counts_only(tmp_path):
    page(tmp_path, title=" ", description=" ", body="<h1>Second section</h1>")
    entry = audit_site(tmp_path)["pages"][0]
    assert entry["h1_count"] == 2
    assert {f["code"] for f in entry["findings"]} == {
        "missing_title",
        "missing_description",
    }


def test_detects_symlink_target_without_reading_it(tmp_path):
    page(tmp_path, body='<a href="asset.txt">Asset</a>')
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("not a site asset", encoding="utf-8")
    (tmp_path / "asset.txt").symlink_to(outside)
    assert codes(audit_site(tmp_path)) == {"outside_root_link"}


def test_symlinked_html_is_rejected(tmp_path):
    original = page(tmp_path)
    (tmp_path / "copy.html").symlink_to(original)
    with pytest.raises(ValueError, match="symbolic"):
        audit_site(tmp_path)


def test_symlinked_directories_are_not_traversed(tmp_path):
    outside = tmp_path.parent / "other-site"
    outside.mkdir()
    page(outside)
    (tmp_path / "other").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="HTML"):
        audit_site(tmp_path)


def test_empty_site_and_missing_root_are_errors(tmp_path):
    with pytest.raises(ValueError, match="HTML"):
        audit_site(tmp_path)
    with pytest.raises(ValueError, match="directory"):
        audit_site(tmp_path / "missing")


def test_invalid_encoding_is_reported_without_replacement(tmp_path):
    (tmp_path / "index.html").write_bytes(b"<title>\xff</title>")
    with pytest.raises(ValueError, match="UTF-8"):
        audit_site(tmp_path)


def test_malformed_url_becomes_unevaluated_finding(tmp_path):
    page(tmp_path, body='<a href="https://[invalid">Broken syntax</a>')
    assert codes(audit_site(tmp_path)) == {"invalid_link"}


def test_broken_html_symlink_is_rejected_instead_of_silently_omitted(tmp_path):
    """A dangling HTML link is still an unsupported symbolic HTML input."""
    page(tmp_path)
    (tmp_path / "dangling.html").symlink_to(tmp_path / "absent.html")
    with pytest.raises(ValueError, match="symbolic"):
        audit_site(tmp_path)
