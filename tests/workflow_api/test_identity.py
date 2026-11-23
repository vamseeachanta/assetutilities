# ABOUTME: TDD tests for the deterministic run-identity contract (workspace-hub#3428):
# ABOUTME: canonical serialization, domain-separated digests, and identity derivation.
"""Identity contract tests (no engine dependency).

These pin the normative rules from the on-main
``docs/architecture/algorithm-run-dataset-contract.yaml`` ``identity`` block:
canonical serialization owned here, SHA-256 digests domain-separated by id type,
each id binds exactly its declared required components (and rejects the forbidden
ones), and identity is fail-closed / re-derivable from a verified clean context.
"""

from __future__ import annotations

import inspect
from decimal import Decimal

import pytest

from assetutilities.workflow_api import identity


# ---------------------------------------------------------------------------
# shared fixtures / builders
# ---------------------------------------------------------------------------

def _avid(**overrides) -> str:
    kwargs = dict(
        algorithm_id="stress_screen",
        semantic_version="1.4.2",
        clean_git_commit="a" * 40,
        input_schema_version="in-3",
        output_schema_version="out-2",
        environment_digest="env-" + "b" * 8,
    )
    kwargs.update(overrides)
    return identity.algorithm_version_id(**kwargs)


def _input_record(**overrides) -> dict:
    rec = dict(
        role="primary",
        native_schema_version="ns-1",
        source_snapshot="snap-2026-07-01",
        transformation_id="xf-9",
        artifact_sha256="c" * 64,
        redistribution_rights="internal",
        complete_replay_location="s3://bucket/replay/1",
    )
    rec.update(overrides)
    return rec


def _derive(**overrides):
    kwargs = dict(
        algorithm_id="stress_screen",
        semantic_version="1.4.2",
        clean_git_commit="a" * 40,
        input_schema_version="in-3",
        output_schema_version="out-2",
        environment_digest="env-" + "b" * 8,
        inputs=[("primary", "irid-1"), ("aux", "irid-2")],
        execution_parameters={"tolerance": "1e-6", "mode": "fast"},
        seed=1234,
    )
    kwargs.update(overrides)
    return identity.derive_run_identity(**kwargs)


# ---------------------------------------------------------------------------
# 1. algorithm_version_id binds all required components
# ---------------------------------------------------------------------------

def test_algorithm_version_id_binds_all_components():
    base = _avid()
    changes = {
        "algorithm_id": "other_algo",
        "semantic_version": "1.4.3",
        "clean_git_commit": "d" * 40,
        "input_schema_version": "in-4",
        "output_schema_version": "out-3",
        "environment_digest": "env-" + "e" * 8,
    }
    ids = {base}
    for comp, newval in changes.items():
        variant = _avid(**{comp: newval})
        assert variant != base, f"changing {comp} must change algorithm_version_id"
        ids.add(variant)
    # every single-component change produced a distinct id
    assert len(ids) == len(changes) + 1

    # a missing/None required component is rejected (fail-closed), never hashed as absent
    with pytest.raises(identity.IdentityError):
        _avid(environment_digest=None)


# ---------------------------------------------------------------------------
# 2. run_id binds its components, excludes outputs, uses input_set_id
# ---------------------------------------------------------------------------

def test_run_id_binds_components_excludes_outputs():
    avid = _avid()
    isid = identity.input_set_id([("primary", "irid-1")])
    rid = identity.run_id(
        algorithm_version_id=avid,
        input_set_id=isid,
        execution_parameters={"mode": "fast"},
        seed=7,
    )
    # run_id has no output channel at all -> an output change cannot move it.
    rid_again = identity.run_id(
        algorithm_version_id=avid,
        input_set_id=isid,
        execution_parameters={"mode": "fast"},
        seed=7,
    )
    assert rid == rid_again

    # each real component is bound
    assert rid != identity.run_id(
        algorithm_version_id=_avid(algorithm_id="x"),
        input_set_id=isid, execution_parameters={"mode": "fast"}, seed=7)
    assert rid != identity.run_id(
        algorithm_version_id=avid,
        input_set_id=identity.input_set_id([("primary", "irid-2")]),
        execution_parameters={"mode": "fast"}, seed=7)
    assert rid != identity.run_id(
        algorithm_version_id=avid, input_set_id=isid,
        execution_parameters={"mode": "slow"}, seed=7)
    assert rid != identity.run_id(
        algorithm_version_id=avid, input_set_id=isid,
        execution_parameters={"mode": "fast"}, seed=8)


