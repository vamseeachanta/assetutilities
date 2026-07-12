# ABOUTME: TDD tests for the publication + staged-promotion contract (workspace-hub#3433):
# ABOUTME: five-record projection, evidence-bearing promotion state machine, fail-closed egress,
# ABOUTME: injectable HF port with in-memory fake, append-only source-repo publication ledger.
"""Publication + staged-promotion contract tests (no network, no engine).

These pin the normative rules from the on-main
``docs/architecture/algorithm-run-dataset-contract.yaml`` ``promotion`` block and
the approved+remediated #3433 plan:

- a ``RunProjection`` binds the five record types (identity/artifact/inputs/output/
  metrics) under ONE run_id, strict-identity-bound (envelope hashes are evidence only);
- the promotion state machine (emitted -> validated -> replayed -> draft_rendered ->
  reviewed -> hf_candidate -> report_pinned -> accepted, plus terminal ``rejected``)
  carries an EVIDENCE-BEARING journal -- resume validates PROOFS, not a bare ordinal;
- a composed fail-closed egress gate fires at four points (source / report draft /
  HF card+bytes / final pinned report + publication record);
- an injectable ``HfPort`` (in-memory fake for tests; real hub adapter is a documented
  shim) with immutable revisions + content-addressed objects; and
- an append-only SOURCE-REPO ``publications.jsonl`` ledger that is the SOLE eligibility
  authority and re-validates the journal proofs before appending.

No real Hugging Face network upload is exercised anywhere.
"""

from __future__ import annotations

import hashlib

import pytest

from assetutilities.workflow_api import identity, inputs, artifact, metrics
from assetutilities.workflow_api import output_contract as oc
from assetutilities.workflow_api.publication import (
    projection as projection_mod,
    promotion as promotion_mod,
    egress as egress_mod,
    hf_port as hf_port_mod,
    ledger as ledger_mod,
)


# ---------------------------------------------------------------------------
# real-byte builders (content_digest must be a true sha256 of real bytes so the
# HF re-hash stage has something to verify)
# ---------------------------------------------------------------------------

OBJ_BYTES = b'{"basin": "permian", "wells": 3}'
OBJ_DIGEST = hashlib.sha256(OBJ_BYTES).hexdigest()

_PUBLIC_EVIDENCE = {"redistribution": "public", "license": "CC-BY-4.0"}


def _input_record():
    return inputs.make_input(
        kind="dataset_snapshot",
        role="wells",
        schema_version="wed-1",
        source_authority="EIA",
        public_locator={"uri": "https://eia.gov/ds/wells", "version": "v2026-06"},
        data_as_of="2026-06-01",
        retrieval_time="2026-07-11T00:00:00Z",
        selection={"basin": "permian"},
        snapshot_identity="d" * 64,
        content_digest=OBJ_DIGEST,
        redistribution_rights="public",
        redistribution_evidence=_PUBLIC_EVIDENCE,
        replay_location="content_addressed_dataset_object",
    )


def _artifact_record():
    return artifact.physical_artifact(
        OBJ_BYTES,
        media_type="application/json",
        native_format="json",
        license_evidence_ref=_PUBLIC_EVIDENCE,
    )


def _output_record():
    return oc.make_output_record(
        role="primary",
        native_schema={"id": "gasfield-out", "version": "1"},
        media_type="application/json",
        curated_label="primary_result",
        artifact_refs=[OBJ_DIGEST],
    )


def _metric_observation(run_id, store):
    definition = metrics.make_metric_definition(
        metric_id="wed/gasfield/recovery_factor",
        algorithm_id="wed/gasfield",
        definition_version="1",
        label="Recovery factor",
        meaning="fraction recovered",
        unit_or_dimension="fraction",
        data_type="number",
        derivation="curated",
        applicability="all",
        directionality="higher_is_better",
        quality_rule="0..1",
    )
    store.register(definition)
    return metrics.make_metric_observation(
        definition=definition,
        run_id=run_id,
        value=1,
        quality_state="valid",
        derivation_evidence={"from": "primary"},
    )


