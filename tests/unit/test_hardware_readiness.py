"""Hardware checklist tests use synthetic observations, not device ratings."""

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from assetutilities.cli.hardware_readiness import assess_readiness

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples" / "hardware_readiness" / "observations.json"


@pytest.fixture
def complete_input():
    """Synthetic policy inputs; no number represents a hardware specification."""
    return {
        "requirements": {
            "shared_storage": {"minimum_capacity_bytes": 1000},
            "displays": {"minimum_count": 2},
            "wired_network": {
                "minimum_observation_seconds": 3600,
                "maximum_outages": 1,
            },
            "kvm": {"minimum_computers": 3},
        },
        "observations": {
            "graphics": {"functional": True},
            "audio": {"playback": True},
            "shared_storage": {"capacity_bytes": 1200, "smb_access": True},
            "displays": {"simultaneous_count": 2},
            "remote_access": {"login": True, "graphical_session": True},
            "meeting_audio": {"capture": True, "playback": True},
            "wired_network": {
                "link": True,
                "observation_seconds": 3600,
                "outages": 1,
            },
            "kvm": {
                "switched_computers": 3,
                "keyboard": True,
                "mouse": True,
                "video": True,
            },
        },
    }


def checks_by_id(report):
    return {check["id"]: check for check in report["checks"]}


def test_complete_checklist_at_boundaries(complete_input):
    """Hand oracle: 1200 >= 1000 bytes; 2 >= 2 displays; 3600 >= 3600
    observation seconds; 1 <= 1 outage; 3 >= 3 computers. All supplied
    functional results are true, so all eight checklist areas pass.
    """
    original = copy.deepcopy(complete_input)
    report = assess_readiness(complete_input)
    assert complete_input == original
    assert report["status"] == "PASS"
    assert set(checks_by_id(report)) == {
        "graphics",
        "audio",
        "shared_storage",
        "displays",
        "remote_access",
        "meeting_audio",
        "wired_network",
        "kvm",
    }
    assert all(check["status"] == "PASS" for check in report["checks"])
    assert all(check["missing"] == check["failed"] == [] for check in report["checks"])


@pytest.mark.parametrize(
    "area,field,value",
    [
        ("graphics", "functional", False),
        ("audio", "playback", False),
        ("shared_storage", "capacity_bytes", 999),
        ("shared_storage", "smb_access", False),
        ("displays", "simultaneous_count", 1),
        ("remote_access", "login", False),
        ("remote_access", "graphical_session", False),
        ("meeting_audio", "capture", False),
        ("meeting_audio", "playback", False),
        ("wired_network", "link", False),
        ("wired_network", "outages", 2),
        ("kvm", "switched_computers", 2),
        ("kvm", "keyboard", False),
        ("kvm", "mouse", False),
        ("kvm", "video", False),
    ],
)
def test_failed_observations(complete_input, area, field, value):
    """Independent comparisons: 999 < 1000, 1 < 2, 2 > 1 and 2 < 3;
    false functional observations fail by the documented checklist contract.
    """
    complete_input["observations"][area][field] = value
    report = assess_readiness(complete_input)
    check = checks_by_id(report)[area]
    assert report["status"] == check["status"] == "FAIL"
    assert check["failed"] == [f"observations.{area}.{field}"]


def test_no_evidence_is_not_evaluated():
    report = assess_readiness({})
    assert report["status"] == "NOT_EVALUATED"
    assert all(check["status"] == "NOT_EVALUATED" for check in report["checks"])
    assert all(check["missing"] for check in report["checks"])


def test_missing_targets_cannot_pass(complete_input):
    del complete_input["requirements"]
    report = assess_readiness(complete_input)
    checks = checks_by_id(report)
    assert report["status"] == "NOT_EVALUATED"
    for area in ("shared_storage", "displays", "wired_network", "kvm"):
        assert checks[area]["status"] == "NOT_EVALUATED"
        assert all(path.startswith("requirements.") for path in checks[area]["missing"])


def test_short_network_observation_is_not_evaluated(complete_input):
    """3599 < the supplied 3600-second window gives insufficient evidence."""
    complete_input["observations"]["wired_network"]["observation_seconds"] = 3599
    report = assess_readiness(complete_input)
    check = checks_by_id(report)["wired_network"]
    assert report["status"] == check["status"] == "NOT_EVALUATED"
    assert check["insufficient"] == ["observations.wired_network.observation_seconds"]


