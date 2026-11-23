# ABOUTME: Tests for issue #52 in-repo sub-tasks: ruamel YAML split + X-Y plot helper.
# ABOUTME: Verifies round-trip-preserving split (N files, content) and plot file creation.
import os

import pytest

from assetutilities.modules.yml_utilities import (
    save_yml,
    split_yaml_file_by_primary_key,
)

SAMPLE_YAML = """\
# top of file
scalar_key: just a value

block_one:
  # a comment inside block_one
  alpha: 1
  beta: 2

block_two:
  numbers:
    - 10
    - 20
    - 30
"""


def _write_sample(tmp_path):
    src = tmp_path / "sample.yml"
    src.write_text(SAMPLE_YAML, encoding="utf-8")
    return src


def test_split_produces_expected_files(tmp_path):
    src = _write_sample(tmp_path)
    out_dir = tmp_path / "out"

    result = split_yaml_file_by_primary_key(str(src), str(out_dir))

    # scalar_key is single-line -> skipped; block_one + block_two emitted.
    out_files = sorted(os.path.basename(r["data"]) for r in result)
    assert out_files == ["sample_block_one.yml", "sample_block_two.yml"]
    for r in result:
        assert os.path.exists(r["data"])


def test_split_round_trip_preserves_content_and_comments(tmp_path):
    src = _write_sample(tmp_path)
    out_dir = tmp_path / "out"

    result = split_yaml_file_by_primary_key(str(src), str(out_dir))
    by_name = {os.path.basename(r["data"]): r["data"] for r in result}

    # Re-load each split file round-trip and check the data is intact.
    b1_text = open(by_name["sample_block_one.yml"], encoding="utf-8-sig").read()
    assert "block_one:" in b1_text
    assert "alpha: 1" in b1_text
    assert "beta: 2" in b1_text
    # ruamel round-trip preserves the inner comment.
    assert "a comment inside block_one" in b1_text

    b2_text = open(by_name["sample_block_two.yml"], encoding="utf-8-sig").read()
    assert "block_two:" in b2_text
    assert "- 10" in b2_text and "- 30" in b2_text


def test_save_yml_round_trip(tmp_path):
    out = tmp_path / "saved.yml"
    save_yml({"k": {"nested": [1, 2, 3]}}, str(out))
    assert out.exists()
    text = open(out, encoding="utf-8-sig").read()
    assert "k:" in text and "nested:" in text


def test_save_yml_via_savedatayaml_ruamel_mode(tmp_path):
    # Previously the "ruamel" / "round_trip_dump" branches raised NameError.
    from assetutilities.common.saveData import saveDataYaml

    base = tmp_path / "ruamel_save"
    saveDataYaml({"a": {"b": 1}}, str(base), default_flow_style="round_trip_dump")
    written = str(base) + ".yml"
    assert os.path.exists(written)
    text = open(written, encoding="utf-8-sig").read()
    assert "a:" in text and "b: 1" in text


def test_plot_xy_from_arrays_matplotlib(tmp_path):
    pytest.importorskip("matplotlib")
    from assetutilities.common.visualization.xy_plot_from_arrays import (
        plot_xy_from_arrays,
    )

    x = [0, 1, 2, 3, 4]
    y = [0, 1, 4, 9, 16]
    out_path = plot_xy_from_arrays(
        x,
        y,
        str(tmp_path),
        file_name="issue52_xy",
        title="Issue 52 XY",
        xlabel="x",
        ylabel="y = x^2",
        plt_engine="matplotlib",
    )

    assert out_path.endswith(".png")
    assert os.path.exists(out_path)
    assert os.path.getsize(out_path) > 0