def _identity_context(input_records):
    pairs = [(rec["role"], inputs.input_record_id(rec)) for rec in input_records]
    return dict(
        algorithm_id="wed/gasfield",
        semantic_version="1.0.0",
        clean_git_commit="a" * 40,
        input_schema_version="in-1",
        output_schema_version="out-1",
        environment_digest="env-" + "b" * 12,
        inputs=pairs,
        execution_parameters={"mode": "batch"},
        seed=7,
    )


def _build_projection(**overrides):
    input_records = [_input_record()]
    outputs = [_output_record()]
    oe = oc.output_equality_digest(outputs)
    store = metrics.MetricDefinitionStore()
    ident = identity.derive_run_identity(**_identity_context(input_records))
    observation = _metric_observation(ident["run_id"], store)
    kwargs = dict(
        identity_context=_identity_context(input_records),
        input_records=input_records,
        artifacts=[_artifact_record()],
        outputs=outputs,
        output_equality_digest=oe,
        metric_observations=[observation],
        object_bytes={OBJ_DIGEST: OBJ_BYTES},
        terminal_status="succeeded",
        metric_store=store,
        evidence={"envelope_input_hash": "e" * 64},
    )
    kwargs.update(overrides)
    return projection_mod.build_projection(**kwargs)


def _machine(*, force_revision=None, env_tokens=None, legal_deny_list=(),
             external_validator=None, port=None, ledger=None, projection=None):
    projection = projection or _build_projection()
    port = port or hf_port_mod.InMemoryHfPort(force_revision=force_revision)
    ledger = ledger or ledger_mod.Ledger()
    gate = egress_mod.EgressGate(
        legal_deny_list=legal_deny_list,
        env_tokens=env_tokens or {},
        external_validator=external_validator,
    )
    return promotion_mod.PromotionMachine(
        projection, hf_port=port, ledger=ledger, egress=gate
    ), port, ledger


# The ordered happy-path drivers.
_ORDER = (
    "emitted", "validated", "replayed", "draft_rendered",
    "reviewed", "hf_candidate", "report_pinned", "accepted",
)


def _advance_one(machine):
    state = machine.state
    if state == "emitted":
        machine.validate()
    elif state == "validated":
        machine.replay()
    elif state == "replayed":
        machine.render_draft()
    elif state == "draft_rendered":
        machine.review(
            human_promotion_review={"approved": True, "reviewer": "vp"},
            adversarial_artifact_review={"approved": True, "reviewer": "red-team"},
        )
    elif state == "reviewed":
        machine.promote_to_hf_candidate()
    elif state == "hf_candidate":
        machine.pin_report()
    elif state == "report_pinned":
        machine.accept()
    else:
        raise AssertionError(f"cannot advance from terminal {state!r}")


def _drive(machine, upto):
    target = _ORDER.index(upto)
    while _ORDER.index(machine.state) < target:
        _advance_one(machine)
    return machine


# ---------------------------------------------------------------------------
# 1. projection binds five records, strict identity
# ---------------------------------------------------------------------------

def test_projection_binds_five_records_identity_strict():
    proj = _build_projection()
    # one run_id binds identity + artifact + inputs + output + metrics
    assert proj.run_id
    assert proj.algorithm_id == "wed/gasfield"
    assert proj.terminal_status == "succeeded"
    assert OBJ_DIGEST in proj.object_digests()
    assert proj.output_equality_digest["digest"]
    # envelope hashes are EVIDENCE only, never identity
    assert proj.evidence["envelope_input_hash"] == "e" * 64
    assert proj.run_id != proj.evidence["envelope_input_hash"]

    # strict identity bind: an observation from a DIFFERENT run is rejected
    store = metrics.MetricDefinitionStore()
    alien = _metric_observation("deadbeef" * 8, store)
    with pytest.raises(projection_mod.ProjectionError):
        _build_projection(metric_observations=[alien], metric_store=store)

    # strict identity bind: input records whose set digest disagrees with the
    # declared identity input_set_id are rejected (identity, not envelope, binds).
    bad_ctx = _identity_context([_input_record()])
    bad_ctx["inputs"] = [("wells", "f" * 64)]  # a wrong input_record_id pair
    with pytest.raises(projection_mod.ProjectionError):
        _build_projection(identity_context=bad_ctx)


