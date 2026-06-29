# ABOUTME: run_workflow() entrypoint + registry resolution + ResultLocator for the
# ABOUTME: deterministic workflow API (workspace-hub#3282). Consumes engine(embed=True).
"""Deterministic, in-process workflow runner.

``run_workflow(workflow_id, params=None, cfg=None, verify_reproducible=False)``
returns a typed :class:`~assetutilities.workflow_api.envelope.ResultEnvelope`.

Side-effect-freeness comes entirely from the #3297 embed path:
``engine(cfg=<built cfg>, embed=True, root_folder=tempfile.mkdtemp(), log_to_file=False)``
routes ALL result + log writes under the injected ``root_folder`` and emits no
``.log``. The runner reads + content-hashes the emitted outputs from that tempdir,
then ``shutil.rmtree``s it -- leaving the repo/example dirs byte-for-byte untouched.
This module owns ZERO engine/ApplicationManager edits; it only calls the embed path.
"""

from __future__ import annotations

import copy
import glob
import hashlib
import os
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from assetutilities.common.update_deep import update_deep_dictionary
from assetutilities.workflow_api.envelope import (
    ResultEnvelope,
    compute_reproducible,
    input_hash,
    make_provenance,
    result_hash,
    utc_now_iso,
)

PACKAGE_NAME = "assetutilities"


def _repo_root() -> Path:
    # runner.py -> workflow_api -> assetutilities -> src -> <repo root>
    return Path(__file__).resolve().parents[3]


def registry_path() -> Path:
    return _repo_root() / "docs" / "registry" / "workflows.yaml"


def load_registry() -> dict:
    with open(registry_path()) as fh:
        return yaml.safe_load(fh)


def resolve_registry_row(workflow_id: str) -> dict:
    registry = load_registry()
    for row in registry.get("workflows", []):
        if row.get("id") == workflow_id:
            return row
    raise KeyError(f"unknown workflow_id '{workflow_id}' (not in {registry_path()})")


def lookup_row_for_cfg(cfg: dict) -> dict | None:
    basename = cfg.get("basename")
    if not basename:
        return None
    for row in load_registry().get("workflows", []):
        if row.get("basename") == basename or row.get("id") == basename:
            return row
    return None


def resolve_example_path(rel_input: str) -> Path:
    """Resolve a registry ``input:`` path against the repo root."""
    return _repo_root() / rel_input


@dataclass
class ResultLocator:
    """The per-workflow declared result location (#3282-owned descriptor).

    ``kind: files`` (default) -- outputs are files; discovered by globbing the
    injected embed root (the embed-path file_name is cfg-derived, so the actual
    emitted names differ from the registry's documentary ``outputs:`` names).

    ``kind: in_memory`` -- the payload is ``cfg[key]``. Supported but currently
    unexercised (all registry rows are file-writing).
    """

    kind: str = "files"
    key: str | None = None
    outputs: list = field(default_factory=list)

    @classmethod
    def from_row(cls, row: dict | None) -> "ResultLocator":
        if not row:
            return cls()
        result = row.get("result") or {}
        return cls(
            kind=result.get("kind", "files"),
            key=result.get("key"),
            outputs=list(result.get("outputs", []) or []),
        )

    @classmethod
    def default_for(cls, cfg: dict) -> "ResultLocator":
        return cls()


