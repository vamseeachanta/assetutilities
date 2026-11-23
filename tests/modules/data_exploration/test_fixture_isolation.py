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


@pytest.mark.parametrize("input_file", FIXTURES)
def test_data_exploration_heading_statistics_match_hand_calculation(
    input_file, data_exploration_run
):
    # Source: csv/test_1.csv and csv/test_2.csv, Heading, rows 2 through 26.
    # Both contain 25 values from 0 to 360 in steps of 15: min=0, max=360.
    # Mean: sum=4500, 4500/25=180. Sample variance about that mean:
    # 15**2 * 2 * (1**2 + ... + 12**2) / 24 = 225*1300/24 = 12187.5.
    # Sample stdev is sqrt(12187.5); expectations do not use engine output.
    # Basis: OpenStax, Introductory Statistics, 2nd ed., sections 2.5 and 2.7.
    expected = {
        "min": 0.0,
        "max": 360.0,
        "mean": 180.0,
        "stdev": 110.39701082909808,
    }
    cfg = data_exploration_run(input_file)
    tables = _csv_tables(cfg)
    prefix = cfg["Analysis"]["file_name"]

    if cfg["type"]["df_statistics"]["flag"]:
        columns = tables[Path(f"{prefix}_column.csv")]
        assert len(columns.columns) == 2
        for statistic, value in expected.items():
            summary = tables[Path(f"{prefix}_{statistic}.csv")]
            for label in columns:
                heading = summary.loc[columns[label] == "Heading", label]
                assert heading.tolist() == pytest.approx([value], rel=1e-12, abs=1e-12)
            transposed = tables[Path(f"{prefix}_{statistic}_T.csv")]
            heading = transposed.set_index("input_file")["Heading"]
            assert heading.to_dict() == pytest.approx(
                {label: value for label in columns}, rel=1e-12, abs=1e-12
            )
    else:
        assert len(tables) == 2
        for table in tables.values():
            statistics = table.dropna(subset=["statistic"]).set_index("statistic")
            assert statistics["Heading"].to_dict() == pytest.approx(
                expected, rel=1e-12, abs=1e-12
            )
