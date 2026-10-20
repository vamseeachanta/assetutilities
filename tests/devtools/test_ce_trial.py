"""Decision cases derived by hand from issues #81 and #86 (2026).

The Boolean method is explicit: installation AND isolation are prerequisites;
a complete accepted loop permits full adoption, otherwise accepted advisory
skills alone permit partial adoption. Missing evidence never earns a skill.
PASS fixtures below are synthetic assessments, not observed plugin results.
"""

import copy
import json
from pathlib import Path

import pytest

from assetutilities.devtools.ce_trial import (
    ADVISORY_SKILLS,
    PIPELINE_SKILLS,
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
    ) | set(PIPELINE_SKILLS)


def test_complete_trial_keeps_all_skills():
    """Hand result: both prerequisites and every skill PASS implies adopt/full."""
    result = assess(accepted())
    assert result["verdict"] == "adopt"
    assert result["mode"] == "full"
    assert set(result["keep"]) == set(ADVISORY_SKILLS) | set(PIPELINE_SKILLS)
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


@pytest.mark.parametrize("skill", PIPELINE_SKILLS)
def test_broken_loop_retains_only_advisory_skills(skill):
    """Hand result: any failed loop member breaks the loop, preserving advisories."""
    record = accepted()
    record["skills"][skill]["status"] = "FAIL"
    result = assess(record)
    assert result["verdict"] == "adopt-partial"
    assert set(result["keep"]) == set(ADVISORY_SKILLS) - {skill}
    assert skill in result["failed"]


def test_pipeline_success_without_advisory_evaluation_is_not_full_adoption():
    """Hand result: #84 findings are required by #86; #85 alone cannot replace them."""
    record = snapshot()
    passed = accepted()
    record["prerequisites"] = passed["prerequisites"]
    for skill in PIPELINE_SKILLS:
        record["skills"][skill] = passed["skills"][skill]
    result = assess(record)
    assert result["verdict"] == "adopt-partial"
    assert result["keep"] == ["ce-code-review"]


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
    assert main([str(EXAMPLE)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result == assess(snapshot())
    assert EXAMPLE.read_bytes() == before


@pytest.mark.parametrize("content", ["{", "[]", '{"prerequisites": {}, "skills": {}}'])
def test_cli_rejects_invalid_input_without_echoing_it(tmp_path, capsys, content):
    path = tmp_path / "evidence.json"
    path.write_text(content, encoding="utf-8")
    assert main([str(path)]) == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert (
        output.err == "Invalid trial evidence. Supply the documented evidence format.\n"
    )


def test_cli_missing_input_is_a_fixed_error(tmp_path, capsys):
    assert main([str(tmp_path / "missing.json")]) == 2
    assert "missing.json" not in capsys.readouterr().err


def test_cli_rejects_conflicting_duplicate_status(tmp_path, capsys):
    """A PASS following FAIL cannot silently discard the failed observation."""
    content = json.dumps(accepted()).replace(
        '"status": "PASS"', '"status": "FAIL", "status": "PASS"'
    )
    path = tmp_path / "evidence.json"
    path.write_text(content, encoding="utf-8")
    assert main([str(path)]) == 2
    assert capsys.readouterr().out == ""


def test_cli_rejects_non_utf8_input(tmp_path, capsys):
    path = tmp_path / "evidence.json"
    path.write_bytes(bytes([255]))
    assert main([str(path)]) == 2
    assert capsys.readouterr().out == ""


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
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", document.read_text()):
            assert (document.parent / target).is_file(), target


def test_local_setup_config_is_ignored_but_public_example_is_not():
    import subprocess

    result = subprocess.run(
        [
            "git",
            "check-ignore",
            "--stdin",
        ],
        input=".compound-engineering/sample.local.yaml\nexamples/devtools/ce-trial-evidence.json\n",
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.splitlines() == [".compound-engineering/sample.local.yaml"]