def extract_result(cfg_base: dict, locator: ResultLocator, root_folder: str):
    """Return ``(payload, warnings)`` for an embed run.

    For ``kind: files`` the ACTUALLY emitted files are discovered by globbing the
    engine-resolved ``result_folder`` under the injected ``root_folder``. The
    ``save_cfg`` cfg-dump ``<file_name>.yml`` (written by ``engine`` into the same
    dir) is EXCLUDED -- it embeds the tempdir abspath + a ``start_time`` datetime
    that would poison the content hash and make ``reproducible`` spuriously False.
    """
    if locator.kind == "in_memory":
        if locator.key not in cfg_base:
            return (
                {"kind": "in_memory", "value": None},
                [f"declared in_memory result key '{locator.key}' absent from cfg"],
            )
        return {"kind": "in_memory", "value": cfg_base[locator.key]}, []

    # kind == "files"
    analysis = cfg_base.get("Analysis", {}) or {}
    results_dir = analysis.get("result_folder") or os.path.join(root_folder, "results")
    # Exclude the save_cfg cfg-dump: its name is exactly <file_name>.yml (same key
    # save_cfg uses at ApplicationManager.save_cfg). Genuine router outputs carry a
    # "_<label>"/"_<column>" suffix, so this never excludes a real output here.
    file_name = analysis.get("file_name", "")
    cfg_dump = os.path.abspath(os.path.join(results_dir, file_name + ".yml"))

    emitted = sorted(
        p
        for p in glob.glob(os.path.join(results_dir, "*"))
        if os.path.isfile(p) and os.path.abspath(p) != cfg_dump
    )

    files, warns = [], []
    for path in emitted:
        with open(path, "rb") as fh:
            digest = hashlib.sha256(fh.read()).hexdigest()
        files.append(
            {
                "basename": os.path.basename(path),
                "sha256": digest,
                "size": os.path.getsize(path),
            }
        )
    if not files:
        warns.append(f"declared kind:files workflow emitted no files under {results_dir}")
    elif locator.outputs and len(files) != len(locator.outputs):
        # Documentary count cross-check only; names are NOT compared (embed
        # file_name != registry CLI-path names).
        warns.append(
            f"emitted {len(files)} files; registry outputs lists {len(locator.outputs)}"
        )
    return {"kind": "files", "outputs": files}, warns


def build_cfg(row: dict, params: dict | None) -> dict:
    """Build the run cfg from a registry row + caller params.

    Starts from the row's ``basename`` + its loaded example ``input``, then
    deep-merges caller ``params`` (params win). The example-load path is a
    convenience for in-repo runs; the example-load-free primary path is
    ``run_workflow(cfg=<full dict>)``.
    """
    cfg: dict = {"basename": row["basename"]}
    input_rel = row.get("input")
    if input_rel:
        example_path = resolve_example_path(input_rel)
        with open(example_path) as fh:
            example_cfg = yaml.safe_load(fh) or {}
        cfg = update_deep_dictionary(cfg, example_cfg)
    if params:
        cfg = update_deep_dictionary(cfg, copy.deepcopy(params))
    return cfg


def _run_once(cfg: dict, locator: ResultLocator):
    """One side-effect-free embed run. Returns ``(payload, warnings, result_hash)``."""
    # Imported here to keep the (~30s cold) engine import off module load.
    from assetutilities.engine import engine

    root = tempfile.mkdtemp(prefix="auwf_")
    try:
        cfg_base = engine(
            cfg=copy.deepcopy(cfg),
            embed=True,
            root_folder=root,
            log_to_file=False,
        )
        payload, warns = extract_result(cfg_base, locator, root)
        rhash = result_hash(payload)
        return payload, warns, rhash
    finally:
        shutil.rmtree(root, ignore_errors=True)


def run_workflow(
    workflow_id: str | None = None,
    params: dict | None = None,
    cfg: dict | None = None,
    verify_reproducible: bool = False,
) -> ResultEnvelope:
    """Run a registry workflow in-process and return a typed ResultEnvelope.

    Fail-closed: an unknown id or a router exception is returned as a
    ``status="error"`` envelope, never raised.
    """
    wid = workflow_id or "(inline-cfg)"
    try:
        if cfg is None:
            row = resolve_registry_row(workflow_id)
            cfg = build_cfg(row, params)
            locator = ResultLocator.from_row(row)
        else:
            cfg = copy.deepcopy(cfg)
            row = lookup_row_for_cfg(cfg)
            locator = ResultLocator.from_row(row) if row else ResultLocator.default_for(cfg)

        ihash = input_hash(cfg)
        payload, warns, rhash = _run_once(cfg, locator)
        repro = compute_reproducible(
            lambda: _run_once(cfg, locator)[2], rhash, verify_reproducible
        )
        return ResultEnvelope(
            workflow_id=wid,
            status="ok",
            result=payload,
            provenance=make_provenance(
                ihash, package_name=PACKAGE_NAME, data_as_of=utc_now_iso()
            ),
            determinism={"result_hash": rhash, "reproducible": repro},
            confidence=None,
            warnings=warns,
        )
    except Exception as exc:  # fail-closed -> error envelope, never a raw traceback
        return ResultEnvelope(
            workflow_id=wid,
            status="error",
            result={},
            provenance=make_provenance(None, package_name=PACKAGE_NAME),
            determinism={"result_hash": None, "reproducible": None},
            confidence=None,
            warnings=[str(exc)],
        )
