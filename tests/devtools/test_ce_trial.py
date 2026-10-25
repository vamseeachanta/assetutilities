"""Decision cases derived by hand from issues #81 and #86 (2026).

The Boolean method is explicit: installation AND isolation are prerequisites;
a complete accepted loop permits full adoption, otherwise accepted advisory
skills alone permit partial adoption. Missing evidence never earns a skill.
PASS fixtures below are synthetic assessments, not observed plugin results.
"""

import copy
import json
import os
import sys
from pathlib import Path

import pytest

from assetutilities.devtools.ce_trial import (
    ADVISORY_SKILLS,
    PIPELINE_ASSESSMENTS,
    assess,
    main,
)


ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples/devtools/ce-trial-evidence.json"


def snapshot():
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def accepted():
    record = snapshot()
    for item in [*record["prerequisites"].values(), *record["skills"].values()]:
        item.update(
            status="PASS", evidence=["synthetic reviewed result"], reason="accepted"
        )
    return record


def test_missing_trial_results_do_not_authorize_rollout():
    """Hand result: unknown installation AND isolation is false; keep is empty."""
    result = assess(snapshot())
    assert result["verdict"] == "drop"
    assert result["mode"] == "none"
    assert result["keep"] == []
    assert set(result["not_evaluated"]) == {"install", "worktree"} | set(
        ADVISORY_SKILLS
    ) | set(PIPELINE_ASSESSMENTS)


def test_complete_trial_keeps_all_skills():
    """Hand result: both prerequisites and every skill PASS implies adopt/full."""
    result = assess(accepted())
    assert result["verdict"] == "adopt"
    assert result["mode"] == "full"
    assert result["keep"] == [
        "ce-code-review",
        "ce-compound",
        "ce-debug",
        "ce-doc-review",
        "ce-plan",
        "ce-simplify-code",
        "ce-work",
    ]
    assert result["not_evaluated"] == []


@pytest.mark.parametrize("skill", ADVISORY_SKILLS)
def test_one_advisory_success_permits_only_partial_adoption(skill):
    """Hand result: prerequisites true, one advisory PASS, loop unknown => partial."""
    record = snapshot()
    passed = accepted()
    record["prerequisites"] = passed["prerequisites"]
    record["skills"][skill] = passed["skills"][skill]
    result = assess(record)
    assert result["verdict"] == "adopt-partial"
    assert result["mode"] == "advisory"
    assert result["keep"] == [skill]


@pytest.mark.parametrize("prerequisite", ["install", "worktree"])
@pytest.mark.parametrize("status", ["FAIL", "NOT_EVALUATED"])
def test_prerequisite_blocks_even_successful_skills(prerequisite, status):
    """Hand result: a non-PASS operand makes the prerequisite conjunction false."""
    record = accepted()
    record["prerequisites"][prerequisite]["status"] = status
    result = assess(record)
    assert result["verdict"] == "drop"
    assert result["keep"] == []


@pytest.mark.parametrize("skill", PIPELINE_ASSESSMENTS)
def test_broken_loop_retains_only_advisory_skills(skill):
    """Hand result: any failed loop member breaks the loop, preserving advisories."""
    record = accepted()
    record["skills"][skill]["status"] = "FAIL"
    result = assess(record)
    assert result["verdict"] == "adopt-partial"
    assert set(result["keep"]) == set(ADVISORY_SKILLS)
    assert skill in result["failed"]


def test_pipeline_success_without_advisory_evaluation_is_not_full_adoption():
    """Hand result: #84 findings are required by #86; #85 alone cannot replace them."""
    record = snapshot()
    passed = accepted()
    record["prerequisites"] = passed["prerequisites"]
    for skill in PIPELINE_ASSESSMENTS:
        record["skills"][skill] = passed["skills"][skill]
    result = assess(record)
    assert result["verdict"] == "drop"
    assert result["mode"] == "none"
    assert result["keep"] == []


