# ABOUTME: TDD tests for the curated-output + rolling-report contract
# ABOUTME: (workspace-hub#3431): curated taxonomy, digest_contribution, output_equality_digest,
# ABOUTME: failure disjointness/signature stability, surface eligibility, and the rolling report.
"""Curated output + rolling algorithm report contract tests (no engine dependency).

These pin the normative rules from the on-main
``docs/architecture/algorithm-run-dataset-contract.yaml`` ``records.output`` +
``identity.output_equality`` + ``failure_policy`` blocks:

- An Output record carries role, native_schema {id, version}, media_type,
  shape/row_count, per-field units, coordinate/sign convention (when applicable),
  validation_state, review_state, artifact_refs (referencing Artifacts by
  content_digest via :mod:`artifact`) and ``digest_contribution``.
- Curated-vs-excluded is a declared allowlist (primary_result / validation_evidence
  / selected_report / decision_support). Anything unlabeled defaults to EXCLUDED
  (fail-closed) -- never recorded / digested.
- ``digest_contribution`` DEFAULTS to ``included``; ``excluded`` is permitted ONLY
  via an explicitly declared + justified rule (fail-closed).
- ``output_equality_digest`` (default ``raw_bytes_sha256``) is a
  digest-of-sorted-digests, NOT raw byte concatenation. A semantic canonicalizer is
  allowed ONLY when the 5 fields are declared; undeclared normalization is
  presentation_only. Exact-rerun mismatch rejects without mutation (identity policy).
- Success vs failure requirement sets are provably disjoint: ``failure_signature``
  is the XOR discriminator. The signature strips volatile paths/timestamps/pids/hosts
  and normalizes stack frames by module qualname so the same fault hashes identically
  cross-machine. Failed runs are eligible only for run_health / diagnostics.
- The rolling report renders mandatory Inputs + Outputs, separates failed runs, pins
  every displayed run to an EXACT HF revision (a moving ref fails), draws eligibility
  from a SOURCE-REPO ledger (not HF visibility), and is HTML-safe.
"""

from __future__ import annotations

import hashlib

import pytest

from assetutilities.workflow_api import identity, output_contract, report


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _digest(tag: str) -> str:
    return hashlib.sha256(tag.encode()).hexdigest()


def _schema(**over) -> dict:
    base = {
        "id": "well-log-v",
        "version": "2.1.0",
        "fields": {"depth_m": "number", "name": "string"},
        "required": ["depth_m"],
    }
    base.update(over)
    return base


def _ref(tag: str) -> dict:
    return {"content_digest": _digest(tag)}


def _curated_output(*, label="primary_result", refs=("a",), digest_contribution=None,
                    exclusion_rule=None, **over) -> dict:
    kwargs = dict(
        role="result_table",
        native_schema=_schema(),
        media_type="application/json",
        curated_label=label,
        artifact_refs=[_ref(t) for t in refs],
        row_count=3,
        units={"depth_m": "m"},
    )
    if digest_contribution is not None:
        kwargs["digest_contribution"] = digest_contribution
    if exclusion_rule is not None:
        kwargs["exclusion_rule"] = exclusion_rule
    kwargs.update(over)
    return output_contract.make_output_record(**kwargs)


# ---------------------------------------------------------------------------
# 1. output record fields + native schema preserved
# ---------------------------------------------------------------------------

def test_output_record_fields_and_native_schema_preserved():
    rec = output_contract.make_output_record(
        role="result_table",
        native_schema=_schema(),
        media_type="application/json",
        curated_label="primary_result",
        artifact_refs=[_ref("a")],
        shape=[3, 2],
        row_count=3,
        units={"depth_m": "m"},
        convention={"axis": "z-down", "sign": "compression-positive"},
        validation_state="validated",
        review_state="reviewed",
    )
    for field in ("role", "native_schema", "media_type", "shape", "row_count",
                  "units", "convention", "validation_state", "review_state",
                  "artifact_refs", "digest_contribution", "curated_label"):
        assert field in rec
    # native_schema preserved verbatim (id + version at minimum)
    assert rec["native_schema"]["id"] == "well-log-v"
    assert rec["native_schema"]["version"] == "2.1.0"
    # artifact_refs reference artifacts by content_digest (do NOT redefine artifacts)
    assert rec["artifact_refs"][0]["content_digest"] == _digest("a")
    # residency + dataset_table match the on-main contract
    assert output_contract.DATASET_TABLE == "outputs"
    assert output_contract.RESIDENCY == "hf_object_and_normalized_record"


# ---------------------------------------------------------------------------
# 2. curated taxonomy allowlist; unlabeled defaults EXCLUDED (fail-closed)
# ---------------------------------------------------------------------------

