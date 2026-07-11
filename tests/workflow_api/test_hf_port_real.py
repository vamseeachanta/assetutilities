# ABOUTME: TDD tests for the REAL env-token-backed huggingface_hub adapter
# ABOUTME: (workspace-hub#3433). huggingface_hub is MOCKED via sys.modules; no test here
# ABOUTME: ever contacts huggingface.co or publishes anything.
"""Mock-only tests for :class:`HuggingFaceHubHfPort`.

These prove the real adapter is a drop-in :class:`HfPort` -- it maps to
``huggingface_hub.HfApi.create_commit`` (dataset repo, ``exist_ok`` create_repo),
returns the EXACT hub-reported commit oid, pins ``hf_hub_download`` to an exact
revision, classifies transient vs auth vs missing faults onto the port taxonomy,
fails closed with :class:`HfUnavailableError` when the library is absent, and never
holds/echoes a token.

How ``huggingface_hub`` is mocked: :func:`_make_fake_hub` builds a stand-in
``types.ModuleType('huggingface_hub')`` exposing ``HfApi`` (records every
``create_repo`` / ``create_commit`` / ``list_*`` kwargs), ``CommitOperationAdd``
(captures ``path_in_repo`` / ``path_or_fileobj``), and ``hf_hub_download`` (records
kwargs, returns bytes from an in-test ``store`` written to a throwaway temp file). Each
test injects it with ``monkeypatch.setitem(sys.modules, 'huggingface_hub', fake)`` so the
adapter's LAZY ``from huggingface_hub import ...`` resolves to the fake. NO network.
"""

from __future__ import annotations

import hashlib
import os
import sys
import tempfile
import types

import pytest

from assetutilities.workflow_api import artifact, identity, inputs, metrics
from assetutilities.workflow_api import output_contract as oc
from assetutilities.workflow_api.publication import (
    egress as egress_mod,
    hf_port as hf_port_mod,
    ledger as ledger_mod,
    projection as projection_mod,
    promotion as promotion_mod,
)


REPO = "aceengineer/wed-runs-test"
OBJ_BYTES = b'{"basin": "permian", "wells": 3}'
OBJ_DIGEST = hashlib.sha256(OBJ_BYTES).hexdigest()
CARD_BYTES = b"# dataset card\n"
FAKE_OID = "a" * 40  # 40-hex so promotion's is_exact_revision() accepts it


# ---------------------------------------------------------------------------
# the huggingface_hub mock
# ---------------------------------------------------------------------------

class _FakeCommitInfo:
    """Stand-in for huggingface_hub.CommitInfo -- only ``.oid`` is read by the adapter."""

    def __init__(self, oid):
        self.oid = oid


class _FakeCommitOperationAdd:
    def __init__(self, *, path_in_repo, path_or_fileobj):
        self.path_in_repo = path_in_repo
        self.path_or_fileobj = path_or_fileobj


class _FakeHTTPError(Exception):
    """Stand-in for huggingface_hub.utils.HfHubHTTPError (carries ``.response.status_code``)."""

    def __init__(self, status_code):
        super().__init__(f"HTTP {status_code}")
        self.response = types.SimpleNamespace(status_code=status_code)