# valid HF SPDX-ish license ids (the run-ledger is aceengineer's own data -> ``other``).
_VALID_HF_LICENSES = {"other", "mit", "apache-2.0", "cc-by-4.0", "cc0-1.0"}


def _parse_card_frontmatter(card_bytes):
    """Split a dataset card into (parsed YAML frontmatter dict, body). Fails if absent."""
    import yaml  # PyYAML is a hard assetutilities dependency

    text = card_bytes.decode("utf-8")
    assert text.startswith("---\n"), "dataset card must open with a YAML frontmatter fence"
    _, front, body = text.split("---\n", 2)
    meta = yaml.safe_load(front)
    assert isinstance(meta, dict), "frontmatter must parse to a YAML mapping"
    return meta, body


def test_dataset_card_has_valid_yaml_frontmatter_and_no_bogus_configs():
    # The generated default card (no card supplied) must be a VALID HF dataset card:
    # parseable YAML frontmatter with a valid license + pretty_name, and -- because this
    # is a content-addressed object store, not tabular parquet -- NO fabricated configs
    # block (which would make the datasets viewer error). Regression for the dm#1505 live
    # "empty or missing yaml metadata in repo card" warning.
    proj = _build_projection()
    meta, body = _parse_card_frontmatter(proj.dataset_card())

    assert meta.get("license") in _VALID_HF_LICENSES
    assert isinstance(meta.get("pretty_name"), str) and meta["pretty_name"].strip()
    assert isinstance(meta.get("tags"), list) and meta["tags"]
    # a content-addressed store has no tabular tables -> a configs block must NOT be faked
    assert "configs" not in meta

    # the body is truthful to the actual content-addressed ledger contract
    assert "objects/<sha256[:2]>/<sha256>" in body
    assert "publications.jsonl" in body
    assert "3433" in body

    # parameterization: repo id / run count are threaded through when supplied
    parameterized = proj.dataset_card(
        repo_id="aceengineer/digitalmodel-runs", run_count=3
    )
    meta2, body2 = _parse_card_frontmatter(parameterized)
    assert meta2["license"] in _VALID_HF_LICENSES
    assert "aceengineer/digitalmodel-runs" in body2
    assert "configs" not in meta2

    # a supplied card is passed through verbatim (unchanged contract)
    assert proj.with_card(b"custom").dataset_card() == b"custom"


# ---------------------------------------------------------------------------
# 2. no bypass edge to accepted
# ---------------------------------------------------------------------------

def test_state_machine_has_no_bypass_edge_to_accepted():
    # the ONLY predecessor of accepted is report_pinned
    preds = [s for s, dests in promotion_mod.TRANSITIONS.items() if "accepted" in dests]
    assert preds == ["report_pinned"]
    # calling accept() from every earlier state fails closed
    for state in ("emitted", "validated", "replayed", "draft_rendered",
                  "reviewed", "hf_candidate"):
        machine, _, ledger = _machine()
        _drive(machine, state)
        with pytest.raises(promotion_mod.PromotionError):
            machine.accept()
        assert ledger.eligible_run_ids() == set()


# ---------------------------------------------------------------------------
# 3. each transition requires its contract requirements
# ---------------------------------------------------------------------------

def test_each_transition_requires_its_contract_requirements():
    assert promotion_mod.REQUIREMENTS["validated"] == (
        "schema", "hashes", "provenance", "license", "legal",
        "sanitization", "clean_source",
    )
    assert promotion_mod.REQUIREMENTS["draft_rendered"] == (
        "mandatory_report_sections", "exact_candidate_run_set",
    )
    assert promotion_mod.REQUIREMENTS["reviewed"] == (
        "human_promotion_review", "adversarial_artifact_review",
    )
    assert promotion_mod.REQUIREMENTS["hf_candidate"] == (
        "complete_projection_commit", "object_integrity",
    )
    assert promotion_mod.REQUIREMENTS["report_pinned"] == (
        "exact_hf_revision", "source_report_commit",
    )
    assert promotion_mod.REQUIREMENTS["accepted"] == (
        "verified_hf_revision", "verified_report_commit", "cross_system_verification",
    )
    # replayed success branch demands output_equality; the journal proof records it
    machine, _, _ = _machine()
    _drive(machine, "replayed")
    proof = machine.journal.proof_for("replayed")
    assert proof["clean_environment_replay"] is True
    assert proof["output_equality"] == machine.projection.output_equality_digest["digest"]