def test_curated_taxonomy_allowlist_unlabeled_defaults_excluded():
    assert output_contract.CURATED_LABELS == frozenset(
        {"primary_result", "validation_evidence", "selected_report", "decision_support"}
    )
    for good in output_contract.CURATED_LABELS:
        assert output_contract.is_curated_label(good) is True
    # unlabeled / unknown -> excluded (never recorded)
    assert output_contract.is_curated_label(None) is False
    assert output_contract.is_curated_label("scratch_dump") is False

    # an unlabeled output cannot be recorded at all (fail-closed)
    with pytest.raises(output_contract.OutputContractError):
        _curated_output(label=None)
    with pytest.raises(output_contract.OutputContractError):
        _curated_output(label="scratch_dump")


# ---------------------------------------------------------------------------
# 3. digest_contribution defaults included; exclusion must be declared+justified
# ---------------------------------------------------------------------------

def test_digest_contribution_defaults_included_and_exclusion_must_be_declared():
    rec = _curated_output()
    assert rec["digest_contribution"] == "included"

    # silent / undeclared exclusion fails closed
    with pytest.raises(output_contract.OutputContractError):
        _curated_output(digest_contribution="excluded")
    with pytest.raises(output_contract.OutputContractError):
        _curated_output(digest_contribution="excluded", exclusion_rule={"rule_id": "r1"})

    # a declared + justified exclusion rule is permitted
    ex = _curated_output(
        digest_contribution="excluded",
        exclusion_rule={"rule_id": "constant-header",
                        "justification": "byte-identical constant banner, reproduced exactly"},
    )
    assert ex["digest_contribution"] == "excluded"
    assert ex["exclusion_rule"]["rule_id"] == "constant-header"


# ---------------------------------------------------------------------------
# 4. output_equality_digest = digest-of-sorted-digests (NOT concatenation)
# ---------------------------------------------------------------------------

def test_output_equality_digest_is_digest_of_sorted_artifact_digests():
    o1 = _curated_output(refs=("x", "y"))
    o2 = _curated_output(label="validation_evidence", refs=("z",))

    res = output_contract.output_equality_digest([o1, o2])
    assert res["algorithm"] == "raw_bytes_sha256"

    all_digs = sorted([_digest("x"), _digest("y"), _digest("z")])
    expected = hashlib.sha256(identity.canonicalize(all_digs).encode()).hexdigest()
    assert res["digest"] == expected

    # NOT raw byte concatenation (boundary-ambiguous)
    concat = hashlib.sha256("".join(all_digs).encode()).hexdigest()
    assert res["digest"] != concat

    # order independence (sorted): reversed input -> same digest
    res_rev = output_contract.output_equality_digest([o2, o1])
    assert res_rev["digest"] == res["digest"]

    # a declared-excluded output does NOT contribute to the digest
    o_excl = _curated_output(
        refs=("w",),
        digest_contribution="excluded",
        exclusion_rule={"rule_id": "r", "justification": "nondeterministic-but-approved presentation only"},
    )
    res_with_excl = output_contract.output_equality_digest([o1, o2, o_excl])
    assert res_with_excl["digest"] == res["digest"]


# ---------------------------------------------------------------------------
# 5. undeclared semantic canonicalizer fails closed (declared needs 5 fields)
# ---------------------------------------------------------------------------

def test_undeclared_semantic_canonicalizer_fails_closed():
    o1 = _curated_output(refs=("x",))
    assert output_contract.SEMANTIC_EXCEPTION_REQUIRED == (
        "canonicalizer_id", "canonicalizer_version", "raw_hash", "semantic_hash", "explicit_approval",
    )

    # partial declaration -> fail closed
    with pytest.raises(output_contract.OutputContractError):
        output_contract.output_equality_digest(
            [o1], semantic_canonicalizer={"canonicalizer_id": "sortcols", "canonicalizer_version": "1"},
        )

    # full declaration -> semantic algorithm, digest is the declared semantic_hash
    decl = {
        "canonicalizer_id": "sortcols",
        "canonicalizer_version": "1.0.0",
        "raw_hash": _digest("raw"),
        "semantic_hash": _digest("sem"),
        "explicit_approval": "owner@ok",
    }
    res = output_contract.output_equality_digest([o1], semantic_canonicalizer=decl)
    assert res["digest"] == _digest("sem")
    assert res["algorithm"].startswith("semantic:")


# ---------------------------------------------------------------------------
# 6. exact-rerun output mismatch rejects without mutation
# ---------------------------------------------------------------------------

