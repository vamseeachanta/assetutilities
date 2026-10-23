"""Offline examples for the ZIP-to-CSV boundary; no engineering data is used."""

import io
import zipfile

import pytest
import requests

from assetutilities.common.download_data.dwnld_from_zipurl import DownloadDataFromURL


@pytest.fixture(autouse=True)
def reject_network(monkeypatch):
    def unexpected_request(*args, **kwargs):
        pytest.fail("Offline ZIP tests must not send HTTP requests")

    monkeypatch.setattr(requests.sessions.Session, "request", unexpected_request)


def test_download_and_process_zip_mocked(monkeypatch, tmp_path):
    """Hand calculation: ZIP stem + '_' + member stem + '.csv'.

    APDRawData.zip and well_data/sample.csv yield APDRawData_sample.csv.
    Reading then writing the synthetic CSV preserves its header and sole row:
    a,b followed by 1,2. A directory member produces no output file.
    """
    payload = "a,b\n1,2\n"
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr("well_data/", "")
        zipped.writestr("well_data/sample.csv", payload)
    calls = []

    class FakeResponse:
        content = archive.getvalue()

        def raise_for_status(self):
            calls.append("status checked")

    url = "https://example.invalid/APDRawData.zip"

    def fake_get(request_url, *, timeout):
        assert request_url == url
        assert timeout is not None
        return FakeResponse()

    monkeypatch.setattr(requests, "get", fake_get)
    cfg = {"input_data": {"out_directory": str(tmp_path)}}
    DownloadDataFromURL().download_and_process_zip(url, cfg)

    assert calls == ["status checked"]
    assert [path.name for path in tmp_path.iterdir()] == ["APDRawData_sample.csv"]
    assert (tmp_path / "APDRawData_sample.csv").read_text() == payload


def test_http_failure_writes_no_output(monkeypatch, tmp_path):
    """A failed HTTP status raises before ZIP processing; output set is empty."""

    class FailedResponse:
        def raise_for_status(self):
            raise requests.HTTPError("synthetic response failure")

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: FailedResponse())
    cfg = {"input_data": {"out_directory": str(tmp_path)}}
    with pytest.raises(requests.HTTPError, match="synthetic response failure"):
        DownloadDataFromURL().download_and_process_zip(
            "https://example.invalid/archive.zip",
            cfg,
        )
    assert list(tmp_path.iterdir()) == []
