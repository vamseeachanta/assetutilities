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
        newline="\n",
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
        text = Path(item["data"]).read_text(encoding="utf-8")
        assert YAML(typ="safe").load(text) == {key: expected[key]}
        assert "# dataset comment" in text
    assert '"points"' in Path(result[0]["data"]).read_text(encoding="utf-8")
    assert "# pair comment" in Path(result[0]["data"]).read_text(encoding="utf-8")


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
    source.write_text(text, encoding="utf-8", newline="\n")
    output = tmp_path / "out"
    with pytest.raises(ValueError):
        split_yaml_file_by_primary_key(source, output)
    assert not output.exists()


def test_duplicate_keys_are_rejected_and_next_document_still_loads(tmp_path):
    """YAML 1.2.2 (2021), section 3.2.1.1: mapping keys are unique."""
    from ruamel.yaml.constructor import DuplicateKeyError

    source = tmp_path / "duplicate.yml"
    source.write_text("data: [a]\ndata: [b]\n", encoding="utf-8", newline="\n")
    output = tmp_path / "out"
    with pytest.raises(DuplicateKeyError):
        split_yaml_file_by_primary_key(source, output)
    assert not output.exists()
    source.write_text("data: [a]\n", encoding="utf-8", newline="\n")
    result = split_yaml_file_by_primary_key(source, output)
    assert YAML(typ="safe").load(Path(result[0]["data"])) == {"data": ["a"]}


