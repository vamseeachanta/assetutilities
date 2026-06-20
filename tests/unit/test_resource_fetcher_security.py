# ABOUTME: Security regression tests for web-contextualization ResourceFetcher.
# ABOUTME: Pins the http/https scheme allowlist added in review 2026-05-23.

import importlib.util
import tempfile
from pathlib import Path

import pytest

# The module lives under a hyphenated directory ("web-contextualization") and
# is not importable as a normal package, so load it by file path.
_MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "modules"
    / "web-contextualization"
    / "resource_fetcher.py"
)


def _load_resource_fetcher():
    spec = importlib.util.spec_from_file_location(
        "resource_fetcher_under_test", _MODULE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ResourceFetcher


ResourceFetcher = _load_resource_fetcher()


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "gopher://example.com/1",
        "ftp://example.com/x",
        "FILE:///etc/passwd",
    ],
)
def test_fetch_rejects_non_http_schemes(url):
    """Non-http(s) schemes must be rejected before any fetch is attempted."""
    with tempfile.TemporaryDirectory() as tmp:
        fetcher = ResourceFetcher(cache_dir=Path(tmp))
        path, metadata = fetcher.fetch(url)

    assert path is None
    assert metadata["status"] == "failed"
    assert "scheme" in (metadata["error"] or "").lower()


def test_fetch_accepts_http_scheme_passes_validation():
    """An http(s) URL passes the scheme gate (network call may still fail).

    We only assert that the failure, if any, is NOT the scheme rejection — i.e.
    the allowlist let an http URL through.
    """
    with tempfile.TemporaryDirectory() as tmp:
        fetcher = ResourceFetcher(cache_dir=Path(tmp))
        # Unroutable TEST-NET-1 address with a short timeout-ish path; the call
        # will fail to connect, but the error must not be a scheme rejection.
        path, metadata = fetcher.fetch("http://192.0.2.1/nope.html")

    error = (metadata.get("error") or "").lower()
    assert "scheme" not in error
