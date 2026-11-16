"""Structure-preserving row formatting, YAML 1.2.2 (2021), section 7.4.1."""

import copy

import pytest
from ruamel.yaml import YAML

from assetutilities.modules.yml_utilities import save_yml


@pytest.mark.parametrize(
    "rows",
    [
        [[1, 2, 3], [4, 5]],
        [["a, b", "c: d"], ["[x]", "#note"]],
        [[True, None], [False, "null"]],
        [["a\nb", "c"], ["d", "e"]],
    ],
)
def test_shaping_preserves_every_value_and_input_object(tmp_path, rows):
    """Expected rows are the literal synthetic input, with no calculation.

    Three-element rows must retain all entries; commas, colons and newlines
    belong to scalar values and must not become YAML delimiters.
    """
    data = {"rows": rows}
    before = copy.deepcopy(data)
    destination = tmp_path / "shaped.yml"
    save_yml(data, destination, shape_output=True)
    assert YAML(typ="safe").load(destination) == before
    assert data == before


def test_shaping_keeps_block_scalar_text_and_row_comments(tmp_path):
    """The apparent sequence in the note is literal YAML block-scalar text."""
    data = YAML().load(
        "note: |\n  - - alpha\n    - beta\n" "rows:\n  - - 1  # first entry\n    - 2\n"
    )
    destination = tmp_path / "shaped.yml"
    save_yml(data, destination, shape_output=True)
    assert YAML(typ="safe").load(destination) == {
        "note": "- - alpha\n  - beta\n",
        "rows": [[1, 2]],
    }
    assert "# first entry" in destination.read_text(encoding="utf-8-sig")


def test_shaping_emits_scalar_pairs_in_flow_style(tmp_path):
    """The formatting contract is a two-scalar row written as '[a, b]'."""
    destination = tmp_path / "shaped.yml"
    save_yml({"rows": [[1, 2], [3, 4]]}, destination, shape_output=True)
    text = destination.read_text(encoding="utf-8-sig")
    assert "- [1, 2]" in text
    assert "- [3, 4]" in text