@pytest.mark.parametrize("status", ["FAIL", "NOT_EVALUATED"])
def test_no_passing_advisory_skill_blocks_partial_adoption(status):
    """Hand result: P true, A empty, T false gives drop/none despite a PASS loop."""
    record = accepted()
    record["skills"]["ce-code-review-loop"] = copy.deepcopy(
        record["skills"]["ce-code-review"]
    )
    for skill in ADVISORY_SKILLS:
        record["skills"][skill]["status"] = status
    result = assess(record)
    assert result["verdict"] == "drop"
    assert result["mode"] == "none"
    assert result["keep"] == []


@pytest.mark.parametrize(
    ("advisory_status", "loop_status"),
    [
        ("PASS", "FAIL"),
        ("PASS", "NOT_EVALUATED"),
        ("FAIL", "PASS"),
        ("NOT_EVALUATED", "PASS"),
    ],
)
def test_review_assessments_are_independent(advisory_status, loop_status):
    """Hand result: mixed review outcomes break T; only #84 PASS earns review."""
    record = accepted()
    record["skills"]["ce-code-review-loop"] = copy.deepcopy(
        record["skills"]["ce-code-review"]
    )
    record["skills"]["ce-code-review"]["status"] = advisory_status
    record["skills"]["ce-code-review-loop"]["status"] = loop_status
    result = assess(record)
    expected = ["ce-debug", "ce-doc-review", "ce-simplify-code"]
    if advisory_status == "PASS":
        expected.append("ce-code-review")
    assert result["verdict"] == "adopt-partial"
    assert result["mode"] == "advisory"
    assert result["keep"] == sorted(expected)
    for skill, status in [
        ("ce-code-review", advisory_status),
        ("ce-code-review-loop", loop_status),
    ]:
        assert (skill in result["failed"]) == (status == "FAIL")
        assert (skill in result["not_evaluated"]) == (status == "NOT_EVALUATED")


def test_shared_review_record_is_insufficient_evidence():
    record = accepted()
    record["skills"].pop("ce-code-review-loop", None)
    with pytest.raises(ValueError):
        assess(record)


@pytest.mark.parametrize("bad_status", ["pass", "KEEP", True, None])
def test_invalid_status_rejected(bad_status):
    record = accepted()
    record["skills"]["ce-plan"]["status"] = bad_status
    with pytest.raises(ValueError):
        assess(record)


@pytest.mark.parametrize("status", ["PASS", "FAIL"])
@pytest.mark.parametrize("evidence", [[], [""], ["  "], "issue result", [True]])
def test_observed_status_requires_substantive_evidence(status, evidence):
    record = accepted()
    record["skills"]["ce-plan"].update(status=status, evidence=evidence)
    with pytest.raises(ValueError):
        assess(record)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_skill",
        "unknown_skill",
        "missing_prerequisite",
        "unknown_prerequisite",
        "blank_reason",
        "not_object",
        "unknown_field",
    ],
)
def test_malformed_records_rejected(mutation):
    record = accepted()
    if mutation == "missing_skill":
        del record["skills"]["ce-work"]
    elif mutation == "unknown_skill":
        record["skills"]["unreviewed-skill"] = record["skills"]["ce-work"]
    elif mutation == "missing_prerequisite":
        del record["prerequisites"]["install"]
    elif mutation == "unknown_prerequisite":
        record["prerequisites"]["other"] = record["prerequisites"]["install"]
    elif mutation == "blank_reason":
        record["skills"]["ce-work"]["reason"] = " "
    elif mutation == "not_object":
        record = []
    else:
        record["skills"]["ce-work"]["unrecognized"] = "ignored?"
    with pytest.raises(ValueError):
        assess(record)


def test_assessment_does_not_modify_input():
    record = accepted()
    original = copy.deepcopy(record)
    assess(record)
    assert record == original


def test_example_cli_is_read_only(capsys):
    before = EXAMPLE.read_bytes()
    assert main([EXAMPLE.as_posix()]) == 0
    output = capsys.readouterr()
    assert output.out == json.dumps(assess(snapshot()), indent=2, sort_keys=True) + "\n"
    assert output.err == ""
    assert EXAMPLE.read_bytes() == before


@pytest.mark.parametrize("content", ["{", "[]", '{"prerequisites": {}, "skills": {}}'])
def test_cli_rejects_invalid_input_without_echoing_it(tmp_path, capsys, content):
    path = tmp_path / "evidence.json"
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(content)
    assert main([path.as_posix()]) == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert (
        output.err == "Invalid trial evidence. Supply the documented evidence format.\n"
    )


