# ABOUTME: Unit tests for ResultEnvelope + determinism/provenance helpers (#3282).
"""Envelope + hashing tests (no engine dependency)."""

from __future__ import annotations

from assetutilities.workflow_api.envelope import (
    ResultEnvelope,
    code_version,
    compute_reproducible,
    input_hash,
    make_provenance,
    result_hash,
)


def _envelope() -> ResultEnvelope:
    return ResultEnvelope(
        workflow_id="data_exploration",
        status="ok",
        result={"kind": "files", "outputs": [{"basename": "a.csv", "sha256": "ab", "size": 3}]},
        provenance=make_provenance("deadbeef", data_as_of="2026-06-28T00:00:00Z"),
        determinism={"result_hash": "cafe", "reproducible": None},
        confidence=None,
        warnings=["w1"],
    )


def test_envelope_roundtrip():
    env = _envelope()
    restored = ResultEnvelope.from_dict(env.to_dict())
    assert restored == env
    assert restored.to_dict() == env.to_dict()


def test_input_hash_excludes_volatile_keys():
    base = {"basename": "data_exploration", "type": {"flag": True}}
    a = dict(base, Analysis={"file_name": "x", "start_time": "t1"}, default={"a": 1}, cfg_array=[1])
    b = dict(base, Analysis={"file_name": "y", "start_time": "t2"}, default={"a": 2}, cfg_array=[9])
    assert input_hash(a) == input_hash(b)


def test_input_hash_changes_on_real_input():
    a = {"basename": "data_exploration", "type": {"flag": True}}
    b = {"basename": "data_exploration", "type": {"flag": False}}
    assert input_hash(a) != input_hash(b)


def test_result_hash_files_content_sensitive():
    p1 = {"kind": "files", "outputs": [{"basename": "a.csv", "sha256": "11"},
                                       {"basename": "b.csv", "sha256": "22"}]}
    p2 = {"kind": "files", "outputs": [{"basename": "a.csv", "sha256": "11"},
                                       {"basename": "b.csv", "sha256": "22"}]}
    p3 = {"kind": "files", "outputs": [{"basename": "a.csv", "sha256": "11"},
                                       {"basename": "b.csv", "sha256": "99"}]}  # one byte changed
    assert result_hash(p1) == result_hash(p2)
    assert result_hash(p1) != result_hash(p3)


def test_result_hash_files_location_independent():
    # Same basenames + contents, reordered + with extra location metadata (size)
    # that must NOT affect the hash.
    p1 = {"kind": "files", "outputs": [{"basename": "a.csv", "sha256": "11", "size": 1},
                                       {"basename": "b.csv", "sha256": "22", "size": 2}]}
    p2 = {"kind": "files", "outputs": [{"basename": "b.csv", "sha256": "22", "size": 999},
                                       {"basename": "a.csv", "sha256": "11", "size": 888}]}
    assert result_hash(p1) == result_hash(p2)


def test_provenance_code_version_shape():
    cv = code_version("assetutilities")
    assert set(cv.keys()) == {"package_version", "git_sha"}
    prov = make_provenance("abc")
    assert set(prov["code_version"].keys()) == {"package_version", "git_sha"}
    assert prov["input_hash"] == "abc"
    assert prov["standard_revisions"] == []


def test_code_version_parameterized_by_package():
    # Unknown package degrades to package_version None (not a raise), proving the
    # parameter is honored rather than hardcoded to assetutilities.
    cv = code_version("this_package_does_not_exist_xyz")
    assert cv["package_version"] is None


def test_reproducible_not_hardcoded_default_none():
    assert compute_reproducible(lambda: "h", "h", verify=False) is None


def test_reproducible_computed_true_and_false():
    assert compute_reproducible(lambda: "same", "same", verify=True) is True
    assert compute_reproducible(lambda: "drift", "same", verify=True) is False