# ---------------------------------------------------------------------------
# 3. canonicalization: equivalent values -> same digest
# ---------------------------------------------------------------------------

def test_canonicalization_equivalent_values_same_digest():
    # (a) JCS: object key order + insignificant whitespace are irrelevant.
    a = {"b": 1, "a": {"y": 2, "x": 3}}
    b = {"a": {"x": 3, "y": 2}, "b": 1}
    assert identity.canonicalize(a) == identity.canonicalize(b)
    assert identity.canonical_digest("t", a) == identity.canonical_digest("t", b)

    # (b) numbers normalize via Decimal, no float round-trip.
    assert identity.canonicalize(1e3) == identity.canonicalize(1000)
    assert identity.canonicalize(1000) == identity.canonicalize(Decimal("1E3"))
    assert identity.canonicalize(5.0) == identity.canonicalize(5)
    assert identity.canonicalize(5.00) == identity.canonicalize(Decimal("5.00"))
    assert identity.canonicalize(5) == identity.canonicalize(Decimal("5.00"))

    # (c) Unicode NFC vs NFD forms collapse before hashing.
    nfc = "é"          # é  (composed)
    nfd = "é"         # e + combining acute (decomposed)
    assert nfc != nfd
    assert identity.canonicalize(nfc) == identity.canonicalize(nfd)

    # (d) a physical quantity MUST be an explicit {value, unit} pair; a bare
    # units-bearing numeric string is rejected.
    with pytest.raises(identity.IdentityError):
        identity.canonicalize("5 kg")
    with pytest.raises(identity.IdentityError):
        identity.canonicalize({"mass": "5.0m"})
    # the explicit pair is accepted
    identity.canonicalize({"mass": {"value": 5.0, "unit": "kg"}})


# ---------------------------------------------------------------------------
# 4. different inputs never collide (incl. near-collision)
# ---------------------------------------------------------------------------

def test_different_inputs_never_collide():
    assert identity.canonical_digest("t", {"v": 1.0}) != identity.canonical_digest(
        "t", {"v": 1.0000000001})
    assert identity.canonical_digest("t", [1, 2]) != identity.canonical_digest(
        "t", [2, 1])  # arrays are ordered
    assert identity.canonical_digest("t", {"a": 1}) != identity.canonical_digest(
        "t", {"a": 1, "b": None})  # explicit null is a real difference, not omitted


# ---------------------------------------------------------------------------
# 5. domain separation prevents cross-type collision
# ---------------------------------------------------------------------------

def test_domain_separation_prevents_cross_type_collision():
    components = {"role": "primary", "x": 1}
    a = identity.canonical_digest("algorithm_version_id", components)
    b = identity.canonical_digest("input_record_id", components)
    c = identity.canonical_digest("run_id", components)
    assert len({a, b, c}) == 3, "same bytes under different id types must not collide"
    # and equal type + equal bytes DO agree (determinism)
    assert a == identity.canonical_digest("algorithm_version_id", dict(components))


# ---------------------------------------------------------------------------
# 6. canonicalization_version is in every digest and pins the scheme
# ---------------------------------------------------------------------------

def test_canonicalization_version_in_digests_and_pins_scheme(monkeypatch):
    before = identity.canonical_digest("t", {"a": 1})
    assert isinstance(identity.CANONICALIZATION_VERSION, str)
    monkeypatch.setattr(identity, "CANONICALIZATION_VERSION", "identity-jcs-999")
    after = identity.canonical_digest("t", {"a": 1})
    assert before != after, "bumping the scheme version must mint new ids deterministically"


# ---------------------------------------------------------------------------
# 7. fail-closed eligibility
# ---------------------------------------------------------------------------

