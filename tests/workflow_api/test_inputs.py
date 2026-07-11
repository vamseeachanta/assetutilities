# ABOUTME: TDD tests for the replayable public-input + source-snapshot contract
# ABOUTME: (workspace-hub#3430): six closed input kinds, fail-closed admission, snapshot identity.
"""Replayable-input contract tests (no engine dependency).

These pin the normative rules from the on-main
``docs/architecture/algorithm-run-dataset-contract.yaml`` ``records.input`` +
``public_input_policy`` blocks: exactly six closed input kinds, a fail-closed
admission layer that rejects every contract ``rejection_reason``, a snapshot
identity whose identity-bearing subset excludes fetch-volatile fields, and
replay durability (bytes MATERIALIZED, locator is provenance only). Identity is
minted through :mod:`identity` (``input_record_id`` / ``input_set_id``) and never
re-derived here.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from assetutilities.workflow_api import identity, inputs


# ---------------------------------------------------------------------------
# builders
# ---------------------------------------------------------------------------

def _dataset(**overrides) -> dict:
    """A fully-admissible dataset_snapshot input (materialized + pinned + public)."""
    kwargs = dict(
        kind="dataset_snapshot",
        role="wells",
        schema_version="wed-1",
        source_authority="EIA",
        public_locator={"uri": "https://eia.gov/ds/wells", "version": "v2026-06"},
        data_as_of="2026-06-01",
        retrieval_time="2026-07-11T00:00:00Z",
        selection={"basin": "permian"},
        snapshot_identity="d" * 64,
        content_digest="a" * 64,  # materialized HF object (via #3429)
        redistribution_rights="public",
        redistribution_evidence={"license": "CC-BY-4.0", "checked_at": "2026-07-11"},
        replay_location="content_addressed_dataset_object",
    )
    kwargs.update(overrides)
    return inputs.make_input(**kwargs)


def _artifact_ref(**overrides) -> dict:
    kwargs = dict(
        kind="artifact_reference",
        role="grid",
        schema_version="grid-2",
        content_digest="b" * 64,
        redistribution_rights="public",
        replay_location="content_addressed_dataset_object",
    )
    kwargs.update(overrides)
    return inputs.make_input(**kwargs)


def _config(**overrides) -> dict:
    kwargs = dict(
        kind="configuration_document",
        role="run_config",
        schema_version="cfg-1",
        canonical_repr={"a": 1, "b": 5.0, "nested": {"x": 1, "y": 2}},
        redistribution_rights="owned",
        replay_location="content_addressed_dataset_object",
    )
    kwargs.update(overrides)
    return inputs.make_input(**kwargs)


# ---------------------------------------------------------------------------
# 1. six closed input kinds (api -> dataset_snapshot; unknown rejected)
# ---------------------------------------------------------------------------

def test_six_input_kinds_closed_enum():
    assert inputs.INPUT_KINDS == frozenset({
        "parameter_set",
        "configuration_document",
        "dataset_snapshot",
        "public_external_resource",
        "upstream_run_reference",
        "artifact_reference",
    })
    # each of the six classifies to itself
    for kind in inputs.INPUT_KINDS:
        assert inputs.classify_kind(kind) == kind
    # API-backed inputs are classified as dataset_snapshot (no separate `api` kind)
    assert inputs.classify_kind("api") == "dataset_snapshot"
    assert "api" not in inputs.INPUT_KINDS
    # an unknown kind is rejected fail-closed
    with pytest.raises(inputs.InputError):
        inputs.classify_kind("database")
    with pytest.raises(inputs.InputError):
        inputs.make_input(kind="database", role="x", schema_version="s-1")


# ---------------------------------------------------------------------------
# 2. re-fetching the SAME snapshot yields the SAME input-set identity
# ---------------------------------------------------------------------------

def test_refetch_same_snapshot_yields_same_input_set_id():
    a = _dataset(
        retrieval_time="2026-07-11T00:00:00Z",
        redistribution_evidence={"license": "CC-BY-4.0", "checked_at": "2026-07-11"},
    )
    # SAME snapshot re-fetched later: different retrieval_time AND different
    # (volatile) redistribution_evidence -- neither is identity-bearing.
    b = _dataset(
        retrieval_time="2026-08-02T09:15:00Z",
        redistribution_evidence={"license": "CC-BY-4.0", "checked_at": "2026-08-02",
                                 "proof_url": "https://eia.gov/license"},
    )
    assert inputs.input_record_id(a) == inputs.input_record_id(b)
    assert inputs.canonical_input_set_digest([a]) == inputs.canonical_input_set_digest([b])

    # a genuine snapshot change (data_as_of / selection / snapshot_identity) DOES move it
    assert inputs.input_record_id(_dataset(data_as_of="2026-05-01")) != inputs.input_record_id(a)
    assert inputs.input_record_id(_dataset(selection={"basin": "eagleford"})) != inputs.input_record_id(a)
    assert inputs.input_record_id(_dataset(snapshot_identity="e" * 64)) != inputs.input_record_id(a)


# ---------------------------------------------------------------------------
# 3. canonically-equivalent configs -> identical identity
# ---------------------------------------------------------------------------

def test_canonically_equivalent_configs_same_identity():
    c1 = _config(canonical_repr={"a": 1, "b": 5.0, "nested": {"x": 1, "y": 2}})
    # key order differs, whitespace irrelevant, numbers equivalent (5.00 == 5.0)
    c2 = _config(canonical_repr={"b": Decimal("5.00"), "nested": {"y": 2, "x": 1}, "a": 1})
    assert inputs.input_record_id(c1) == inputs.input_record_id(c2)
    assert inputs.canonical_input_set_digest([c1]) == inputs.canonical_input_set_digest([c2])
    # a real content change moves identity
    assert inputs.input_record_id(_config(canonical_repr={"a": 2})) != inputs.input_record_id(c1)


# ---------------------------------------------------------------------------
# 4. ambiguous OR absent license fails admission
# ---------------------------------------------------------------------------

def test_ambiguous_or_unknown_license_fails_admission():
    for rights in ("ambiguous", "unknown", None):
        rec = _dataset(redistribution_rights=rights)
        assert inputs.admission_reason(rec) == "ambiguous_license"
        with pytest.raises(inputs.AdmissionError) as ei:
            inputs.admit(rec)
        assert ei.value.reason == "ambiguous_license"
        with pytest.raises(inputs.AdmissionError):
            inputs.input_record_id(rec)


# ---------------------------------------------------------------------------
# 5. admission rejects EVERY contract rejection_reason
# ---------------------------------------------------------------------------

def test_admission_rejects_all_contract_rejection_reasons():
    cases = {
        "restricted": _dataset(redistribution_rights="restricted"),
        "private": _dataset(residency="private"),
        "path_leaking": _dataset(public_locator={"uri": "/mnt/local/data.csv", "version": "v1"}),
        "schema_invalid": _dataset(schema_version=None),
        # pinned + hashed (snapshot_identity) but NOT materialized -> locator/pointer only
        "pointer_only": _dataset(content_digest=None, canonical_repr=None),
        # materialized but no snapshot pin (missing snapshot_identity)
        "mutable_unpinned": _dataset(snapshot_identity=None),
        # a reference input carrying no content hash at all
        "unhashed": _artifact_ref(content_digest=None),
        # valid+hashed+materialized reference but no complete_replay_location
        "incomplete": _artifact_ref(replay_location=None),
    }
    for expected, rec in cases.items():
        assert inputs.admission_reason(rec) == expected, expected
        with pytest.raises(inputs.AdmissionError) as ei:
            inputs.admit(rec)
        assert ei.value.reason == expected, expected
    # every reason exercised is a declared contract rejection reason
    assert set(cases) | {"ambiguous_license"} <= inputs.REJECTION_REASONS


# ---------------------------------------------------------------------------
# 6. absolute local paths forbidden (path_leaking)
# ---------------------------------------------------------------------------

def test_absolute_local_path_forbidden():
    for leak in ("/mnt/local/data.csv", "~/secret/data", "file:///etc/passwd",
                 "C:\\\\data\\\\x.csv"):
        rec = _dataset(public_locator={"uri": leak, "version": "v1"})
        assert inputs.admission_reason(rec) == "path_leaking"
    # a path leaking through an embedded config value is also caught
    bad_cfg = _config(canonical_repr={"input_path": "/home/vamsee/data.csv"})
    assert inputs.admission_reason(bad_cfg) == "path_leaking"
    # a proper remote URL is NOT a path leak
    assert inputs.admission_reason(_dataset()) is None


# ---------------------------------------------------------------------------
# 7. data_as_of == retrieval_time (utc_now) WITHOUT a snapshot identity fails
# ---------------------------------------------------------------------------

def test_data_as_of_run_timestamp_without_snapshot_identity_fails():
    now = "2026-07-11T12:00:00Z"
    # worldenergydata utc_now pattern: data_as_of stamped as the run/fetch time
    volatile = _dataset(data_as_of=now, retrieval_time=now, snapshot_identity=None)
    # the RULE is the missing snapshot identity (mutable_unpinned), not the
    # timestamp equality which is only the SYMPTOM.
    assert inputs.admission_reason(volatile) == "mutable_unpinned"
    with pytest.raises(inputs.AdmissionError):
        inputs.admit(volatile)
    # pin it with a real byte-snapshot identity (timestamps still equal) -> admitted
    pinned = _dataset(data_as_of=now, retrieval_time=now, snapshot_identity="f" * 64)
    assert inputs.admission_reason(pinned) is None
    inputs.admit(pinned)


# ---------------------------------------------------------------------------
# 8. schema-invalid input fails closed
# ---------------------------------------------------------------------------

def test_schema_invalid_input_fails_closed():
    for bad in (None, "", 3):
        rec = _dataset(schema_version=bad)
        assert inputs.admission_reason(rec) == "schema_invalid"
        with pytest.raises(inputs.AdmissionError):
            inputs.input_record_id(rec)


# ---------------------------------------------------------------------------
# 9. replay-critical bytes MUST be materialized (locator is provenance only)
# ---------------------------------------------------------------------------

def test_replay_bytes_must_be_materialized():
    # locator-only: a stable public URI with an immutable snapshot digest, but the
    # bytes are NOT materialized (no content-addressed HF object, no embedded repr).
    locator_only = _dataset(
        content_digest=None, canonical_repr=None,
        replay_location="stable_public_uri_with_immutable_digest",
    )
    assert inputs.admission_reason(locator_only) == "pointer_only"

    # materialized as a content-addressed HF object -> admitted
    materialized_obj = _dataset(content_digest="a" * 64)
    assert inputs.admission_reason(materialized_obj) is None

    # materialized by embedding the canonical representation -> admitted
    embedded = _dataset(
        content_digest=None,
        canonical_repr={"rows": [{"well": "A"}, {"well": "B"}]},
    )
    assert inputs.admission_reason(embedded) is None


# ---------------------------------------------------------------------------
# 10. a parameter cannot be counted on BOTH input-set and execution-parameter sides
# ---------------------------------------------------------------------------

def test_parameter_not_double_counted_across_contracts():
    params = inputs.make_input(
        kind="parameter_set",
        role="tuning",
        schema_version="p-1",
        canonical_repr={"tolerance": "1e-6", "max_iter": 100},
        redistribution_rights="owned",
        replay_location="content_addressed_dataset_object",
    )
    # disjoint sides are fine (execution_parameters are run-control knobs, #3428)
    inputs.check_no_parameter_double_count([params], {"mode": "fast", "seed_source": "explicit"})
    # the SAME key on both sides is rejected -- it belongs to exactly one contract
    with pytest.raises(inputs.InputError):
        inputs.check_no_parameter_double_count([params], {"tolerance": "1e-9"})


# ---------------------------------------------------------------------------
# 11. record + set identity are minted THROUGH the identity module
# ---------------------------------------------------------------------------

def test_input_record_and_set_reuse_identity_module():
    rec = _dataset()
    subset = inputs.snapshot_identity_subset(rec)
    # identity-bearing subset is EXACTLY the five snapshot fields (fetch-volatile
    # retrieval_time + redistribution_evidence excluded)
    assert set(subset) == {
        "source_authority", "public_locator", "data_as_of", "selection", "snapshot_identity",
    }
    expected_components = {
        "role": "wells",
        "native_schema_version": "wed-1",
        "source_snapshot": identity.canonical_digest("input_source_snapshot", subset),
        "transformation_id": "identity",
        "artifact_sha256": "a" * 64,
        "redistribution_rights": "public",
        "complete_replay_location": "content_addressed_dataset_object",
    }
    assert inputs.input_record_id(rec) == identity.input_record_id(expected_components)

    # the set digest is the identity module's input_set_id over (role, record_id) pairs
    rec2 = _artifact_ref(role="grid")
    pairs = [(rec["role"], inputs.input_record_id(rec)),
             (rec2["role"], inputs.input_record_id(rec2))]
    assert inputs.canonical_input_set_digest([rec, rec2]) == identity.input_set_id(pairs)
    # order-independent (identity.input_set_id sorts)
    assert (inputs.canonical_input_set_digest([rec, rec2])
            == inputs.canonical_input_set_digest([rec2, rec]))
