"""Keep tracked-text regression tests in the unconditional CI gates."""

from pathlib import Path

import yaml


def test_hygiene_tests_run_in_gates() -> None:
    root = Path(__file__).resolve().parents[2]
    with (root / ".github/workflows/tests.yml").open(
        encoding="utf-8", newline="\n"
    ) as stream:
        workflow = yaml.safe_load(stream)
    steps = workflow["jobs"]["gates"]["steps"]
    hygiene_steps = [
        step
        for step in steps
        if step.get("run") == "uv run python -m pytest tests/hygiene"
    ]
    assert len(hygiene_steps) == 1
    assert "if" not in workflow["jobs"]["gates"]
    assert "if" not in hygiene_steps[0]
