"""Check numeric retention through the learning-record interface.

Independent hand calculations for arbitrary synthetic diameters in metres:
area = pi * (outer_diameter**2 - inner_diameter**2) / 4, hence
(4**2 - 2**2) / 4 = 3 and (6**2 - 2**2) / 4 = 8 square metres per pi.
The divisor follows from radius = diameter / 2. These are synthetic operands,
not design defaults. Squaring, subtracting and dividing these operands is exact
in binary floating point; both paths use math.pi. Equality checks serialization
of finite floats, not an engineering acceptance limit. History counts below
come from one or two explicit writes; list indices are zero based.
"""

import json
import math
from copy import deepcopy
from pathlib import Path

from assetutilities.agent_os.integration.workflow_refresh import WorkflowRefreshManager


def _pipe_section_workflow(inputs: dict[str, float]) -> dict[str, object]:
    """Local deterministic stub; no external workflow execution is involved."""
    return {
        "area": math.pi
        * (inputs["outer_diameter_m"] ** 2 - inputs["inner_diameter_m"] ** 2)
        / 4,
        "unit": "m^2",
    }


def _assert_area(data: dict, expected_area: float) -> None:
    """Assert the serialized result against an independent hand reference."""
    assert isinstance(data["result"]["area"], float)
    assert data["result"]["area"] == expected_area
    assert data["result"]["unit"] == "m^2"


def test_workflow_area_survives_learning_reload(tmp_path: Path) -> None:
    inputs = {"outer_diameter_m": 4.0, "inner_diameter_m": 2.0}
    original_inputs = deepcopy(inputs)
    result = _pipe_section_workflow(inputs)
    original_result = deepcopy(result)
    execution_data = {"inputs": inputs, "result": result}
    original_data = deepcopy(execution_data)

    manager = WorkflowRefreshManager(tmp_path)
    manager.capture_learning(execution_data)
    del manager

    reader = WorkflowRefreshManager(tmp_path)
    history = json.loads((tmp_path / "context" / "learning.json").read_text())
    assert len(history) == 1
    _assert_area(history[0]["data"], 3 * math.pi)
    assert history[0]["data"] == original_data

    insights = reader.get_learning_insights()
    _assert_area(insights["latest_entry"]["data"], 3 * math.pi)
    assert insights["latest_entry"]["data"] == original_data
    assert inputs == original_inputs
    assert result == original_result
    assert execution_data == original_data


def test_learning_history_preserves_distinct_engineering_results(
    tmp_path: Path,
) -> None:
    first_inputs = {"outer_diameter_m": 4.0, "inner_diameter_m": 2.0}
    second_inputs = {"outer_diameter_m": 6.0, "inner_diameter_m": 2.0}
    original_first_inputs = deepcopy(first_inputs)
    original_second_inputs = deepcopy(second_inputs)
    first_result = _pipe_section_workflow(first_inputs)
    second_result = _pipe_section_workflow(second_inputs)
    original_first_result = deepcopy(first_result)
    original_second_result = deepcopy(second_result)
    first_data = {"inputs": first_inputs, "result": first_result}
    second_data = {"inputs": second_inputs, "result": second_result}
    original_first_data = deepcopy(first_data)
    original_second_data = deepcopy(second_data)

    manager = WorkflowRefreshManager(tmp_path)
    manager.capture_learning(first_data)
    del manager

    manager = WorkflowRefreshManager(tmp_path)
    manager.capture_learning(second_data)
    del manager

    reader = WorkflowRefreshManager(tmp_path)
    history = json.loads((tmp_path / "context" / "learning.json").read_text())
    assert len(history) == 2
    _assert_area(history[0]["data"], 3 * math.pi)
    _assert_area(history[1]["data"], 8 * math.pi)
    assert [entry["data"] for entry in history] == [
        original_first_data,
        original_second_data,
    ]

    insights = reader.get_learning_insights()
    assert insights["total_entries"] == 2
    _assert_area(insights["latest_entry"]["data"], 8 * math.pi)
    assert insights["latest_entry"]["data"] == original_second_data
    assert first_inputs == original_first_inputs
    assert second_inputs == original_second_inputs
    assert first_result == original_first_result
    assert second_result == original_second_result
    assert first_data == original_first_data
    assert second_data == original_second_data
