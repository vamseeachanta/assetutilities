from pathlib import Path

import pandas as pd
from pandas.testing import assert_frame_equal
import pytest
import yaml

from assetutilities.engine import engine


FIXTURES = (
    "df_basic_statistics.yml",
    "df_basic_statistics_add_to_df.yml",
    "df_statistics.yml",
    "df_statistics_file_management.yml",
)


@pytest.mark.parametrize("input_file", FIXTURES)
def test_data_exploration_runs_use_distinct_output_roots(
    input_file, prepare_data_exploration_run, tmp_path
):
    first_input = prepare_data_exploration_run(input_file)
    second_input = prepare_data_exploration_run(input_file)
    assert first_input.parent != second_input.parent
    first = engine(str(first_input))
    second = engine(str(second_input))

    for folder in ("analysis_root_folder", "result_folder", "log_folder"):
        first_root = Path(first["Analysis"][folder]).resolve()
        second_root = Path(second["Analysis"][folder]).resolve()
        assert first_root != second_root
        assert first_root.is_relative_to(tmp_path)
        assert second_root.is_relative_to(tmp_path)
        assert first_root.is_relative_to(first_input.parent)
        assert second_root.is_relative_to(second_input.parent)


@pytest.mark.parametrize("input_file", FIXTURES)
def test_prepared_runs_preserve_fixture_inputs(
    input_file, prepare_data_exploration_run
):
    fixture_dir = Path(__file__).parent
    source = yaml.safe_load((fixture_dir / input_file).read_text(encoding="utf-8"))
    prepared_input = prepare_data_exploration_run(input_file)
    prepared = yaml.safe_load(prepared_input.read_text(encoding="utf-8"))
    run_root = prepared_input.parent
    source_csvs = {
        path.name: path.read_bytes() for path in (fixture_dir / "csv").glob("*.csv")
    }
    expected_files = {Path(input_file), *(Path("csv") / name for name in source_csvs)}
    assert {
        p.relative_to(run_root) for p in run_root.rglob("*") if p.is_file()
    } == expected_files
    assert {
        p.name: p.read_bytes() for p in (run_root / "csv").glob("*.csv")
    } == source_csvs

    for group, original in zip(prepared["data"]["groups"], source["data"]["groups"]):
        assert (
            Path(group["file_name"])
            == run_root / "csv" / Path(original["file_name"]).name
        )
        group["file_name"] = original["file_name"]
    if source["data"]["type"] == "file_management":
        assert Path(prepared["file_management"]["input_directory"]) == run_root / "csv"
        prepared["file_management"]["input_directory"] = source["file_management"][
            "input_directory"
        ]
    assert prepared == source


def _csv_tables(cfg):
    result_folder = Path(cfg["Analysis"]["result_folder"])
    tables = {
        path.relative_to(result_folder): pd.read_csv(path)
        for path in result_folder.glob("*.csv")
    }
    assert tables
    return tables


@pytest.mark.parametrize("input_file", FIXTURES)
def test_data_exploration_runs_retain_equivalent_outputs(
    input_file, data_exploration_run
):
    first = data_exploration_run(input_file)
    first_tables = _csv_tables(first)
    first_result_folder = Path(first["Analysis"]["result_folder"])
    retained_files = {
        path: path.read_bytes()
        for path in first_result_folder.rglob("*")
        if path.is_file()
    }
    first_log = Path(first["Analysis"]["log_folder"]) / (
        first["Analysis"]["file_name"] + ".log"
    )

    second = data_exploration_run(input_file)
    second_tables = _csv_tables(second)
    second_log = Path(second["Analysis"]["log_folder"]) / (
        second["Analysis"]["file_name"] + ".log"
    )
    assert first_log.read_text(encoding="utf-8")
    assert second_log.read_text(encoding="utf-8")
    assert {
        path: path.read_bytes()
        for path in first_result_folder.rglob("*")
        if path.is_file()
    } == retained_files
    assert first_tables.keys() == second_tables.keys()
    for name, first_table in first_tables.items():
        assert not first_table.empty
        assert_frame_equal(first_table, second_tables[name], check_exact=True)