def _eligible(**overrides):
    kwargs = dict(
        clean_tree=True,
        commit="a" * 40,
        commit_known=True,
        input_schema_version="in-3",
        output_schema_version="out-2",
        environment_digest="env-1",
        seed=0,
        execution_parameters={},
    )
    kwargs.update(overrides)
    return identity.check_eligibility(**kwargs)


def test_dirty_or_unpinned_or_implicit_seed_fails_closed():
    # baseline is eligible
    assert _eligible() is True

    reject_cases = [
        dict(clean_tree=False),                       # dirty_source
        dict(commit_known=False),                     # unknown_revision (shallow/unknown)
        dict(commit=None),                            # unknown_revision (no commit)
        dict(input_schema_version=None),              # unpinned_schema
        dict(output_schema_version=None),             # unpinned_schema
        dict(environment_digest=None),                # missing_environment_digest
        dict(seed=None),                              # implicit_seed
        dict(execution_parameters=None),              # implicit_execution_default
    ]
    for case in reject_cases:
        with pytest.raises(identity.EligibilityError):
            _eligible(**case)

    # seed == 0 is EXPLICIT (must not be treated as implicit)
    assert _eligible(seed=0) is True


# ---------------------------------------------------------------------------
# 8. same canonical inputs -> same run_id across machines
# ---------------------------------------------------------------------------

def test_same_canonical_inputs_same_run_id_cross_machine(monkeypatch, tmp_path):
    a = _derive()
    # simulate a different machine: different cwd + different environment
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOSTNAME", "machine-b")
    monkeypatch.setenv("PWD", str(tmp_path))
    monkeypatch.setenv("USER", "someone-else")
    b = _derive()
    assert a["run_id"] == b["run_id"]
    assert a["algorithm_version_id"] == b["algorithm_version_id"]
    assert a["input_set_id"] == b["input_set_id"]


# ---------------------------------------------------------------------------
# 9. any component change changes identity
# ---------------------------------------------------------------------------

def test_any_component_change_changes_identity():
    base = _derive()["run_id"]
    assert _derive(semantic_version="9.9.9")["run_id"] != base
    assert _derive(clean_git_commit="f" * 40)["run_id"] != base
    assert _derive(environment_digest="env-other")["run_id"] != base
    assert _derive(inputs=[("primary", "irid-1"), ("aux", "irid-CHANGED")])["run_id"] != base
    assert _derive(execution_parameters={"tolerance": "1e-6", "mode": "slow"})["run_id"] != base
    assert _derive(seed=4321)["run_id"] != base


# ---------------------------------------------------------------------------
# 10. execution_parameters vs parameter_set are not double-counted
# ---------------------------------------------------------------------------

def test_execution_parameter_and_parameter_set_not_double_counted():
    # input_set_id depends ONLY on the input records, never on execution_parameters.
    isid_a = identity.input_set_id([("primary", "irid-1")])
    isid_b = identity.input_set_id([("primary", "irid-1")])
    assert isid_a == isid_b

    # A knob living on the execution side moves run_id but NOT input_set_id.
    r1 = _derive(execution_parameters={"knob": "A"})
    r2 = _derive(execution_parameters={"knob": "B"})
    assert r1["input_set_id"] == r2["input_set_id"]   # not leaking into the input side
    assert r1["run_id"] != r2["run_id"]

    # The same logical value expressed on the INPUT side (a different input record)
    # moves input_set_id (and run_id) but leaves execution_parameters untouched --
    # i.e. it is counted on exactly one side, never both.
    r3 = _derive(inputs=[("primary", "irid-knobA")], execution_parameters={})
    r4 = _derive(inputs=[("primary", "irid-knobB")], execution_parameters={})
    assert r3["input_set_id"] != r4["input_set_id"]
    assert r3["run_id"] != r4["run_id"]


# ---------------------------------------------------------------------------
# 11. run_id uses an opaque injected input_set_id (no #3430 dependency)
# ---------------------------------------------------------------------------