# ---------------------------------------------------------------------------
# 4. run record never mutates candidate -> accepted
# ---------------------------------------------------------------------------

def test_run_record_never_mutates_candidate_to_accepted():
    machine, _, ledger = _machine()
    _drive(machine, "hf_candidate")
    before = machine.run_record()
    _drive(machine, "accepted")
    after = machine.run_record()
    assert before == after  # the run row is written once and never mutated
    # acceptance appends an append-only Publication record (a SEPARATE object)
    assert machine.projection.run_id in ledger.eligible_run_ids()
    pubs = [r for r in ledger.records() if r.get("run_id") == machine.projection.run_id
            and r.get("published")]
    assert len(pubs) == 1


# ---------------------------------------------------------------------------
# 5. hf_candidate is analysis-ineligible until a publication record accepts it
# ---------------------------------------------------------------------------

def test_hf_candidate_ineligible_until_publication_record():
    machine, port, ledger = _machine()
    _drive(machine, "hf_candidate")
    run_id = machine.projection.run_id
    # the object is VISIBLE on HF but eligibility is read from the ledger ONLY
    assert port.list_objects(machine.candidate_revision)
    assert ledger.is_eligible(run_id) is False
    assert run_id not in ledger.eligible_run_ids()
    _drive(machine, "accepted")
    assert ledger.is_eligible(run_id) is True
    assert run_id in ledger.eligible_run_ids()


# ---------------------------------------------------------------------------
# 6. reviewed requires BOTH channels; absent is not approval
# ---------------------------------------------------------------------------

def test_reviewed_requires_both_channels_absent_is_not_approval():
    # missing adversarial channel
    machine, _, _ = _machine()
    _drive(machine, "draft_rendered")
    with pytest.raises(promotion_mod.PromotionError):
        machine.review(
            human_promotion_review={"approved": True},
            adversarial_artifact_review=None,
        )
    assert machine.state == "draft_rendered"

    # an UNAVAILABLE channel is not approval
    machine2, _, _ = _machine()
    _drive(machine2, "draft_rendered")
    with pytest.raises(promotion_mod.PromotionError):
        machine2.review(
            human_promotion_review={"approved": True},
            adversarial_artifact_review={"available": False},
        )

    # an explicit rejection is not approval
    machine3, _, _ = _machine()
    _drive(machine3, "draft_rendered")
    with pytest.raises(promotion_mod.PromotionError):
        machine3.review(
            human_promotion_review={"approved": False},
            adversarial_artifact_review={"approved": True},
        )

    # BOTH explicit approvals advance
    machine4, _, _ = _machine()
    _drive(machine4, "draft_rendered")
    machine4.review(
        human_promotion_review={"approved": True},
        adversarial_artifact_review={"approved": True},
    )
    assert machine4.state == "reviewed"


# ---------------------------------------------------------------------------
# 7. hf_candidate re-verifies every uploaded byte
# ---------------------------------------------------------------------------

def test_hf_candidate_reverifies_every_uploaded_byte():
    # a corrupted OBJECT byte is caught by the post-upload re-hash
    machine, port, _ = _machine()
    _drive(machine, "reviewed")
    port.corrupt_objects = {OBJ_DIGEST}
    with pytest.raises((promotion_mod.PromotionError, artifact.IntegrityError)):
        machine.promote_to_hf_candidate()
    assert machine.state == "reviewed"

    # a corrupted CARD is caught too
    machine2, port2, _ = _machine()
    _drive(machine2, "reviewed")
    port2.corrupt_card = True
    with pytest.raises((promotion_mod.PromotionError, artifact.IntegrityError)):
        machine2.promote_to_hf_candidate()

    # the clean path verifies EVERY object + the card and advances
    machine3, port3, _ = _machine()
    _drive(machine3, "hf_candidate")
    proof = machine3.journal.proof_for("hf_candidate")
    assert proof["object_integrity"][OBJ_DIGEST] == "verified"
    assert proof["object_integrity"]["card"] == "verified"


