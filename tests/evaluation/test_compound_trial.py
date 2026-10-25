"""Behavioral tests for the trial evidence CLI; all observations are synthetic."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/evaluation/compound_trial.py"


def run_trial(tmp_path, record):
    """Execute the public CLI without repository bindings inherited by children."""
    path = tmp_path / "trial.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"}
    }
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(path), "--root", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def deferred_record():
    """Criteria are transcribed from the success criteria of the trial epic."""
    return {
        "schema_version": 1,  # Local record format, not a plugin version.
        "plugin": {"version": "unresolved", "revision": None},
        "criteria": {
            name: {
                "status": "NOT_EVALUATED",
                "reason": "Synthetic example: live observations have not been collected.",
                "evidence": [],
            }
            for name in (
                "install_clean",
                "advisory_value",
                "plan_work",
                "compound_capture",
                "rollout_recommendation",
            )
        },
    }


def test_missing_observations_defer_rollout(tmp_path):
    """Hand count: no PASS, no FAIL, five NOT_EVALUATED from the epic checklist."""
    result = run_trial(tmp_path, deferred_record())
    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report["disposition"] == "defer"
    assert report["counts"] == {"PASS": 0, "FAIL": 0, "NOT_EVALUATED": 5}
    assert report["ready_for_maintainer_review"] is False


def observed_record(tmp_path):
    """Create synthetic observations; hashes are computed independently by hashlib."""
    artifact = tmp_path / "observation.txt"
    artifact.write_text(
        "Synthetic observation, not a live plugin trial.\n", encoding="utf-8"
    )
    record = deferred_record()
    record["plugin"] = {"version": "synthetic", "revision": "a" * 40}
    for criterion in record["criteria"].values():
        criterion.update(
            status="PASS",
            reason="Synthetic observation for CLI testing only.",
            evidence=[
                {
                    "path": "observation.txt",
                    "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                }
            ],
        )
    return record


def test_complete_record_is_ready_for_review_not_adoption(tmp_path):
    """Hand count: five PASS, no FAIL, no NOT_EVALUATED; adoption is not decided."""
    result = run_trial(tmp_path, observed_record(tmp_path))
    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report["counts"] == {"PASS": 5, "FAIL": 0, "NOT_EVALUATED": 0}
    assert report["ready_for_maintainer_review"] is True
    assert report["disposition"] == "ready_for_review"


def test_one_failure_prevents_rollout_even_with_pending_checks(tmp_path):
    """Hand count: three PASS, one FAIL, one NOT_EVALUATED; FAIL governs."""
    record = observed_record(tmp_path)
    record["criteria"]["advisory_value"]["status"] = "FAIL"
    record["criteria"]["plan_work"] = deferred_record()["criteria"]["plan_work"]
    result = run_trial(tmp_path, record)
    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report["counts"] == {"PASS": 3, "FAIL": 1, "NOT_EVALUATED": 1}
    assert report["disposition"] == "do_not_roll_out"


@pytest.mark.parametrize("change", ["tamper", "missing", "unrecorded"])
def test_observations_need_matching_artifact_bytes(tmp_path, change):
    """An observed criterion without its original matching evidence is invalid."""
    record = observed_record(tmp_path)
    if change == "tamper":
        (tmp_path / "observation.txt").write_text("Changed bytes", encoding="utf-8")
    elif change == "missing":
        record["criteria"]["install_clean"]["evidence"][0]["path"] = "absent.txt"
    else:
        record["criteria"]["install_clean"]["evidence"] = []
    result = run_trial(tmp_path, record)
    assert result.returncode == 2
    assert "invalid trial record" in result.stderr
    assert result.stdout == ""


@pytest.mark.parametrize(
    "change",
    [
        "schema_version",
        "boolean_version",
        "extra_top_key",
        "missing_criterion",
        "extra_criterion",
        "unknown_status",
        "empty_reason",
        "string_evidence",
        "missing_revision",
        "short_revision",
        "empty_plugin_version",
        "extra_plugin_key",
        "bad_digest",
        "extra_evidence_key",
        "duplicate_evidence",
        "null_criterion",
    ],
)
def test_malformed_records_are_rejected(tmp_path, change):
    """Malformed data cannot establish the epic's complete success criteria."""
    record = observed_record(tmp_path)
    criterion = record["criteria"]["install_clean"]
    if change == "schema_version":
        record["schema_version"] = 2
    elif change == "boolean_version":
        record["schema_version"] = True
    elif change == "extra_top_key":
        record["adopt"] = True
    elif change == "missing_criterion":
        del record["criteria"]["rollout_recommendation"]
    elif change == "extra_criterion":
        record["criteria"]["invented"] = criterion.copy()
    elif change == "unknown_status":
        criterion["status"] = "SKIPPED"
    elif change == "empty_reason":
        criterion["reason"] = "  "
    elif change == "string_evidence":
        criterion["evidence"] = "observation.txt"
    elif change == "missing_revision":
        record["plugin"]["revision"] = None
    elif change == "short_revision":
        record["plugin"]["revision"] = "abc"
    elif change == "empty_plugin_version":
        record["plugin"]["version"] = " "
    elif change == "extra_plugin_key":
        record["plugin"]["installed"] = True
    elif change == "bad_digest":
        criterion["evidence"][0]["sha256"] = "bad"
    elif change == "extra_evidence_key":
        criterion["evidence"][0]["trusted"] = True
    elif change == "duplicate_evidence":
        criterion["evidence"] *= 2
    else:
        record["criteria"]["install_clean"] = None
    result = run_trial(tmp_path, record)
    assert result.returncode == 2
    assert "invalid trial record" in result.stderr
    assert "Traceback" not in result.stderr
    assert result.stdout == ""


