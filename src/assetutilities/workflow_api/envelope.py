# ABOUTME: Typed ResultEnvelope + determinism/provenance helpers for the
# ABOUTME: deterministic workflow API (workspace-hub#3282). Stdlib-only, no Pydantic.
"""ResultEnvelope and determinism helpers.

The ``ResultEnvelope`` is the typed contract the whole deterministic-workflow
epic (workspace-hub#3281) exposes. It is a plain stdlib :func:`dataclasses.dataclass`
(NOT Pydantic) so the shared library carries no hard third-party dependency;
serialization is via explicit :meth:`ResultEnvelope.to_dict` /
:meth:`ResultEnvelope.from_dict`.

Determinism fields are COMPUTED, never hardcoded:

- ``input_hash`` -- sha256 over the caller cfg with volatile top-level keys pruned.
- ``result_hash`` -- for ``kind: files`` payloads, a content hash keyed by sorted
  basename (location-independent AND content-sensitive).
- ``reproducible`` -- ``None`` unless an opt-in double-run verification is requested.
- ``provenance.code_version`` -- ``{package_version, git_sha}``, parameterized by
  package so each adopting repo stamps its OWN version (workspace-hub#3287).
"""

from __future__ import annotations

import dataclasses
import datetime
import hashlib
import importlib.metadata
import json
import os
import subprocess
from dataclasses import dataclass, field

# Volatile top-level cfg keys excluded from input_hash: they carry absolute
# paths, resolved folders, timestamps, and per-run scaffolding that would make
# the hash location-/time-dependent without reflecting a real input change.
VOLATILE_TOP_KEYS = {"Analysis", "default", "cfg_array"}


def _sha256_hexdigest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _git_sha_or_none() -> str | None:
    """Best-effort ``git rev-parse HEAD`` for the package source tree.

    Returns ``None`` when git is unavailable or the source is not a checkout
    (e.g. installed from a wheel). Never raises.
    """
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=here,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if out.returncode == 0:
            sha = out.stdout.strip()
            return sha or None
    except Exception:
        return None
    return None


def code_version(package_name: str = "assetutilities") -> dict:
    """Return ``{package_version, git_sha}`` for ``package_name``.

    Parameterized so each adopting repo stamps its own version
    (workspace-hub#3287): a hardcoded "assetutilities" would make an assethold
    or digitalmodel envelope report the wrong package version. Both keys are
    always present; ``git_sha`` may be ``None``.
    """
    try:
        pkg_version = importlib.metadata.version(package_name)
    except Exception:
        pkg_version = None
    return {"package_version": pkg_version, "git_sha": _git_sha_or_none()}


def make_provenance(
    input_hash_value: str | None,
    *,
    package_name: str = "assetutilities",
    standard_revisions: list | None = None,
    data_as_of: str | None = None,
) -> dict:
    """Assemble the ``provenance`` block for an envelope."""
    return {
        "code_version": code_version(package_name),
        "standard_revisions": list(standard_revisions or []),
        "data_as_of": data_as_of,
        "input_hash": input_hash_value,
    }


def canonical_input(cfg: dict) -> str:
    """Canonical JSON of the caller cfg with volatile top-level keys pruned."""
    pruned = {k: v for k, v in cfg.items() if k not in VOLATILE_TOP_KEYS}
    return json.dumps(pruned, sort_keys=True, default=str)


def input_hash(cfg: dict) -> str:
    """Content hash of the non-volatile input cfg."""
    return _sha256_hexdigest(canonical_input(cfg))


def result_hash(payload: dict) -> str:
    """Hash a standardized result payload.

    For ``kind == "files"`` the canonical form is ``sorted((basename, sha256))``
    over the per-file content digests already computed by ``extract_result``.
    This is location-independent (the throwaway tempdir abspath is dropped) AND
    content-sensitive (a changed output byte flips a per-file ``sha256`` and so
    the overall hash). For any other ``kind`` the payload itself is hashed.
    """
    if payload.get("kind") == "files":
        canon = {
            "kind": "files",
            "files": sorted(
                (f["basename"], f["sha256"]) for f in payload.get("outputs", [])
            ),
        }
    else:
        canon = payload
    return _sha256_hexdigest(json.dumps(canon, sort_keys=True, default=str))


def compute_reproducible(rerun_fn, first_hash: str, verify: bool) -> bool | None:
    """Opt-in determinism check.

    ``verify=False`` returns ``None`` ("not checked") -- an honest default, never
    a fabricated ``True``. ``verify=True`` runs ``rerun_fn`` (a fresh embed run in
    its OWN root_folder) and compares the measured content hashes.
    """
    if not verify:
        return None
    second_hash = rerun_fn()
    return second_hash == first_hash


@dataclass
class ResultEnvelope:
    """Typed, side-effect-free result of an in-process workflow run."""

    workflow_id: str
    status: str  # "ok" | "error"
    result: dict
    provenance: dict
    determinism: dict
    confidence: dict | None = None
    warnings: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ResultEnvelope":
        return cls(
            workflow_id=data["workflow_id"],
            status=data["status"],
            result=data.get("result", {}),
            provenance=data.get("provenance", {}),
            determinism=data.get("determinism", {}),
            confidence=data.get("confidence"),
            warnings=list(data.get("warnings", [])),
        )


def utc_now_iso() -> str:
    """Timestamp helper for ``provenance.data_as_of`` (UTC, second precision)."""
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