def test_cli_missing_input_is_a_fixed_error(tmp_path, capsys):
    assert main([(tmp_path / "missing.json").as_posix()]) == 2
    assert "missing.json" not in capsys.readouterr().err


def test_cli_rejects_conflicting_duplicate_status(tmp_path, capsys):
    """A PASS following FAIL cannot silently discard the failed observation."""
    content = json.dumps(accepted()).replace(
        '"status": "PASS"', '"status": "FAIL", "status": "PASS"'
    )
    path = tmp_path / "evidence.json"
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(content)
    assert main([path.as_posix()]) == 2
    assert capsys.readouterr().out == ""


def test_cli_rejects_non_utf8_input(tmp_path, capsys):
    path = tmp_path / "evidence.json"
    path.write_bytes(bytes([255]))
    assert main([path.as_posix()]) == 2
    assert capsys.readouterr().out == ""


def test_cli_accepts_utf8_bom_without_modifying_evidence(tmp_path, capsys):
    path = tmp_path / "evidence.json"
    content = b"\xef\xbb\xbf" + json.dumps(accepted()).encode("utf-8")
    path.write_bytes(content)
    assert main([path.as_posix()]) == 0
    assert json.loads(capsys.readouterr().out) == assess(accepted())
    assert path.read_bytes() == content


def test_cli_rejects_deeply_nested_json_without_echoing_input(tmp_path, capsys):
    depth = sys.getrecursionlimit() + 100
    path = tmp_path / "evidence.json"
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write("[" * depth + "0" + "]" * depth)
    assert main([path.as_posix()]) == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == (
        "Invalid trial evidence. Supply the documented evidence format.\n"
    )


def test_documented_worked_answer_matches_assessment():
    """Compare the published hand-derived answer with the executable example."""
    import re

    document = ROOT / "docs/modules/agent-os/ce-trial-decision.md"
    content = document.read_text(encoding="utf-8")
    answer = re.search(r"```json\n(.*?)\n```", content, re.DOTALL)
    assert answer is not None
    assert json.loads(answer.group(1)) == assess(snapshot())


def test_adoption_documentation_links_resolve():
    import re

    for relative in [
        "docs/modules/agent-os/ce-trial-decision.md",
        "docs/modules/agent-os/ce-adoption-note.md",
    ]:
        document = ROOT / relative
        for target in re.findall(
            r"\[[^\]]+\]\(([^)]+)\)", document.read_text(encoding="utf-8")
        ):
            assert (document.parent / target).is_file(), target


@pytest.mark.parametrize("stdin_newline", ["\n", "\r\n"])
@pytest.mark.parametrize(
    "binding", [None, "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE"]
)
def test_local_setup_config_is_ignored_but_public_example_is_not(
    monkeypatch, tmp_path, stdin_newline, binding
):
    import subprocess

    if binding:
        monkeypatch.setenv(binding, (tmp_path / "unrelated-repository").as_posix())
    original_run = subprocess.run

    def run_with_platform_newline(*args, **kwargs):
        if kwargs.get("text") and "input" in kwargs:
            kwargs["input"] = kwargs["input"].replace("\n", stdin_newline)
        return original_run(*args, **kwargs)

    monkeypatch.setattr(subprocess, "run", run_with_platform_newline)
    env = os.environ.copy()
    for variable in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE"):
        env.pop(variable, None)
    result = subprocess.run(
        [
            "git",
            "check-ignore",
            ".compound-engineering/sample.local.yaml",
            "examples/devtools/ce-trial-evidence.json",
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout.splitlines() == [".compound-engineering/sample.local.yaml"]


def test_devtools_registry_routes_to_the_reviewed_tests():
    import yaml

    registry = yaml.safe_load(
        (ROOT / "docs/registry/module-routing.yaml").read_text(encoding="utf-8")
    )
    devtools = next(
        module for module in registry["modules"] if module["name"] == "devtools"
    )
    assert devtools["tests_path"] == "tests/devtools/"
    assert devtools["submodules"]["ce_trial"]["tests_path"] == (
        "tests/devtools/test_ce_trial.py"
    )