# ---------------------------------------------------------------------------
# 8. report pin requires an exact revision; a moving ref fails
# ---------------------------------------------------------------------------

def test_report_pin_requires_exact_revision_moving_ref_fails():
    machine, port, _ = _machine(force_revision="main")
    _drive(machine, "hf_candidate")
    assert machine.candidate_revision == "main"
    with pytest.raises(promotion_mod.PromotionError):
        machine.pin_report()
    assert machine.state == "hf_candidate"

    # an exact revision pins
    machine2, port2, _ = _machine()
    _drive(machine2, "hf_candidate")
    machine2.pin_report()
    assert machine2.state == "report_pinned"
    assert promotion_mod.is_exact_revision(machine2.candidate_revision)


# ---------------------------------------------------------------------------
# 9. accept requires cross-system verification
# ---------------------------------------------------------------------------

def test_accept_requires_cross_system_verification():
    machine, port, ledger = _machine()
    _drive(machine, "report_pinned")
    # break the HF side between pin and accept -> cross-verify fails -> no publication
    port.make_object_unavailable(machine.candidate_revision, OBJ_DIGEST)
    with pytest.raises(promotion_mod.PromotionError):
        machine.accept()
    assert ledger.eligible_run_ids() == set()
    assert machine.state == "report_pinned"

    # the clean cross-system verification path accepts + records the proof
    machine2, _, ledger2 = _machine()
    _drive(machine2, "accepted")
    proof = machine2.journal.proof_for("accepted")
    assert proof["cross_system_verification"] is True
    assert proof["verified_hf_revision"] == machine2.candidate_revision


# ---------------------------------------------------------------------------
# 10. transient failure retries R1, no second candidate
# ---------------------------------------------------------------------------

def test_transient_failure_retries_R1_no_second_candidate():
    machine, port, ledger = _machine()
    _drive(machine, "hf_candidate")
    r1 = machine.candidate_revision
    assert port.commit_count == 1
    # a transient pin/verify fault -> resume retries against the SAME captured R1
    port.inject_transient_fetch_failures(2)
    outcome = machine.resume()
    assert outcome["outcome"] == "retried_R1"
    assert machine.candidate_revision == r1
    assert port.commit_count == 1  # no second candidate, no duplicate run row
    _drive(machine, "accepted")
    assert machine.candidate_revision == r1


# ---------------------------------------------------------------------------
# 11. irreparable R1 -> rejected disposition + corrective R2 (same run_id)
# ---------------------------------------------------------------------------

def test_irreparable_R1_rejected_disposition_and_corrective_R2():
    machine, port, ledger = _machine()
    _drive(machine, "hf_candidate")
    r1 = machine.candidate_revision
    run_id = machine.projection.run_id
    # R1 is irreparably corrupt (post-upload byte re-hash can never pass)
    port.corrupt_stored_object(r1, OBJ_DIGEST)
    outcome = machine.resume()
    assert outcome["outcome"] == "corrective_R2"
    r2 = machine.candidate_revision
    assert r2 != r1
    assert promotion_mod.is_exact_revision(r2)
    assert machine.projection.run_id == run_id  # SAME run_id, one run record
    assert port.commit_count == 2
    # R1 was never overwritten; it stays as a rejected disposition in the ledger
    assert r1 in port.list_revisions()
    dispositions = [r for r in ledger.records()
                    if r.get("disposition") == "rejected" and r.get("revision") == r1]
    assert len(dispositions) == 1
    # the corrective candidate can still be accepted under the same run_id
    _drive(machine, "accepted")
    assert ledger.is_eligible(run_id) is True


# ---------------------------------------------------------------------------
# 12. resume validates proofs, not a bare ordinal
# ---------------------------------------------------------------------------

def test_resume_validates_proofs_not_ordinal():
    machine, port, _ = _machine()
    _drive(machine, "hf_candidate")
    # tamper a prior proof WITHOUT touching the state ordinal
    machine.journal.entries[2]["proof"]["clean_environment_replay"] = "TAMPERED"
    with pytest.raises(promotion_mod.PromotionError):
        machine.resume()