def test_exact_rerun_output_mismatch_rejects_without_mutation():
    run1 = output_contract.output_equality_digest([_curated_output(refs=("x",))])
    run2 = output_contract.output_equality_digest([_curated_output(refs=("DIFFERENT",))])
    assert run1["digest"] != run2["digest"]

    prior = {"run_id": "r-1", "output_equality_digest": run1["digest"]}
    snapshot = dict(prior)
    with pytest.raises(identity.OutputMismatchError):
        output_contract.assert_output_equality(run1["digest"], run2["digest"], prior_record=prior)
    # reject_without_mutation: prior record untouched
    assert prior == snapshot

    # equal digests accepted
    assert output_contract.assert_output_equality(run1["digest"], run1["digest"]) is True


# ---------------------------------------------------------------------------
# 7. success vs failure requirement sets are disjoint (failure_signature XOR)
# ---------------------------------------------------------------------------

def test_success_and_failure_requirements_disjoint():
    norm = output_contract.make_failure_normalization(
        failure_phase="solve",
        failure_code="singular_matrix",
        failure_signature="fsig-1:abc",
        curated_diagnostic_digests=[_digest("diag")],
        replay_evidence={"seed": 7, "inputs": "input_set_id:1"},
    )
    # reproducible_failure MUST carry a failure_signature
    output_contract.assert_status_requirements("reproducible_failure", norm)
    with pytest.raises(output_contract.OutputContractError):
        output_contract.assert_status_requirements(
            "reproducible_failure", {k: v for k, v in norm.items() if k != "failure_signature"}
        )

    # succeeded MUST NOT carry a failure_signature (XOR discriminator)
    output_contract.assert_status_requirements("succeeded", {"outputs": ["o1"]})
    with pytest.raises(output_contract.OutputContractError):
        output_contract.assert_status_requirements("succeeded", {"failure_signature": "fsig-1:abc"})


# ---------------------------------------------------------------------------
# 8. failure_signature stable cross-machine
# ---------------------------------------------------------------------------

def test_failure_signature_stable_cross_machine():
    machine_a = dict(
        phase="solve",
        code="ZeroDivisionError",
        frames=[
            {"file": "/home/alice/proj/.venv/lib/python3.11/site-packages/numpy/core/_methods.py",
             "func": "_mean", "lineno": 42},
            {"file": "/home/alice/proj/src/algo/run.py", "module": "algo.run", "func": "solve", "lineno": 88},
        ],
        detail="failed at 2026-07-11T14:58:01Z pid=12345 host=ace-linux-1 in /home/alice/proj/tmp/x",
    )
    machine_b = dict(
        phase="solve",
        code="ZeroDivisionError",
        frames=[
            {"file": "/opt/ci/build/.venv/lib/python3.11/site-packages/numpy/core/_methods.py",
             "func": "_mean", "lineno": 47},
            {"file": "/opt/ci/build/src/algo/run.py", "module": "algo.run", "func": "solve", "lineno": 91},
        ],
        detail="failed at 2026-07-12T09:03:55Z pid=999 host=ci-runner-7 in /opt/ci/build/tmp/y",
    )
    sig_a = output_contract.failure_signature(**machine_a)
    sig_b = output_contract.failure_signature(**machine_b)
    assert sig_a == sig_b  # same fault -> identical signature cross-machine

    # a genuinely different fault (different code) -> different signature
    other = dict(machine_a)
    other["code"] = "ValueError"
    assert output_contract.failure_signature(**other) != sig_a


# ---------------------------------------------------------------------------
# 9. failed run forbidden from metric/insight/decision surfaces
# ---------------------------------------------------------------------------

def test_failed_run_forbidden_from_metric_insight_decision_surfaces():
    assert output_contract.FAILURE_ELIGIBLE_SURFACES == frozenset({"run_health", "diagnostics"})
    assert output_contract.FAILURE_FORBIDDEN_SURFACES == frozenset(
        {"metric_observations", "insights", "decision_briefs"}
    )
    for surface in output_contract.FAILURE_ELIGIBLE_SURFACES:
        assert output_contract.assert_surface_allowed("reproducible_failure", surface) is True
    for surface in output_contract.FAILURE_FORBIDDEN_SURFACES:
        with pytest.raises(output_contract.OutputContractError):
            output_contract.assert_surface_allowed("reproducible_failure", surface)
    # a succeeded run may publish to any of those surfaces
    assert output_contract.assert_surface_allowed("succeeded", "decision_briefs") is True


# ---------------------------------------------------------------------------
# 10. report pins an EXACT HF revision (moving ref fails)
# ---------------------------------------------------------------------------

_EXACT_REV = "a" * 40


def _run(run_id="r-1", status="succeeded", rev=_EXACT_REV, **over):
    base = dict(
        run_id=run_id,
        status=status,
        hf_revision=rev,
        inputs=[{"name": "grid", "value": "512x512"}],
        outputs=[{"role": "result_table", "value": "ok"}],
    )
    base.update(over)
    return base