@pytest.mark.parametrize(
    "kind", ["absolute", "parent", "symlink", "drive", "backslash"]
)
def test_evidence_paths_stay_within_root(tmp_path, kind):
    """Even correctly hashed evidence cannot escape the selected evidence root."""
    record = observed_record(tmp_path)
    item = record["criteria"]["install_clean"]["evidence"][0]
    external = tmp_path.parent / "outside.txt"
    external.write_bytes((tmp_path / "observation.txt").read_bytes())
    if kind == "absolute":
        item["path"] = str(tmp_path / "observation.txt")
    elif kind == "parent":
        item["path"] = "../outside.txt"
    elif kind == "symlink":
        (tmp_path / "link.txt").symlink_to(external)
        item["path"] = "link.txt"
    elif kind == "drive":
        item["path"] = "C:observation.txt"
    else:
        item["path"] = "folder\\observation.txt"
    result = run_trial(tmp_path, record)
    assert result.returncode == 2
    assert "invalid trial record" in result.stderr


@pytest.mark.parametrize(
    "raw",
    ["[]", '{"schema_version":1,"schema_version":1}', '{"schema_version":NaN}', "{"],
)
def test_noncanonical_json_is_rejected(tmp_path, raw):
    """Ambiguous or incomplete input yields a diagnostic rather than a traceback."""
    path = tmp_path / "raw.json"
    path.write_text(raw, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(path), "--root", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "invalid trial record" in result.stderr
    assert "Traceback" not in result.stderr


def test_shipped_example_has_no_observed_plugin_results(tmp_path):
    """The worked example must report five pending criteria, never plugin success."""
    example = SCRIPT.parents[2] / "examples/compound-engineering/deferred-trial.json"
    record = json.loads(example.read_text(encoding="utf-8"))
    result = run_trial(tmp_path, record)
    assert result.returncode == 1
    assert json.loads(result.stdout)["counts"] == {
        "PASS": 0,
        "FAIL": 0,
        "NOT_EVALUATED": 5,
    }


def test_local_plugin_config_is_ignored_without_ignoring_evidence():
    """The setup issue requires local config exclusion, not exclusion of trial docs."""
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"}
    }
    result = subprocess.run(
        ["git", "check-ignore", "--no-index", "--stdin"],
        input=(
            ".compound-engineering/config.local.yaml\n"
            "examples/compound-engineering/deferred-trial.json\n"
        ),
        cwd=SCRIPT.parents[2],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout.splitlines() == [".compound-engineering/config.local.yaml"]


def test_symlink_cycle_is_an_invalid_record_without_path_disclosure(tmp_path):
    """A filesystem resolution failure must not become an unhandled exception."""
    record = observed_record(tmp_path)
    (tmp_path / "cycle.txt").symlink_to("cycle.txt")
    record["criteria"]["install_clean"]["evidence"][0]["path"] = "cycle.txt"
    result = run_trial(tmp_path, record)
    assert result.returncode == 2
    assert "invalid trial record" in result.stderr
    assert "Traceback" not in result.stderr
    assert str(tmp_path) not in result.stderr


def test_validation_preserves_input_and_evidence_bytes(tmp_path):
    """Re-reading evidence must not refresh a hash or modify the observation."""
    record = observed_record(tmp_path)
    run_trial(tmp_path, record)
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}
    result = run_trial(tmp_path, record)
    assert result.returncode == 0
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir()} == before
