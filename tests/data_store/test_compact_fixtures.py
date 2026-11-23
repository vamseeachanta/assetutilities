"""Exercise compact tabular fixtures through stem compression."""

import csv
from io import StringIO
from pathlib import Path
from zipfile import ZipFile

from assetutilities.modules.zip_utilities.zip_utilities import ZipUtilities


def test_compact_tables_preserve_archive_members_and_rows(tmp_path):
    root = Path(__file__).resolve().parents[2]
    source = root / "tests/modules/zip_utilities/compact"
    cfg = {"Analysis": {"result_folder": str(tmp_path)}}
    result = ZipUtilities._process_single_stem(cfg, "response", str(source), ["csv"])
    assert result["error"] is None
    with ZipFile(result["zip_file_path"]) as archive:
        assert sorted(archive.namelist()) == [
            "response_member_1.csv",
            "response_member_2.csv",
            "response_member_3.csv",
        ]
        for name in archive.namelist():
            text = archive.read(name).decode("utf-8-sig")
            rows = list(csv.reader(StringIO(text)))
            assert len(rows) == 1001
            assert rows[0] == [
                "time",
                "x displacment",
                "y displacment",
                "x velocity",
                "y velocity",
                "FX Force",
                "FY Force",
                "FZ Force",
            ]
            assert len(rows[1]) == len(rows[0])
            assert float(rows[-1][0]) > float(rows[1][0])