def _ledger(*run_ids):
    return [{"run_id": rid, "published": True} for rid in run_ids]


def test_report_pins_exact_revision_moving_ref_fails():
    assert report.is_exact_revision(_EXACT_REV) is True
    for moving in ("main", "HEAD", "refs/heads/main", "v1.0.0", "a" * 39):
        assert report.is_exact_revision(moving) is False

    runs = [_run(rev=_EXACT_REV)]
    ledger = _ledger("r-1")
    # finalized (pinned) with an exact revision succeeds and shows the revision
    html = report.render_report(algorithm="deep-solver", runs=runs, ledger=ledger, pinned=True)
    assert _EXACT_REV in html

    # a pinned report over a moving ref fails
    with pytest.raises(output_contract.OutputContractError):
        report.render_report(
            algorithm="deep-solver", runs=[_run(rev="main")], ledger=ledger, pinned=True
        )
    # a DRAFT (unpinned) report tolerates a not-yet-pinned revision
    draft = report.render_report(
        algorithm="deep-solver", runs=[_run(rev="main")], ledger=ledger, pinned=False
    )
    assert "DRAFT" in draft.upper()


# ---------------------------------------------------------------------------
# 11. report renders mandatory Inputs + Outputs and separates failed runs
# ---------------------------------------------------------------------------

def test_report_renders_mandatory_inputs_outputs_and_separates_failures():
    runs = [
        _run(run_id="r-ok", status="succeeded",
             optional={"convergence": "residual 1e-9 in 12 iters"}),
        _run(run_id="r-bad", status="reproducible_failure",
             outputs=[], inputs=[{"name": "grid", "value": "1024"}]),
    ]
    ledger = _ledger("r-ok", "r-bad")
    html = report.render_report(algorithm="deep-solver", runs=runs, ledger=ledger, pinned=True)

    # mandatory sections always present
    assert "Inputs" in html
    assert "Outputs" in html
    # only-applicable optional section rendered when provided...
    assert "convergence" in html
    # ...and absent when not provided (no empty optional scaffolding)
    assert "sensitivity" not in html
    # failed run is clearly separated + labelled
    assert "failed-run" in html
    assert "r-bad" in html and "r-ok" in html
    # the failed run id appears after the failed-runs boundary
    assert html.index("failed-run") < html.index("r-bad")


# ---------------------------------------------------------------------------
# 12. report eligibility from the SOURCE-REPO ledger, not HF visibility
# ---------------------------------------------------------------------------

def test_report_eligibility_from_source_repo_ledger_not_hf_visibility():
    runs = [
        _run(run_id="r-published", hf_visible=False),   # in ledger, HF says hidden
        _run(run_id="r-unpublished", hf_visible=True),  # NOT in ledger, HF says visible
    ]
    ledger = _ledger("r-published")  # source-repo publications.jsonl is the source of truth
    html = report.render_report(algorithm="deep-solver", runs=runs, ledger=ledger, pinned=True)
    assert "r-published" in html      # ledger wins over HF invisibility
    assert "r-unpublished" not in html  # HF visibility does NOT make it eligible


# ---------------------------------------------------------------------------
# 13. report rejects / escapes unsafe HTML
# ---------------------------------------------------------------------------

def test_report_rejects_unsafe_html():
    payload = "<script>alert('x')</script>"
    runs = [_run(run_id="r-xss", inputs=[{"name": "note", "value": payload}])]
    ledger = _ledger("r-xss")
    html = report.render_report(algorithm="deep-solver", runs=runs, ledger=ledger, pinned=True)
    assert payload not in html          # raw script must never survive
    assert "&lt;script&gt;" in html     # it is HTML-escaped instead


# ---------------------------------------------------------------------------
# 14. output violating its declared native schema is rejected
# ---------------------------------------------------------------------------

def test_output_violating_declared_native_schema_rejected():
    schema = _schema()
    # conforming payload passes
    assert output_contract.assert_payload_conforms(schema, {"depth_m": 1500.0, "name": "A-1"}) is True

    # missing required field
    with pytest.raises(output_contract.OutputContractError):
        output_contract.assert_payload_conforms(schema, {"name": "A-1"})
    # wrong type
    with pytest.raises(output_contract.OutputContractError):
        output_contract.assert_payload_conforms(schema, {"depth_m": "deep", "name": "A-1"})
    # undeclared extra field (fail-closed)
    with pytest.raises(output_contract.OutputContractError):
        output_contract.assert_payload_conforms(schema, {"depth_m": 1.0, "name": "A-1", "rogue": 9})
