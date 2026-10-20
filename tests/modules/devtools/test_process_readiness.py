"""Synthetic policy A (2026), independent acceptance examples.

No empirical constants are used. The example policy explicitly chooses a
maximum of 8 hours per accepted item and a minimum of 2 accepted items per
review. By direct comparison, 6 <= 8 and 3 >= 2 pass; 9 <= 8 fails; equality
passes. These are illustrative inputs, not recommended business targets.
"""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from assetutilities.devtools.process_readiness import assess, load_register, main


@pytest.fixture
def register():
    return {
        "roles": ["coordinator", "reviewer"],
        "processes": [
            {
                "id": area,
                "area": area,
                "accountable_role": "coordinator",
                "backup_role": "reviewer",
                "procedure_ref": "synthetic procedure A, section Method (2026)",
                "handoff_ref": "synthetic handoff record A (2026)",
                "metrics": [
                    {
                        "id": "effort",
                        "value": 6,
                        "unit": "hours per accepted item",
                        "evidence_ref": "synthetic observation A (2026)",
                        "criterion": {
                            "operator": "at_most",
                            "target": 8,
                            "source_ref": "synthetic policy A, Elapsed effort (2026)",
                        },
                    }
                ],
            }
            for area in ("sales", "process", "productivity")
        ],
    }


def find(report, check, process_id="sales"):
    return next(
        item
        for item in report["checks"]
        if item["process_id"] == process_id and item["check"] == check
    )


def test_complete_register_passes_without_mutation(register):
    """Three areas times five checks gives 15 passes by hand enumeration."""
    original = copy.deepcopy(register)
    report = assess(register)
    assert register == original
    assert report["status"] == "PASS"
    assert report["summary"] == {"PASS": 15, "FAIL": 0, "NOT_EVALUATED": 0}
    assert all(item["action"] is None for item in report["checks"])


@pytest.mark.parametrize(
    ("operator", "value", "target", "expected"),
    [
        ("at_most", 6, 8, "PASS"),
        ("at_most", 8, 8, "PASS"),
        ("at_most", 9, 8, "FAIL"),
        ("at_least", 3, 2, "PASS"),
        ("at_least", 2, 2, "PASS"),
        ("at_least", 1, 2, "FAIL"),
        ("at_most", 0, 0, "PASS"),
        ("at_least", -3, -2, "FAIL"),
    ],
)
def test_direct_policy_comparisons(register, operator, value, target, expected):
    """Expected results follow the inequalities in the module docstring.

    Zero equals zero. For a signed caller-defined metric, -3 is below -2.
    """
    metric = register["processes"][0]["metrics"][0]
    metric["value"] = value
    metric["criterion"].update(operator=operator, target=target)
    report = assess(register)
    result = find(report, "metric:effort")
    assert result["status"] == expected
    assert result["measurement"] == metric
    assert report["status"] == expected


@pytest.mark.parametrize(
    ("field", "check"),
    [
        ("accountable_role", "accountability"),
        ("backup_role", "backup"),
        ("procedure_ref", "procedure"),
        ("handoff_ref", "handoff"),
        ("metrics", "measurement"),
    ],
)
def test_missing_process_evidence_is_not_evaluated(register, field, check):
    del register["processes"][0][field]
    report = assess(register)
    result = find(report, check)
    assert result["status"] == "NOT_EVALUATED"
    assert result["action"]
    assert report["status"] == "NOT_EVALUATED"


@pytest.mark.parametrize("field", ["value", "evidence_ref", "criterion"])
def test_missing_metric_basis_is_not_evaluated(register, field):
    del register["processes"][0]["metrics"][0][field]
    result = find(assess(register), "metric:effort")
    assert result["status"] == "NOT_EVALUATED"
    assert result["action"]


def test_criterion_without_source_is_not_evaluated(register):
    del register["processes"][0]["metrics"][0]["criterion"]["source_ref"]
    result = find(assess(register), "metric:effort")
    assert result["status"] == "NOT_EVALUATED"
    assert "source" in result["action"]


def test_same_role_backup_fails_and_failure_takes_precedence(register):
    process = register["processes"][0]
    process["backup_role"] = process["accountable_role"]
    process.pop("handoff_ref")
    report = assess(register)
    assert find(report, "backup")["status"] == "FAIL"
    assert report["status"] == "FAIL"


def test_omitted_area_is_not_silently_passed(register):
    register["processes"] = register["processes"][:1]
    report = assess(register)
    missing = [item for item in report["checks"] if item["check"] == "area_coverage"]
    assert {item["area"] for item in missing} == {"process", "productivity"}
    assert all(item["status"] == "NOT_EVALUATED" for item in missing)
    assert report["status"] == "NOT_EVALUATED"


