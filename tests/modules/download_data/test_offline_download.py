"""Synthetic ZIP and URL-schema tests with no external-service requests."""

import io
import zipfile
from pathlib import Path

import pytest
import requests
import yaml

from assetutilities.common.download_data.dwnld_from_zipurl import DownloadDataFromURL


@pytest.mark.parametrize(
    "urls",
    [
        {"sample": "https://example.invalid/sample.zip"},
        [{"url": "https://example.invalid/sample.zip"}],
        ["https://example.invalid/sample.zip"],
    ],
)
def test_supported_url_shapes(monkeypatch, urls):
    calls = []
    downloader = DownloadDataFromURL()
    monkeypatch.setattr(
        downloader, "download_and_process_zip", lambda url, cfg: calls.append(url)
    )
    cfg = {"input_data": {"urls": urls}}
    assert downloader.router(cfg) is cfg
    assert calls == ["https://example.invalid/sample.zip"]


@pytest.mark.parametrize(
    "urls", [None, "invalid", [None], [{"wrong": "url"}], {"bad": None}]
)
def test_bad_url_shapes_fail_before_request(monkeypatch, urls):
    def unexpected(*args, **kwargs):
        pytest.fail("invalid configuration reached a request")

    monkeypatch.setattr(DownloadDataFromURL, "download_and_process_zip", unexpected)
    with pytest.raises(ValueError, match="urls"):
        DownloadDataFromURL().router({"input_data": {"urls": urls}})


def test_packaged_download_basename():
    path = (
        Path(__file__).resolve().parents[3]
        / "src/assetutilities/base_configs/modules/download_data/download_data.yml"
    )
    assert yaml.safe_load(path.read_text())["basename"] == "download_data"


def test_zip_download_offline(monkeypatch, tmp_path):
    """Independent expected CSV: the archive contains exactly label,value/sample,ok.

    Method: extract the sole CSV member and prefix its stem with the URL stem.
    Expected answer: archive_sample.csv with the same header and row.
    """
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr("nested/sample.csv", "label,value\nsample,ok\n")
    response = requests.Response()
    response.status_code = requests.codes.ok
    response._content = archive.getvalue()
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: response)
    cfg = {"input_data": {"out_directory": str(tmp_path)}}
    DownloadDataFromURL().download_and_process_zip(
        "https://example.invalid/archive.zip", cfg
    )
    assert (tmp_path / "archive_sample.csv").read_text() == "label,value\nsample,ok\n"


def test_http_error_propagates(monkeypatch, tmp_path):
    def fail(*args, **kwargs):
        raise requests.HTTPError("synthetic error")

    monkeypatch.setattr(requests, "get", fail)
    with pytest.raises(requests.HTTPError, match="synthetic"):
        DownloadDataFromURL().download_and_process_zip(
            "https://example.invalid/archive.zip",
            {"input_data": {"out_directory": str(tmp_path)}},
        )
    assert list(tmp_path.iterdir()) == []
