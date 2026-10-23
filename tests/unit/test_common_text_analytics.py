"""Set comparison answers are derived by enumerating the synthetic inputs."""

from pathlib import Path

import pytest
import yaml

from assetutilities.common.text_analytics import TextAnalytics
from assetutilities.engine import engine


@pytest.mark.parametrize(
    "sets, expected",
    [
        (
            {"set1": ["b", "a", "b"], "set2": ["b", "c", "c"]},
            {"common": ["b"], "only_in_set1": ["a"], "only_in_set2": ["c"]},
        ),
        (
            {"set1": [], "set2": []},
            {"common": [], "only_in_set1": [], "only_in_set2": []},
        ),
    ],
)
def test_comparison(tmp_path, sets, expected):
    """b belongs to both lists; a only to the first, c only to the second.

    Duplicates do not add set members. Empty inputs have no members.
    """
    cfg = {
        "basename": "text_analytics",
        "data": sets,
        "Analysis": {"result_folder": str(tmp_path)},
    }
    result = TextAnalytics().router(cfg)
    summary = result["text_analytics"]["summary"]
    for key, values in expected.items():
        assert summary[key] == values
        assert summary["counts"][key] == len(values)
    assert summary["input_sizes"] == {key: len(values) for key, values in sets.items()}
    assert (
        yaml.safe_load(Path(result["text_analytics"]["output_file"]).read_text())
        == summary
    )


def test_text_analytics_engine(tmp_path):
    path = tmp_path / "input.yml"
    path.write_text(
        yaml.safe_dump(
            {"basename": "text_analytics", "data": {"set1": ["a"], "set2": ["a", "b"]}}
        )
    )
    result = engine(str(path))
    assert result["text_analytics"]["summary"]["only_in_set2"] == ["b"]
    assert (tmp_path / "results/input.yml").exists()


def test_rejects_non_list_input(tmp_path):
    with pytest.raises(ValueError, match="list"):
        TextAnalytics().router(
            {
                "data": {"set1": "abc", "set2": []},
                "Analysis": {"result_folder": str(tmp_path)},
            }
        )