# ---------------------------------------------------------------------------
# 13. ledger writer rejects a malformed / hand-built journal
# ---------------------------------------------------------------------------

def test_ledger_writer_rejects_malformed_or_handbuilt_journal():
    machine, port, ledger = _machine()
    _drive(machine, "report_pinned")
    good = machine.journal

    # a hand-built journal that SKIPS the reviewed state is rejected
    skipped = [e for e in good.entries if e["state"] != "reviewed"]
    with pytest.raises(ledger_mod.LedgerError):
        ledger.append_publication(
            projection=machine.projection,
            journal_entries=skipped,
            accepted_proof={"verified_hf_revision": machine.candidate_revision,
                            "verified_report_commit": "c" * 40,
                            "cross_system_verification": True},
        )

    # a tampered proof digest is rejected
    tampered = [dict(e) for e in good.entries]
    tampered[1] = dict(tampered[1])
    tampered[1]["proof"] = dict(tampered[1]["proof"])
    tampered[1]["proof"]["schema"] = "FORGED"
    with pytest.raises(ledger_mod.LedgerError):
        ledger.append_publication(
            projection=machine.projection,
            journal_entries=tampered,
            accepted_proof={"verified_hf_revision": machine.candidate_revision,
                            "verified_report_commit": "c" * 40,
                            "cross_system_verification": True},
        )
    assert ledger.eligible_run_ids() == set()


# ---------------------------------------------------------------------------
# 14. egress four gates fail closed
# ---------------------------------------------------------------------------

def test_egress_four_gates_fail_closed():
    token = "hf" + "_" + "LIVESECRETTOKENVALUE0001"
    env = {"HF_TOKEN": token}

    # Gate A: a secret appended to a source byte also breaks its content digest, so
    # the projection itself rejects the tampered byte before it can be staged.
    with pytest.raises(projection_mod.ProjectionError):
        _build_projection(object_bytes={OBJ_DIGEST: OBJ_BYTES + token.encode()})

    gate = egress_mod.EgressGate(env_tokens=env)
    # Gate A over arbitrary source text
    with pytest.raises(egress_mod.EgressDenied):
        gate.gate_source_texts([f"clean ... {token} ... trailing"])
    # Gate B over a rendered report draft
    with pytest.raises(egress_mod.EgressDenied):
        gate.gate_report_draft(f"<main>{token}</main>")
    # Gate C over the dataset card + upload bytes
    with pytest.raises(egress_mod.EgressDenied):
        gate.gate_hf_upload(card=f"card {token}".encode(), objects={OBJ_DIGEST: OBJ_BYTES})
    with pytest.raises(egress_mod.EgressDenied):
        gate.gate_hf_upload(card=b"card", objects={OBJ_DIGEST: token.encode()})
    # Gate D over the final pinned report + publication record
    with pytest.raises(egress_mod.EgressDenied):
        gate.gate_final(pinned_report="<main>ok</main>",
                        publication_record={"run_id": "r", "note": token})

    # the machine's Gate C fires BEFORE the HF commit (no bytes leave)
    machine, port, _ = _machine(env_tokens=env)
    _drive(machine, "reviewed")
    machine.projection = machine.projection.with_card(f"leak {token}".encode())
    with pytest.raises(egress_mod.EgressDenied):
        machine.promote_to_hf_candidate()
    assert port.commit_count == 0


# ---------------------------------------------------------------------------
# 15. egress validator shim fails closed and names uncovered checks
# ---------------------------------------------------------------------------

def test_egress_validator_shim_fails_closed_and_names_uncovered():
    # no external #3013 validator -> bounded shim, still enforces the covered subset
    gate = egress_mod.EgressGate(env_tokens={})
    result = gate.gate_source_texts(["perfectly clean source text"])
    assert result.available is False
    assert result.uncovered == ["public_identity_registry_id_check"]

    # even under the shim a secret is denied (fail-closed)
    token = "ghp" + "_" + "SHIMSTILLBLOCKSTHIS000001"
    gate2 = egress_mod.EgressGate(env_tokens={"GH_TOKEN": token})
    with pytest.raises(egress_mod.EgressDenied):
        gate2.gate_source_texts([f"x {token} y"])

    # with a validator injected, coverage is complete
    class _Validator:
        available = True

        def validate(self, texts):
            return {"ok": True, "uncovered": []}

    gate3 = egress_mod.EgressGate(env_tokens={}, external_validator=_Validator())
    result3 = gate3.gate_source_texts(["clean"])
    assert result3.available is True
    assert result3.uncovered == []