def test_failure_takes_precedence_over_missing_or_short_evidence(complete_input):
    del complete_input["observations"]["remote_access"]["graphical_session"]
    complete_input["observations"]["remote_access"]["login"] = False
    complete_input["observations"]["wired_network"].update(
        observation_seconds=1, outages=2
    )
    report = assess_readiness(complete_input)
    checks = checks_by_id(report)
    assert report["status"] == "FAIL"
    assert checks["remote_access"]["status"] == "FAIL"
    assert checks["remote_access"]["missing"]
    assert checks["wired_network"]["status"] == "FAIL"
    assert checks["wired_network"]["insufficient"]


@pytest.mark.parametrize("document", [None, [], "input", {"unknown": {}}])
def test_invalid_document(document):
    with pytest.raises((TypeError, ValueError)):
        assess_readiness(document)


@pytest.mark.parametrize("section", ["requirements", "observations"])
@pytest.mark.parametrize("value", [None, [], {"unknown": {}}])
def test_invalid_sections(section, value):
    with pytest.raises((TypeError, ValueError)):
        assess_readiness({section: value})


@pytest.mark.parametrize("value", [None, [], {"unknown": True}])
def test_invalid_check_fields(complete_input, value):
    complete_input["observations"]["graphics"] = value
    with pytest.raises((TypeError, ValueError)):
        assess_readiness(complete_input)


@pytest.mark.parametrize("value", [True, -1, 1.5, "2", None])
def test_counts_require_nonnegative_integers(complete_input, value):
    complete_input["observations"]["displays"]["simultaneous_count"] = value
    with pytest.raises((TypeError, ValueError)):
        assess_readiness(complete_input)


@pytest.mark.parametrize("value", [0, -1, True, "2", None])
def test_targets_require_positive_integers(complete_input, value):
    complete_input["requirements"]["displays"]["minimum_count"] = value
    with pytest.raises((TypeError, ValueError)):
        assess_readiness(complete_input)


def test_zero_outage_target_and_observation_are_valid(complete_input):
    complete_input["requirements"]["wired_network"]["maximum_outages"] = 0
    complete_input["observations"]["wired_network"]["outages"] = 0
    assert assess_readiness(complete_input)["status"] == "PASS"


@pytest.mark.parametrize("value", [0, 1, "true", None])
def test_functional_results_require_booleans(complete_input, value):
    complete_input["observations"]["graphics"]["functional"] = value
    with pytest.raises((TypeError, ValueError)):
        assess_readiness(complete_input)


def run_cli(path):
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    return subprocess.run(
        [sys.executable, "-m", "assetutilities.cli.hardware_readiness", str(path)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize(
    "status,exit_code", [("PASS", 0), ("FAIL", 1), ("NOT_EVALUATED", 2)]
)
def test_cli_json_and_exit_codes(tmp_path, complete_input, status, exit_code):
    if status == "FAIL":
        complete_input["observations"]["audio"]["playback"] = False
    elif status == "NOT_EVALUATED":
        complete_input = {}
    path = tmp_path / "observations.json"
    original = json.dumps(complete_input)
    path.write_text(original, encoding="utf-8")
    result = run_cli(path)
    assert result.returncode == exit_code
    assert json.loads(result.stdout)["status"] == status
    assert result.stderr == ""
    assert path.read_text(encoding="utf-8") == original
    assert sorted(item.name for item in tmp_path.iterdir()) == [path.name]


@pytest.mark.parametrize(
    "contents",
    [
        "private-marker",
        '{"private-marker": true}',
        '{"observations": {}, "observations": {}}',
        '{"observations": {"graphics": {"functional": NaN}}}',
    ],
)
def test_cli_rejects_ambiguous_or_invalid_json_without_echo(tmp_path, contents):
    path = tmp_path / "observations.json"
    path.write_text(contents, encoding="utf-8")
    result = run_cli(path)
    assert result.returncode == 2
    assert result.stdout == ""
    assert "private-marker" not in result.stderr
    assert str(path) not in result.stderr
    assert "Traceback" not in result.stderr


def test_cli_missing_file_does_not_echo_location(tmp_path):
    path = tmp_path / "missing.json"
    result = run_cli(path)
    assert result.returncode == 2
    assert str(path) not in result.stderr
    assert "Traceback" not in result.stderr


def test_worked_example():
    """Hand oracle: capacities 1200 >= 1000, displays 2 >= 2, elapsed
    3600 >= 3600, computers 3 >= 3. Network outages 2 > 1 fail;
    absent graphical-session evidence is not evaluated. The remaining six
    areas pass. Overall FAIL takes precedence over incomplete evidence.
    """
    report = assess_readiness(json.loads(EXAMPLE.read_text(encoding="utf-8")))
    assert report["status"] == "FAIL"
    assert {
        status: sum(c["status"] == status for c in report["checks"])
        for status in ("PASS", "FAIL", "NOT_EVALUATED")
    } == {
        "PASS": 6,
        "FAIL": 1,
        "NOT_EVALUATED": 1,
    }