def test_scalar_opt_in_and_aliases_are_readable_in_each_section(tmp_path):
    """The literal alias resolves to the same mapping in every output file.

    YAML 1.2.2 (2021), section 7.1 defines aliases. The source contains three
    keys, all selected when scalar skipping is disabled, including the label.
    """
    source = tmp_path / "sample.yml"
    source.write_text(
        '\ufeff---\nlabel: "header---tail"\n'
        "defaults: &defaults {enabled: true}\n"
        "selected: {settings: *defaults}\n",
        encoding="utf-8",
        newline="\n",
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
    source.write_text(
        "label: omit\nrows:\n  - [1, 2]\n", encoding="utf-8", newline="\n"
    )
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
    assert groups == [[{"data": (tmp_path / "out" / "sample_rows.yml").as_posix()}]]
    assert YAML(typ="safe").load(Path(groups[0][0]["data"])) == {"rows": [[1, 2]]}


@pytest.mark.parametrize("inside", [False, True])
def test_existing_output_symlink_cannot_redirect_a_section(tmp_path, inside):
    """An existing symlink must not redirect or alias an output section."""
    source = tmp_path / "sample.yml"
    source.write_text("section: [a]\n", encoding="utf-8", newline="\n")
    output = tmp_path / "out"
    output.mkdir()
    outside = (output if inside else tmp_path) / "outside.yml"
    outside.write_text("preserved\n", encoding="utf-8", newline="\n")
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
    source.write_text(text, encoding="utf-8", newline="\n")
    output = tmp_path / "out"
    with pytest.raises(YAMLError):
        split_yaml_file_by_primary_key(source, output)
    assert not output.exists()


@pytest.mark.parametrize("shape_output", [False, True])
def test_root_merge_does_not_leak_keys_into_split_sections(tmp_path, shape_output):
    """A root merge contributes values, never extra keys in a section file."""
    source = tmp_path / "sample.yml"
    source.write_text(
        "defaults: &defaults\n"
        "  inherited: 1\n"
        "<<: *defaults\n"
        "section:\n"
        "  - 2\n",
        encoding="utf-8",
        newline="\n",
    )
    result = split_yaml_file_by_primary_key(
        source, tmp_path / "out", shape_output=shape_output
    )
    assert [Path(item["data"]).name for item in result] == [
        "sample_defaults.yml",
        "sample_section.yml",
    ]
    assert YAML(typ="safe").load(Path(result[0]["data"])) == {
        "defaults": {"inherited": 1}
    }
    assert YAML(typ="safe").load(Path(result[1]["data"])) == {"section": [2]}


@pytest.mark.parametrize("shape_output", [False, True])
@pytest.mark.parametrize("skip_scalars", [False, True])
def test_inherited_root_values_are_materialized_per_section(
    tmp_path, shape_output, skip_scalars
):
    """Inherited collections survive; explicit overrides and scalar opt-in hold."""
    source = tmp_path / "sample.yml"
    source.write_text(
        "defaults: &defaults\n"
        '  "points": [[1, 2]]\n'
        '  label: "inherited"\n'
        "  overridden: [0]\n"
        "<<: *defaults\n"
        "overridden: [3]\n",
        encoding="utf-8",
        newline="\n",
    )
    result = split_yaml_file_by_primary_key(
        source,
        tmp_path / "out",
        shape_output=shape_output,
        single_line_keys_skipped=skip_scalars,
    )
    expected = {
        "defaults": {
            "points": [[1, 2]],
            "label": "inherited",
            "overridden": [0],
        },
        "overridden": [3],
        "points": [[1, 2]],
    }
    if not skip_scalars:
        expected["label"] = "inherited"
    assert {Path(item["data"]).name for item in result} == {
        f"sample_{key}.yml" for key in expected
    }
    for item in result:
        path = Path(item["data"])
        key = path.stem.removeprefix("sample_")
        text = path.read_text(encoding="utf-8")
        assert YAML(typ="safe").load(text) == {key: expected[key]}
        assert not YAML().load(text).merge
        if key == "points":
            assert '"points"' in text
        if key == "label":
            assert '"inherited"' in text


@pytest.mark.parametrize("shape_output", [False, True])
def test_split_transfers_only_root_and_selected_key_comments(tmp_path, shape_output):
    """Fresh section roots retain their own quotes, comments and nested merges."""
    source = tmp_path / "sample.yml"
    source.write_text(
        "# document comment\n"
        "defaults: &defaults {enabled: true}  # other key comment\n"
        '"section":  # selected key comment\n'
        "  settings:\n"
        "    <<: *defaults\n"
        '    label: "quoted"\n',
        encoding="utf-8",
        newline="\n",
    )
    result = split_yaml_file_by_primary_key(
        source, tmp_path / "out", shape_output=shape_output
    )
    text = Path(result[1]["data"]).read_text(encoding="utf-8")
    assert YAML(typ="safe").load(text) == {
        "section": {"settings": {"enabled": True, "label": "quoted"}}
    }
    assert '"section"' in text
    assert '"quoted"' in text
    assert "# document comment" in text
    assert "# selected key comment" in text
    assert "<<:" in text


@pytest.mark.parametrize("shape_output", [False, True])
def test_split_retains_yaml_sets(tmp_path, shape_output):
    """A YAML set is a collection even when its entries have null values."""
    source = tmp_path / "sample.yml"
    source.write_text(
        "section: !!set\n  ? alpha\n  ? beta\n",
        encoding="utf-8",
        newline="\n",
    )
    result = split_yaml_file_by_primary_key(
        source, tmp_path / "out", shape_output=shape_output
    )
    assert len(result) == 1
    assert YAML(typ="safe").load(Path(result[0]["data"])) == {
        "section": {"alpha", "beta"}
    }


@pytest.mark.parametrize("shape_output", [False, True])
@pytest.mark.parametrize(
    ("scalar", "expected"),
    [
        ("|\n  alpha\n  beta\n", "alpha\nbeta\n"),
        (">\n  alpha\n  beta\n", "alpha beta\n"),
        ('"alpha\\nbeta"\n', "alpha\nbeta"),
    ],
)
def test_split_retains_tagged_block_and_multiline_scalars(
    tmp_path, shape_output, scalar, expected
):
    """Scalar style and underlying text determine selection, not the wrapper."""
    source = tmp_path / "sample.yml"
    source.write_text("section: !text " + scalar, encoding="utf-8", newline="\n")
    result = split_yaml_file_by_primary_key(
        source, tmp_path / "out", shape_output=shape_output
    )
    assert len(result) == 1
    data = YAML().load(Path(result[0]["data"]))
    assert list(data) == ["section"]
    assert data["section"].value == expected
    assert str(data["section"].tag) == "!text"


@pytest.mark.parametrize("shape_output", [False, True])
def test_tagged_single_line_scalar_still_requires_opt_in(tmp_path, shape_output):
    """A tag alone does not turn a single-line scalar into a split section."""
    source = tmp_path / "sample.yml"
    source.write_text("section: !text alpha\n", encoding="utf-8", newline="\n")
    assert (
        split_yaml_file_by_primary_key(
            source, tmp_path / "out", shape_output=shape_output
        )
        == []
    )
    result = split_yaml_file_by_primary_key(
        source,
        tmp_path / "out",
        shape_output=shape_output,
        single_line_keys_skipped=False,
    )
    assert YAML().load(Path(result[0]["data"]))["section"].value == "alpha"


@pytest.mark.parametrize("shape_output", [False, True])
def test_named_tag_handles_survive_in_each_standalone_section(tmp_path, shape_output):
    """YAML 1.2.2 (2021), section 6.8.2: handles require TAG directives."""
    source = tmp_path / "sample.yml"
    source.write_text(
        "%TAG !e! tag:example.org,2020:\n---\n"
        "section: !e!thing\n  value: 1\n"
        "nested:\n  items:\n    - !e!entry alpha\n",
        encoding="utf-8",
        newline="\n",
    )
    result = split_yaml_file_by_primary_key(
        source, tmp_path / "out", shape_output=shape_output
    )
    assert len(result) == 2
    first = YAML().load(Path(result[0]["data"]))
    second = YAML().load(Path(result[1]["data"]))
    assert list(first) == ["section"]
    assert first["section"] == {"value": 1}
    assert str(first["section"].tag) == "tag:example.org,2020:thing"
    assert list(second) == ["nested"]
    item = second["nested"]["items"][0]
    assert item.value == "alpha"
    assert str(item.tag) == "tag:example.org,2020:entry"


def test_split_text_output_is_utf8_without_bom_and_uses_lf(tmp_path):
    """Unicode data is emitted as UTF-8 with portable LF line endings."""
    source = tmp_path / "sample.yml"
    source.write_text("section: [café]\n", encoding="utf-8", newline="\n")
    result = split_yaml_file_by_primary_key(source, tmp_path / "out")
    raw = Path(result[0]["data"]).read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")
    assert b"\r" not in raw
    assert YAML(typ="safe").load(raw.decode("utf-8")) == {"section": ["café"]}


def test_directory_destination_is_rejected_before_writing_other_sections(tmp_path):
    """Directories, including directory junction targets, cannot be files."""
    source = tmp_path / "sample.yml"
    source.write_text("first: [a]\nsecond: [b]\n", encoding="utf-8", newline="\n")
    output = tmp_path / "out"
    directory = output / "sample_second.yml"
    directory.mkdir(parents=True)
    with pytest.raises(ValueError):
        split_yaml_file_by_primary_key(source, output)
    assert not (output / "sample_first.yml").exists()
    assert directory.is_dir()


def test_reparse_point_is_rejected_before_writing_other_sections(tmp_path, monkeypatch):
    """The Windows reparse flag covers junctions, including broken targets."""
    import stat
    from types import SimpleNamespace

    source = tmp_path / "sample.yml"
    source.write_text("first: [a]\nsecond: [b]\n", encoding="utf-8", newline="\n")
    output = tmp_path / "out"
    output.mkdir()
    blocked = output / "sample_second.yml"
    blocked.write_text("preserved\n", encoding="utf-8", newline="\n")
    original_lstat = Path.lstat

    def lstat_with_reparse_flag(path):
        info = original_lstat(path)
        if path == blocked:
            return SimpleNamespace(
                st_mode=info.st_mode,
                st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT,
            )
        return info

    monkeypatch.setattr(Path, "lstat", lstat_with_reparse_flag)
    with pytest.raises(ValueError):
        split_yaml_file_by_primary_key(source, output)
    assert not (output / "sample_first.yml").exists()
    assert blocked.read_text(encoding="utf-8") == "preserved\n"


def test_regular_destination_can_be_overwritten_and_returns_forward_slashes(tmp_path):
    """Ordinary files remain writable and the public result uses portable paths."""
    source = tmp_path / "sample.yml"
    source.write_text("section: [a]\n", encoding="utf-8", newline="\n")
    output = tmp_path / "out"
    output.mkdir()
    destination = output / "sample_section.yml"
    destination.write_text("old: [b]\n", encoding="utf-8", newline="\n")
    result = split_yaml_file_by_primary_key(source, output)
    assert result == [{"data": destination.as_posix()}]
    assert "\\" not in result[0]["data"]
    assert YAML(typ="safe").load(destination) == {"section": ["a"]}


@pytest.mark.parametrize("shape_output", [False, True])
def test_save_retains_tagged_keys_and_merged_tagged_collections(tmp_path, shape_output):
    """Handle declarations are needed on mapping keys and merge sources too."""
    from assetutilities.modules.yml_utilities import save_yml

    data = YAML().load(
        "%TAG !e! tag:example.org,2020:\n---\n"
        "section:\n  <<: !e!defaults {value: 1}\n"
        "  !e!key alpha: !e!values [2, 3]\n"
    )
    destination = tmp_path / "saved.yml"
    save_yml(data, destination, shape_output=shape_output)
    reloaded = YAML().load(destination)["section"]
    assert reloaded["value"] == 1
    entries = YAML().compose(destination).value[0][1].value
    merge_source = next(value for key, value in entries if key.value == "<<")
    assert merge_source.tag == "tag:example.org,2020:defaults"
    tagged_key = next(key for key in reloaded if not isinstance(key, str))
    assert tagged_key.value == "alpha"
    assert str(tagged_key.tag) == "tag:example.org,2020:key"
    assert reloaded[tagged_key] == [2, 3]
    assert str(reloaded[tagged_key].tag) == "tag:example.org,2020:values"
