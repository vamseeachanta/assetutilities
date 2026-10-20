"""Read-only inventory of a UTF-8 static HTML export, without network access.

Element meanings: HTML Living Standard (retrieved 2026-10-20), sections 4.2.2
(title), 4.2.3 (base), 4.2.5 (meta), 4.3.6 (headings).
https://html.spec.whatwg.org/multipage/semantics.html
https://html.spec.whatwg.org/multipage/sections.html#the-h1,-h2,-h3,-h4,-h5,-and-h6-elements
URL components: RFC 3986 (2005), sections 3 and 5.2.
https://www.rfc-editor.org/rfc/rfc3986#section-5.2
Missing metadata and repeated titles are editorial prompts, not conformance or
search ranking verdicts. No length, page-count or heading-count limits are assumed.
"""

from __future__ import annotations

from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit


class _Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.in_title = False
        self.description = ""
        self.h1_count = 0
        self.links: list[str] = []
        self.has_base = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "title":
            self.in_title = True
        elif tag == "h1":
            self.h1_count += 1  # Literal HTML heading count; no acceptance threshold.
        elif tag == "meta" and (attributes.get("name") or "").lower() == "description":
            self.description = attributes.get("content") or ""
        elif tag == "base" and "href" in attributes:
            self.has_base = True
        elif tag == "a" and "href" in attributes:
            self.links.append(attributes["href"] or "")

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)


def _finding(code: str, href: str | None = None) -> dict[str, str]:
    result = {"code": code}
    if href is not None:
        result["href"] = href
    return result


def _link_kind(root: Path, source: Path, href: str) -> str:
    try:
        parts = urlsplit(href.strip())
    except ValueError:
        return "invalid_link"
    if parts.scheme or parts.netloc:
        return "nonlocal"
    try:
        path = unquote(parts.path, errors="strict")
        if "\x00" in path or "\\" in path:
            return "invalid_link"
        if not path:
            target = source
        elif path.startswith("/"):
            target = root / path.lstrip("/")
        else:
            target = source.parent / path
        target = target.resolve()
        # Resolve symlinks and traversal before checking or reading a target.
        target.relative_to(root)
        if target.is_dir():
            # Explicit static-export convention, not a server routing assumption.
            target = (target / "index.html").resolve()
            target.relative_to(root)
        return "local" if target.is_file() else "broken_local_link"
    except UnicodeError:
        return "invalid_link"
    except ValueError:
        return "outside_root_link"


def audit_site(directory: str | Path) -> dict[str, Any]:
    """Inventory .html/.htm files; return relative paths and editorial findings.

    Directory URLs map to index.html. Query strings and fragments are ignored;
    fragment targets, external links, rendered JavaScript, server redirects and
    pages with a base href are not evaluated. Symlinked HTML is rejected and
    symlinked directories are not traversed. No files are changed.
    """
    root = Path(directory).resolve()
    if not root.is_dir():
        raise ValueError("site root must be an existing directory")
    files = sorted(
        path
        for path in root.rglob("*")
        if path.suffix.lower() in {".html", ".htm"}
        and (path.is_symlink() or path.is_file())
    )
    if not files:
        raise ValueError("site root contains no HTML files")
    pages = []
    titles: dict[str, list[str]] = defaultdict(list)
    for path in files:
        if path.is_symlink():
            raise ValueError("symbolic HTML files are not supported")
        path.resolve().relative_to(root)
        parser = _Page()
        try:
            parser.feed(path.read_text(encoding="utf-8"))
        except UnicodeError as exc:
            raise ValueError("HTML input must be UTF-8") from exc
        parser.close()
        name = path.relative_to(root).as_posix()
        title = "".join(parser.title_parts).strip()
        description = parser.description.strip()
        findings = []
        if not title:
            findings.append(_finding("missing_title"))
        else:
            titles[title].append(name)
        if not description:
            findings.append(_finding("missing_description"))
        if not parser.h1_count:
            findings.append(_finding("missing_h1"))
        internal = nonlocal_count = 0
        if parser.has_base:
            findings.append(_finding("base_links_not_evaluated"))
        else:
            for href in parser.links:
                kind = _link_kind(root, path, href)
                if kind == "nonlocal":
                    nonlocal_count += 1
                else:
                    internal += 1
                    if kind != "local":
                        findings.append(_finding(kind, href))
        pages.append(
            {
                "path": name,
                "title": title,
                "description": description,
                "h1_count": parser.h1_count,
                "internal_links": internal,
                "nonlocal_links": nonlocal_count,
                "link_resolution": "NOT_EVALUATED"
                if parser.has_base
                else "LOCAL_FILES_ONLY",
                "findings": findings,
            }
        )
    return {
        "page_count": len(pages),
        "pages": pages,
        "duplicate_titles": [
            {"title": title, "paths": names}
            for title, names in sorted(titles.items())
            if len(set(names)) > 1  # Repetition means more than one distinct page.
        ],
        "external_links": "NOT_EVALUATED",
        "fragment_targets": "NOT_EVALUATED",
        "rendered_content": "NOT_EVALUATED",
        "search_performance": "NOT_EVALUATED",
    }