def test_run_id_uses_opaque_injected_input_set_digest():
    avid = _avid()
    opaque = "0" * 64  # a stand-in input_set_id we did not compute here
    rid = identity.run_id(
        algorithm_version_id=avid,
        input_set_id=opaque,
        execution_parameters={"mode": "fast"},
        seed=1,
    )
    assert isinstance(rid, str) and len(rid) == 64
    # a different opaque digest yields a different run_id, with no knowledge of
    # how the input_set_id was constructed (that is #3430's concern).
    rid2 = identity.run_id(
        algorithm_version_id=avid,
        input_set_id="1" * 64,
        execution_parameters={"mode": "fast"},
        seed=1,
    )
    assert rid != rid2


# ---------------------------------------------------------------------------
# 12. exact-rerun output mismatch fails closed without mutation
# ---------------------------------------------------------------------------

def test_exact_rerun_output_mismatch_fails_closed_no_mutation():
    assert identity.OUTPUT_EQUALITY_DEFAULT == "raw_bytes_sha256"
    prior = {"run_id": "r1", "output_equality_digest": "aa" * 32, "published": True}

    # equal digests -> accepted (no exception)
    identity.assert_output_equality(prior["output_equality_digest"], "aa" * 32)

    # mismatch -> reject WITHOUT mutating the prior record
    snapshot = dict(prior)
    with pytest.raises(identity.OutputMismatchError):
        identity.assert_output_equality(
            prior["output_equality_digest"], "bb" * 32, prior_record=prior)
    assert prior == snapshot, "reject_without_mutation: prior state must be untouched"


# ---------------------------------------------------------------------------
# 13. terminal statuses carry run_id; indeterminate mints none
# ---------------------------------------------------------------------------

def test_terminal_statuses_have_no_attempt_identity():
    rid = _derive()["run_id"]
    assert identity.mints_identity("succeeded") is True
    assert identity.mints_identity("reproducible_failure") is True
    assert identity.mints_identity("indeterminate_failure") is False

    assert identity.run_identity_for_status("succeeded", rid) == rid
    assert identity.run_identity_for_status("reproducible_failure", rid) == rid
    # non-terminal, non-identity-bearing -> mints NO identity (attempts/retries never do)
    assert identity.run_identity_for_status("indeterminate_failure", rid) is None


# ---------------------------------------------------------------------------
# 14. input_record_id forbids run-scoped and PII components
# ---------------------------------------------------------------------------

def test_input_record_id_forbids_run_scoped_and_pii_components():
    good = identity.input_record_id(_input_record())
    assert isinstance(good, str) and len(good) == 64

    forbidden_examples = [
        "run_id", "algorithm_version_id", "output_set_id", "attempt_id",
        "retry_count", "publication_state", "tenant_id", "customer_id",
        "request_id", "session_id", "user_id",
    ]
    for bad_key in forbidden_examples:
        rec = _input_record(**{bad_key: "leak"})
        with pytest.raises(identity.IdentityError):
            identity.input_record_id(rec)

    # a missing required component is likewise rejected (fail-closed)
    incomplete = _input_record()
    del incomplete["artifact_sha256"]
    with pytest.raises(identity.IdentityError):
        identity.input_record_id(incomplete)


# ---------------------------------------------------------------------------
# 15. envelope hashes are evidence, never identity inputs
# ---------------------------------------------------------------------------

def test_envelope_hashes_are_evidence_not_identity():
    # The identity-derivation entrypoint deliberately consumes NEITHER the
    # envelope input_hash NOR the best-effort code_version git_sha.
    params = set(inspect.signature(identity.derive_run_identity).parameters)
    assert "input_hash" not in params
    assert "git_sha" not in params
    for p in params:
        assert "input_hash" not in p and "git_sha" not in p and "envelope" not in p

    # Concretely: two runs whose ONLY difference is fabricated envelope evidence
    # (a different volatile input_hash / best-effort git_sha) share one run_id,
    # because that evidence is never passed into identity.
    a = _derive()
    _evidence_a = {"input_hash": "deadbeef", "git_sha": "1111111"}  # noqa: F841 -- not consumed
    b = _derive()
    _evidence_b = {"input_hash": "cafef00d", "git_sha": "2222222"}  # noqa: F841 -- not consumed
    assert a["run_id"] == b["run_id"]
    # identity is bound to the VERIFIED clean commit, not the best-effort sha
    assert a["algorithm_version_id"] == b["algorithm_version_id"]