def _make_fake_hub(
    *,
    oid=FAKE_OID,
    store=None,
    create_repo_exc=None,
    create_commit_exc=None,
    download_exc=None,
):
    """Return ``(fake_module, record)``.

    ``store`` maps ``filename -> bytes`` for ``hf_hub_download``. ``record`` captures every
    call's kwargs so tests can assert repo_type/exist_ok/revision/operations passthrough.
    """
    store = store if store is not None else {}
    record = {
        "api_init": None,
        "create_repo_calls": [],
        "create_commit_calls": [],
        "download_calls": [],
    }

    class _FakeHfApi:
        def __init__(self, *args, **kwargs):
            record["api_init"] = (args, kwargs)

        def create_repo(self, **kwargs):
            record["create_repo_calls"].append(kwargs)
            if create_repo_exc is not None:
                raise create_repo_exc
            return types.SimpleNamespace(**kwargs)

        def create_commit(self, **kwargs):
            record["create_commit_calls"].append(kwargs)
            if create_commit_exc is not None:
                raise create_commit_exc
            return _FakeCommitInfo(oid)

        def list_repo_files(self, **kwargs):
            return list(store.keys())

        def list_repo_commits(self, **kwargs):
            return [types.SimpleNamespace(commit_id=oid)]

    def _hf_hub_download(**kwargs):
        record["download_calls"].append(kwargs)
        if download_exc is not None:
            raise download_exc
        data = store[kwargs["filename"]]
        fd, path = tempfile.mkstemp(prefix="fake-hf-")
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        return path

    module = types.ModuleType("huggingface_hub")
    module.HfApi = _FakeHfApi
    module.CommitOperationAdd = _FakeCommitOperationAdd
    module.hf_hub_download = _hf_hub_download
    return module, record


def _install(monkeypatch, module):
    monkeypatch.setitem(sys.modules, "huggingface_hub", module)


# ---------------------------------------------------------------------------
# 1. interface conformance
# ---------------------------------------------------------------------------

def test_real_port_conforms_to_hfport_interface():
    port = hf_port_mod.HuggingFaceHubHfPort(repo_id=REPO)
    assert isinstance(port, hf_port_mod.HfPort)
    for name in ("create_commit", "fetch_object", "fetch_card", "list_objects", "list_revisions"):
        assert callable(getattr(port, name)), name
    # same public method surface as the abstract port + the in-memory fake
    abstract = {m for m in dir(hf_port_mod.HfPort) if not m.startswith("_")}
    assert abstract <= set(dir(port))


# ---------------------------------------------------------------------------
# 2. exact captured revision
# ---------------------------------------------------------------------------

def test_create_commit_returns_captured_revision(monkeypatch):
    module, record = _make_fake_hub(oid="c" * 40)
    _install(monkeypatch, module)
    port = hf_port_mod.HuggingFaceHubHfPort(repo_id=REPO)
    revision = port.create_commit(objects={OBJ_DIGEST: OBJ_BYTES}, card=CARD_BYTES)
    assert revision == "c" * 40  # verbatim from the hub-reported CommitInfo.oid
    assert len(record["create_commit_calls"]) == 1


# ---------------------------------------------------------------------------
# 3. dataset repo_type + create_repo(exist_ok=True) + operations
# ---------------------------------------------------------------------------

def test_create_commit_uses_dataset_repo_type_and_create_repo_exist_ok(monkeypatch):
    module, record = _make_fake_hub()
    _install(monkeypatch, module)
    port = hf_port_mod.HuggingFaceHubHfPort(repo_id=REPO, private=True)
    port.create_commit(objects={OBJ_DIGEST: OBJ_BYTES}, card=CARD_BYTES)

    (repo_kwargs,) = record["create_repo_calls"]
    assert repo_kwargs["repo_type"] == "dataset"
    assert repo_kwargs["exist_ok"] is True
    assert repo_kwargs["private"] is True
    assert repo_kwargs["repo_id"] == REPO

    (commit_kwargs,) = record["create_commit_calls"]
    assert commit_kwargs["repo_type"] == "dataset"
    assert commit_kwargs["repo_id"] == REPO
    paths = {op.path_in_repo for op in commit_kwargs["operations"]}
    assert artifact.storage_locator_for(OBJ_DIGEST) in paths  # content-addressed object path
    assert hf_port_mod.CARD_PATH in paths  # dataset card


# ---------------------------------------------------------------------------
# 4. fetch pins the exact revision + returns bytes
# ---------------------------------------------------------------------------