# ---------------------------------------------------------------------------
# 16. tokens never reach logs or records
# ---------------------------------------------------------------------------

def test_tokens_never_reach_logs_or_records():
    token = "hf" + "_" + "ABSOLUTELYSECRETVALUE9999"
    gate = egress_mod.EgressGate(env_tokens={"HF_TOKEN": token})
    try:
        gate.gate_report_draft(f"<main>{token}</main>")
    except egress_mod.EgressDenied as exc:
        text = str(exc)
        findings = repr(getattr(exc, "findings", ""))
        assert token not in text
        assert token not in findings
        assert "***REDACTED***" in text or "***REDACTED***" in findings
    else:  # pragma: no cover
        raise AssertionError("a leaked token must be denied")


# ---------------------------------------------------------------------------
# 17. the publication ledger lives in the source repo, not the HF dataset
# ---------------------------------------------------------------------------

def test_publication_ledger_in_source_repo_not_hf_dataset():
    assert ledger_mod.PUBLICATIONS_LEDGER_PATH == "publications.jsonl"
    assert ledger_mod.LEDGER_PLANE == "source_repo"
    # the ledger is part of the SOURCE-REPO authority plane...
    assert "publications_ledger" in projection_mod.SOURCE_REPO_AUTHORITY_PLANE
    # ...and NEVER one of the HF data-plane tables
    assert "publications" not in projection_mod.HF_DATA_PLANE_TABLES
    assert "publications_ledger" not in projection_mod.HF_DATA_PLANE_TABLES

    # driving to accepted writes the publication to the LEDGER, not to the HF port
    machine, port, ledger = _machine()
    _drive(machine, "accepted")
    run_id = machine.projection.run_id
    assert any(r.get("run_id") == run_id and r.get("published") for r in ledger.records())
    # the HF dataset holds objects/card only -- no publication record
    for rev in port.list_revisions():
        assert "publications.jsonl" not in port.list_paths(rev)


# ---------------------------------------------------------------------------
# 18. rejection reachable from any non-terminal state
# ---------------------------------------------------------------------------

def test_rejection_reachable_from_any_nonterminal_state():
    for state in ("emitted", "validated", "replayed", "draft_rendered",
                  "reviewed", "hf_candidate", "report_pinned"):
        machine, _, _ = _machine()
        _drive(machine, state)
        machine.reject("policy_reject")
        assert machine.state == "rejected"
        # rejected is terminal
        with pytest.raises(promotion_mod.PromotionError):
            machine.reject("again")

    # you cannot reject an accepted run
    machine, _, _ = _machine()
    _drive(machine, "accepted")
    with pytest.raises(promotion_mod.PromotionError):
        machine.reject("too_late")


# ---------------------------------------------------------------------------
# real HF adapter is env-token-backed and never faked green
# ---------------------------------------------------------------------------

def test_real_hf_adapter_is_env_backed_never_faked(monkeypatch):
    # The real adapter is a drop-in HfPort but is NEVER given a fake body: with the
    # huggingface_hub library absent it fails closed with HfUnavailableError rather than
    # silently "succeeding". (Full mock-based behavior lives in test_hf_port_real.py; no
    # test anywhere contacts huggingface.co.) See test_hf_port_real.py for the drop-in
    # end-to-end proof against a mocked hub.
    import sys

    adapter = hf_port_mod.HuggingFaceHubHfPort(repo_id="aceengineer/wed-runs-test")
    assert isinstance(adapter, hf_port_mod.HfPort)
    monkeypatch.setitem(sys.modules, "huggingface_hub", None)  # force ImportError
    with pytest.raises(hf_port_mod.HfUnavailableError):
        adapter.create_commit(objects={}, card=b"")