def test_minimal_record_is_accepted_as_unknown():
    report = assess({"roles": [], "processes": [{"id": "intake", "area": "sales"}]})
    assert report["status"] == "NOT_EVALUATED"
    assert all(item["status"] == "NOT_EVALUATED" for item in report["checks"])


@pytest.mark.parametrize(
    "change",
    [
        lambda r: r.update(unknown=True),
        lambda r: r.update(roles="reviewer"),
        lambda r: r.update(roles=["reviewer", "reviewer"]),
        lambda r: r.update(processes=[]),
        lambda r: r["processes"].append(copy.deepcopy(r["processes"][0])),
        lambda r: r["processes"][0].update(area="unknown"),
        lambda r: r["processes"][0].update(accountable_role="unregistered"),
        lambda r: r["processes"][0].update(backup_role="unregistered"),
        lambda r: r["processes"][0].update(procedure_ref="  "),
        lambda r: r["processes"][0].update(id=""),
        lambda r: r["processes"][0].update(unknown=True),
        lambda r: r["processes"][0].update(metrics={}),
        lambda r: r["processes"][0]["metrics"].append(
            copy.deepcopy(r["processes"][0]["metrics"][0])
        ),
        lambda r: r["processes"][0]["metrics"][0].update(unit=""),
        lambda r: r["processes"][0]["metrics"][0].update(value=True),
        lambda r: r["processes"][0]["metrics"][0].update(value="6"),
        lambda r: r["processes"][0]["metrics"][0].update(value=float("nan")),
        lambda r: r["processes"][0]["metrics"][0].update(value=float("inf")),
        lambda r: r["processes"][0]["metrics"][0].update(unknown=True),
        lambda r: r["processes"][0]["metrics"][0]["criterion"].update(operator="lt"),
        lambda r: r["processes"][0]["metrics"][0]["criterion"].update(target=False),
        lambda r: r["processes"][0]["metrics"][0]["criterion"].pop("target"),
        lambda r: r["processes"][0]["metrics"][0]["criterion"].update(unknown=True),
    ],
)
def test_invalid_input_rejected_before_assessment(register, change):
    change(register)
    with pytest.raises(ValueError):
        assess(register)


@pytest.mark.parametrize("payload", [None, [], {}, {"roles": [], "processes": [None]}])
def test_malformed_containers_rejected(payload):
    with pytest.raises(ValueError):
        assess(payload)


@pytest.mark.parametrize(
    "text",
    [
        '{"roles": [], "roles": [], "processes": []}',
        '{"roles": [], "processes": [], "value": NaN}',
        '{"roles": [], "processes": [], "value": Infinity}',
        "not JSON",
    ],
)
def test_loader_rejects_ambiguous_json(tmp_path, text):
    path = tmp_path / "register.json"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError):
        load_register(path)


def test_cli_pass_and_failure_exit_codes(register, tmp_path, capsys):
    """CLI contract: success=0, rejected input=2, non-pass assessment=1."""
    path = tmp_path / "register.json"
    path.write_text(json.dumps(register), encoding="utf-8")
    assert main([str(path)]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "PASS"
    register["processes"][0]["metrics"][0]["value"] = 9
    path.write_text(json.dumps(register), encoding="utf-8")
    assert main([str(path)]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "FAIL"
    path.write_text('{"roles": [], "processes": [{"id":"x","area":"sales"}]}')
    assert main([str(path)]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "NOT_EVALUATED"


@pytest.mark.parametrize("kind", ["missing", "invalid", "encoding"])
def test_cli_rejects_input_without_echoing_content_or_path(tmp_path, capsys, kind):
    path = tmp_path / "input-marker.json"
    if kind == "invalid":
        path.write_text('{"unexpected": "content-marker"}', encoding="utf-8")
    elif kind == "encoding":
        path.write_bytes(b"\xff")
    assert main([str(path)]) == 2
    captured = capsys.readouterr()
    assert not captured.out
    assert "input-marker" not in captured.err
    assert "content-marker" not in captured.err


def test_published_example_runs_as_module():
    root = Path(__file__).resolve().parents[3]
    env = dict(os.environ, PYTHONPATH=str(root / "src"))
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "assetutilities.devtools.process_readiness",
            str(root / "examples/devtools/process-readiness.json"),
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "PASS"
    assert report["summary"] == {"PASS": 15, "FAIL": 0, "NOT_EVALUATED": 0}