def test_fetch_object_pins_exact_revision(monkeypatch):
    obj_path = artifact.storage_locator_for(OBJ_DIGEST)
    store = {obj_path: OBJ_BYTES, hf_port_mod.CARD_PATH: CARD_BYTES}
    module, record = _make_fake_hub(store=store)
    _install(monkeypatch, module)
    port = hf_port_mod.HuggingFaceHubHfPort(repo_id=REPO)

    revision = "d" * 40
    data = port.fetch_object(revision, OBJ_DIGEST)
    assert data == OBJ_BYTES

    (call,) = record["download_calls"]
    assert call["revision"] == revision  # exact revision passed through -- no re-resolution
    assert call["repo_type"] == "dataset"
    assert call["filename"] == obj_path

    # the card path is also pinned to the same exact revision
    assert port.fetch_card(revision) == CARD_BYTES
    assert record["download_calls"][1]["revision"] == revision
    assert record["download_calls"][1]["filename"] == hf_port_mod.CARD_PATH


# ---------------------------------------------------------------------------
# 5. transient network / 5xx faults -> HfTransientError
# ---------------------------------------------------------------------------

def test_transient_network_error_maps_to_HfTransientError(monkeypatch):
    # 5xx on commit
    module, _ = _make_fake_hub(create_commit_exc=_FakeHTTPError(503))
    _install(monkeypatch, module)
    port = hf_port_mod.HuggingFaceHubHfPort(repo_id=REPO)
    with pytest.raises(hf_port_mod.HfTransientError):
        port.create_commit(objects={OBJ_DIGEST: OBJ_BYTES}, card=CARD_BYTES)

    # a bare connection reset on download (no status code) is also transient
    module2, _ = _make_fake_hub(download_exc=ConnectionError("connection reset by peer"))
    _install(monkeypatch, module2)
    port2 = hf_port_mod.HuggingFaceHubHfPort(repo_id=REPO)
    with pytest.raises(hf_port_mod.HfTransientError):
        port2.fetch_object("d" * 40, OBJ_DIGEST)


# ---------------------------------------------------------------------------
# 6. auth / permission (401/403) -> HfError (NOT transient)
# ---------------------------------------------------------------------------

def test_auth_or_permission_error_maps_to_HfError(monkeypatch):
    for code in (401, 403):
        module, _ = _make_fake_hub(create_commit_exc=_FakeHTTPError(code))
        _install(monkeypatch, module)
        port = hf_port_mod.HuggingFaceHubHfPort(repo_id=REPO)
        with pytest.raises(hf_port_mod.HfError) as info:
            port.create_commit(objects={OBJ_DIGEST: OBJ_BYTES}, card=CARD_BYTES)
        assert not isinstance(info.value, hf_port_mod.HfTransientError)
        assert not isinstance(info.value, hf_port_mod.HfUnavailableError)

    # a 404 (missing object) maps to HfUnavailableError
    module404, _ = _make_fake_hub(download_exc=_FakeHTTPError(404))
    _install(monkeypatch, module404)
    port404 = hf_port_mod.HuggingFaceHubHfPort(repo_id=REPO)
    with pytest.raises(hf_port_mod.HfUnavailableError):
        port404.fetch_object("d" * 40, OBJ_DIGEST)


# ---------------------------------------------------------------------------
# 7. missing huggingface_hub -> HfUnavailableError
# ---------------------------------------------------------------------------

def test_missing_huggingface_hub_import_raises_unavailable(monkeypatch):
    # sys.modules[name] = None makes `import huggingface_hub` raise ImportError.
    monkeypatch.setitem(sys.modules, "huggingface_hub", None)
    port = hf_port_mod.HuggingFaceHubHfPort(repo_id=REPO)
    with pytest.raises(hf_port_mod.HfUnavailableError):
        port.create_commit(objects={OBJ_DIGEST: OBJ_BYTES}, card=CARD_BYTES)
    with pytest.raises(hf_port_mod.HfUnavailableError):
        port.fetch_object("d" * 40, OBJ_DIGEST)
    with pytest.raises(hf_port_mod.HfUnavailableError):
        port.fetch_card("d" * 40)


# ---------------------------------------------------------------------------
# 8. token never leaks into repr / returned records / hub call args
# ---------------------------------------------------------------------------

