"""Lossless split cases, based on literal input rather than generated oracles.

Syntax basis: YAML 1.2.2 (2021), sections 7.3, 7.4 and 8.1. Expected
values below are direct transcriptions of synthetic input, without units.
"""

from pathlib import Path

import pytest
from ruamel.yaml import YAML

from assetutilities.modules.yml_utilities import split_yaml_file_by_primary_key


def test_split_preserves_quoted_keys_flow_collections_and_literal_text(tmp_path):
    """Select collections and block scalars; omit only single-line scalars.

    Hand enumeration: points, settings, notes are retained; label is omitted.
    The quoted percent text and document-marker text are literal string data.
    """
    source = tmp_path / "sample.yml"
    source.write_text(
        "# dataset comment\n"
        'label: "header---tail"\n'
        '"points": [[0, 0], [1, 1]]  # pair comment\n'
        "settings: {enabled: true}\n"
        "notes: |\n"
        "  marker---inside\n"
        "  rate: %unchanged%\n",
        encoding="utf-8",
    )
    result = split_yaml_file_by_primary_key(source, tmp_path / "out")
    assert [Path(item["data"]).name for item in result] == [
        "sample_points.yml",
        "sample_settings.yml",
        "sample_notes.yml",
    ]
    expected = {
        "points": [[0, 0], [1, 1]],
        "settings": {"enabled": True},
        "notes": "marker---inside\nrate: %unchanged%\n",
    }
    for item, key in zip(result, expected):
        text = Path(item["data"]).read_text(encoding="utf-8-sig")
        assert YAML(typ="safe").load(text) == {key: expected[key]}
        assert "# dataset comment" in text
    assert '"points"' in Path(result[0]["data"]).read_text(encoding="utf-8-sig")
    assert "# pair comment" in Path(result[0]["data"]).read_text(encoding="utf-8-sig")


@pytest.mark.parametrize(
    "text",
    [
        "",
        "plain scalar\n",
        "- a\n- b\n",
        "good: [a]\nbad/name: [b]\n",
        "good: [a]\nbad\\name: [b]\n",
        "good: [a]\n'bad:name': [b]\n",
        "good: [a]\n'bad.': [b]\n",
        "good: [a]\n1: [b]\n",
        "name: [a]\nName: [b]\n",
    ],
)
def test_invalid_split_is_rejected_before_any_file_is_written(tmp_path, text):
    """Hand check: each root is invalid or contains an unusable filename key.

    Case-only names collide on case-insensitive filesystems. No partial split
    may remain when a later key is invalid.
    """
    source = tmp_path / "sample.yml"
    source.write_text(text, encoding="utf-8")
    output = tmp_path / "out"
    with pytest.raises(ValueError):
        split_yaml_file_by_primary_key(source, output)
    assert not output.exists()


def test_duplicate_keys_are_rejected_and_next_document_still_loads(tmp_path):
    """YAML 1.2.2 (2021), section 3.2.1.1: mapping keys are unique."""
    from ruamel.yaml.constructor import DuplicateKeyError

    source = tmp_path / "duplicate.yml"
    source.write_text("data: [a]\ndata: [b]\n", encoding="utf-8")
    output = tmp_path / "out"
    with pytest.raises(DuplicateKeyError):
        split_yaml_file_by_primary_key(source, output)
    assert not output.exists()
    source.write_text("data: [a]\n", encoding="utf-8")
    result = split_yaml_file_by_primary_key(source, output)
    assert YAML(typ="safe").load(Path(result[0]["data"])) == {"data": ["a"]}


def test_scalar_opt_in_and_aliases_are_readable_in_each_section(tmp_path):
    """The literal alias resolves to the same mapping in every output file.

    YAML 1.2.2 (2021), section 7.1 defines aliases. The source contains three
    keys, all selected when scalar skipping is disabled, including the label.
    """
    source = tmp_path / "sample.yml"
    source.write_text(
        '---\nlabel: "header---tail"\n'
        "defaults: &defaults {enabled: true}\n"
        "selected: {settings: *defaults}\n",
        encoding="utf-8-sig",
    )
    result = split_yaml_file_by_primary_key(
        source, tmp_path / "out", single_line_keys_skipped=False
    )
    assert [YAML(typ="safe").load(Path(item["data"])) for item in result] == [
        {"label": "header---tail"},
        {"defaults": {"enabled": True}},
        {"selected": {"settings": {"enabled": True}}},
    ]


def test_router_records_split_groups_and_applies_shaping(tmp_path):
    """The legacy router retains its grouped path return contract."""
    from assetutilities.modules.yml_utilities import RuamelYAML

    source = tmp_path / "sample.yml"
    source.write_text("label: omit\nrows:\n  - [1, 2]\n", encoding="utf-8")
    cfg = {
        "basename": "yaml_utilities",
        "file_management": {"input_files": {"yml": [str(source)]}},
        "Analysis": {"result_folder": str(tmp_path / "out")},
        "yml_analysis": {
            "divide": {"flag": True, "by": "primary_key"},
            "shape_output": {"flag": True},
        },
    }
    result = RuamelYAML().router(cfg)
    groups = result["yaml_utilities"]["divide"]["groups"]
    assert groups == [[{"data": str(tmp_path / "out" / "sample_rows.yml")}]]
    assert YAML(typ="safe").load(Path(groups[0][0]["data"])) == {"rows": [[1, 2]]}


@pytest.mark.parametrize("inside", [False, True])
def test_existing_output_symlink_cannot_redirect_a_section(tmp_path, inside):
    """An existing symlink must not redirect or alias an output section."""
    source = tmp_path / "sample.yml"
    source.write_text("section: [a]\n", encoding="utf-8")
    output = tmp_path / "out"
    output.mkdir()
    outside = (output if inside else tmp_path) / "outside.yml"
    outside.write_text("preserved\n", encoding="utf-8")
    try:
        (output / "sample_section.yml").symlink_to(outside)
    except OSError:
        pytest.skip("File symlinks are unavailable")
    with pytest.raises(ValueError):
        split_yaml_file_by_primary_key(source, output)
    assert outside.read_text(encoding="utf-8") == "preserved\n"


@pytest.mark.parametrize("text", ["section: [a\n", "a: [b]\n---\nc: [d]\n"])
def test_malformed_or_multiple_documents_create_no_output(tmp_path, text):
    """Only one well-formed document is accepted, YAML 1.2.2, section 9.1."""
    from ruamel.yaml.error import YAMLError

    source = tmp_path / "sample.yml"
    source.write_text(text, encoding="utf-8")
    output = tmp_path / "out"
    with pytest.raises(YAMLError):
        split_yaml_file_by_primary_key(source, output)
    assert not output.exists()