def test_token_never_appears_in_repr_or_returned_records(monkeypatch):
    secret = "hf" + "_" + "SUPERSECRET_TOKEN_value_0123456789"
    monkeypatch.setenv("HF_TOKEN", secret)
    obj_path = artifact.storage_locator_for(OBJ_DIGEST)
    store = {obj_path: OBJ_BYTES, hf_port_mod.CARD_PATH: CARD_BYTES}
    module, record = _make_fake_hub(oid="e" * 40, store=store)
    _install(monkeypatch, module)
    port = hf_port_mod.HuggingFaceHubHfPort(repo_id=REPO)

    assert secret not in repr(port)
    assert secret not in str(vars(port))  # token is never stored on the instance

    revision = port.create_commit(objects={OBJ_DIGEST: OBJ_BYTES}, card=CARD_BYTES)
    assert secret not in revision

    # the adapter never passes the token explicitly -- huggingface_hub reads it from env.
    init_args, init_kwargs = record["api_init"]
    assert secret not in str(init_args) and secret not in str(init_kwargs)
    for call in record["create_repo_calls"] + record["create_commit_calls"] + record["download_calls"]:
        assert secret not in str(call)


# ---------------------------------------------------------------------------
# 9. the promotion machine runs end-to-end with the REAL adapter (hub mocked)
# ---------------------------------------------------------------------------

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


def _build_projection():
    input_records = [_input_record()]
    outputs = [
        oc.make_output_record(
            role="primary",
            native_schema={"id": "gasfield-out", "version": "1"},
            media_type="application/json",
            curated_label="primary_result",
            artifact_refs=[OBJ_DIGEST],
        )
    ]
    store = metrics.MetricDefinitionStore()
    ident = identity.derive_run_identity(**_identity_context(input_records))
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
    observation = metrics.make_metric_observation(
        definition=definition,
        run_id=ident["run_id"],
        value=1,
        quality_state="valid",
        derivation_evidence={"from": "primary"},
    )
    return projection_mod.build_projection(
        identity_context=_identity_context(input_records),
        input_records=input_records,
        artifacts=[
            artifact.physical_artifact(
                OBJ_BYTES,
                media_type="application/json",
                native_format="json",
                license_evidence_ref=_PUBLIC_EVIDENCE,
            )
        ],
        outputs=outputs,
        output_equality_digest=oc.output_equality_digest(outputs),
        metric_observations=[observation],
        object_bytes={OBJ_DIGEST: OBJ_BYTES},
        terminal_status="succeeded",
        metric_store=store,
        evidence={"envelope_input_hash": "e" * 64},
    )


def _drive_to_accepted(machine):
    machine.validate()
    machine.replay()
    machine.render_draft()
    machine.review(
        human_promotion_review={"approved": True, "reviewer": "vp"},
        adversarial_artifact_review={"approved": True, "reviewer": "red-team"},
    )
    machine.promote_to_hf_candidate()
    machine.pin_report()
    machine.accept()


def test_promotion_machine_runs_end_to_end_with_a_faked_real_port(monkeypatch):
    projection = _build_projection()
    # the fake hub must serve back exactly the bytes the machine re-hashes post-upload
    store = {hf_port_mod.CARD_PATH: bytes(projection.dataset_card())}
    for digest, blob in projection.object_bytes.items():
        store[artifact.storage_locator_for(digest)] = bytes(blob)
    module, record = _make_fake_hub(oid=FAKE_OID, store=store)
    _install(monkeypatch, module)

    port = hf_port_mod.HuggingFaceHubHfPort(repo_id=REPO)  # REAL adapter, hub mocked
    machine = promotion_mod.PromotionMachine(
        projection,
        hf_port=port,
        ledger=ledger_mod.Ledger(),
        egress=egress_mod.EgressGate(env_tokens={}),
    )
    _drive_to_accepted(machine)

    assert machine.state == "accepted"
    assert machine.candidate_revision == FAKE_OID  # exact hub oid flowed through the machine
    assert len(record["create_commit_calls"]) == 1  # exactly one real commit, no overwrite
    assert record["download_calls"]  # post-upload re-hash actually fetched via the adapter
