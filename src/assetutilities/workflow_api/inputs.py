# ABOUTME: Replayable public input + source-snapshot contract (workspace-hub#3430):
# ABOUTME: six closed input kinds, fail-closed admission, snapshot identity via #3428/#3429.
"""Replayable inputs and the source-snapshot admission contract.

This module implements the on-main
``docs/architecture/algorithm-run-dataset-contract.yaml`` ``records.input`` record
and ``public_input_policy`` block. It builds the Input RECORD + admission layer on
top of the identity and artifact contracts and is stdlib-only (it depends only on
:mod:`identity` and :mod:`artifact`, which are themselves stdlib-only).

Design invariants (from the approved+remediated #3430 plan):

- **Six closed input kinds.** ``parameter_set``, ``configuration_document``,
  ``dataset_snapshot``, ``public_external_resource``, ``upstream_run_reference``,
  ``artifact_reference``. API-backed inputs are classified as ``dataset_snapshot``
  (there is NO separate ``api`` kind). Any other kind fails closed.
- **Snapshot identity excludes fetch-volatile fields.** A dataset input's
  identity-bearing ``source_snapshot`` digest is derived over EXACTLY
  ``{source_authority, public_locator, data_as_of, selection, snapshot_identity}``
  and EXCLUDES ``retrieval_time`` and ``redistribution_evidence`` -- so re-fetching
  the same pinned snapshot never moves ``run_id`` (see
  :func:`snapshot_identity_subset`). Canonically-equivalent JSON/YAML/config yield
  one identity because :mod:`identity` owns canonicalization.
- **Fail-closed admission.** :func:`admission_reason` returns the FIRST matching
  contract ``rejection_reason`` (``restricted``, ``pointer_only``,
  ``ambiguous_license`` -- incl. unknown/absent license, ``mutable_unpinned``,
  ``unhashed``, ``schema_invalid``, ``incomplete``, ``private``, ``path_leaking``);
  absolute local paths are forbidden. The OPERATIVE "pinned snapshot" predicate is
  (``snapshot_identity`` byte-digest present AND versioned ``public_locator``); a
  ``data_as_of == retrieval_time`` (run-timestamp) case fails because it lacks a
  snapshot identity -- the missing snapshot is the RULE, timestamp-equality only the
  symptom.
- **Replay durability.** A replay-critical input's BYTES must be MATERIALIZED --
  a content-addressed HF object (via #3429 ``content_digest``) or an embedded
  ``canonical_repr``. A stable public locator is PROVENANCE, not the reconstruction
  source; a locator-only replay-critical input is rejected ``pointer_only``.
- **Identity is minted THROUGH :mod:`identity`.** :func:`input_record_id` maps a
  record onto identity's seven required ``input_record_id`` components and calls
  :func:`identity.input_record_id`; :func:`canonical_input_set_digest` calls
  :func:`identity.input_set_id`. Digests are never re-derived here.
- **parameter_set vs execution_parameters.** ``parameter_set`` inputs are replay
  DATA (they flow through the input-set digest); ``execution_parameters`` are
  run-control knobs (a #3428 ``run_id`` component). A key belongs to exactly one
  side (:func:`check_no_parameter_double_count`).
"""

from __future__ import annotations

import re

from assetutilities.workflow_api import artifact, identity

# ---- the six closed input kinds (verbatim from the on-main contract) --------
INPUT_KINDS = frozenset({
    "parameter_set",
    "configuration_document",
    "dataset_snapshot",
    "public_external_resource",
    "upstream_run_reference",
    "artifact_reference",
})

# API-backed inputs are classified as dataset_snapshot -- there is no `api` kind.
_KIND_ALIASES = {"api": "dataset_snapshot"}

# Kinds that pull external public data and must record the source snapshot.
SNAPSHOT_KINDS = frozenset({"dataset_snapshot", "public_external_resource"})
# Kinds whose bytes are embedded inline (materialized as their canonical repr).
EMBEDDED_KINDS = frozenset({"parameter_set", "configuration_document"})
# Kinds that reference an already-immutable, content-addressed object / run.
REFERENCE_KINDS = frozenset({"upstream_run_reference", "artifact_reference"})

# allowed_replay_locations (verbatim from public_input_policy).
ALLOWED_REPLAY_LOCATIONS = frozenset({
    "content_addressed_dataset_object",
    "stable_public_uri_with_immutable_digest",
    "accepted_upstream_public_run",
})

# rejection_reasons (verbatim from public_input_policy).
REJECTION_REASONS = frozenset({
    "restricted",
    "pointer_only",
    "ambiguous_license",
    "mutable_unpinned",
    "unhashed",
    "schema_invalid",
    "incomplete",
    "private",
    "path_leaking",
})

# The five identity-bearing snapshot fields (EXCLUDES retrieval_time +
# redistribution_evidence, which are fetch-volatile evidence).
SNAPSHOT_IDENTITY_FIELDS = (
    "source_authority",
    "public_locator",
    "data_as_of",
    "selection",
    "snapshot_identity",
)

# Domain-separation type for the source-snapshot sub-identity.
SOURCE_SNAPSHOT_ID_TYPE = "input_source_snapshot"

# redistribution_rights tokens that are non-redistributable -> `restricted`.
_RESTRICTED_RIGHTS = frozenset(
    {"restricted", "non_redistributable", "client_specific", "forbidden"}
)
# redistribution_rights tokens that are ambiguous/unknown -> `ambiguous_license`.
_AMBIGUOUS_RIGHTS = frozenset({"ambiguous", "unknown", ""})


class InputError(ValueError):
    """Raised when an input record violates the replayable-input contract."""


class AdmissionError(InputError):
    """Raised (fail-closed) when an input is not admissible. Carries ``reason``."""

    def __init__(self, reason: str, message: str | None = None):
        self.reason = reason
        super().__init__(message or f"input rejected: {reason}")


# ---------------------------------------------------------------------------
# kind classification (closed enum)
# ---------------------------------------------------------------------------

def classify_kind(kind) -> str:
    """Return the canonical input kind, mapping ``api`` -> ``dataset_snapshot``.

    Raises :class:`InputError` for any kind outside the six closed kinds.
    """
    canonical = _KIND_ALIASES.get(kind, kind)
    if canonical not in INPUT_KINDS:
        raise InputError(
            f"unknown input kind {kind!r}; the closed set is {sorted(INPUT_KINDS)}"
        )
    return canonical


# ---------------------------------------------------------------------------
# record construction
# ---------------------------------------------------------------------------

def make_input(
    *,
    kind,
    role,
    schema_version,
    required_for_replay=True,
    canonical_repr=None,
    content_digest=None,
    replay_location=None,
    redistribution_rights=None,
    redistribution_evidence=None,
    residency="public",
    transformation_id="identity",
    # dataset/snapshot provenance:
    source_authority=None,
    public_locator=None,
    data_as_of=None,
    retrieval_time=None,
    selection=None,
    snapshot_identity=None,
) -> dict:
    """Build an Input record (classifying ``kind``); admission is applied lazily.

    ``kind`` is validated against the six closed kinds (``api`` ->
    ``dataset_snapshot``). Every other field is stored verbatim; identity is
    minted later via :func:`input_record_id` and durability/rights are enforced by
    :func:`admit`. Embedded kinds default ``redistribution_rights`` to ``owned``.
    """
    kind = classify_kind(kind)
    if kind in EMBEDDED_KINDS and redistribution_rights is None:
        redistribution_rights = "owned"
    return {
        "kind": kind,
        "role": role,
        "schema_version": schema_version,
        "required_for_replay": required_for_replay,
        "canonical_repr": canonical_repr,
        "content_digest": content_digest,
        "replay_location": replay_location,
        "redistribution_rights": redistribution_rights,
        "redistribution_evidence": redistribution_evidence,
        "residency": residency,
        "transformation_id": transformation_id,
        "source_authority": source_authority,
        "public_locator": public_locator,
        "data_as_of": data_as_of,
        "retrieval_time": retrieval_time,
        "selection": selection,
        "snapshot_identity": snapshot_identity,
    }


# ---------------------------------------------------------------------------
# path-leak detection (absolute local paths forbidden)
# ---------------------------------------------------------------------------

_WIN_DRIVE_RE = re.compile(r"^[A-Za-z]:[\\/]")


def _is_abs_local_path(value) -> bool:
    """True if ``value`` is (or embeds) an absolute local / home / UNC path.

    A proper remote URL (``https://``, ``s3://``, ``hf://`` ...) is NOT a leak; a
    ``file:`` URI, a ``/``- or ``~``-rooted path, a backslash/UNC path or a Windows
    drive path IS.
    """
    if not isinstance(value, str) or not value:
        return False
    if value.startswith("file:"):
        return True
    if "://" in value:
        return False  # a non-file remote URL scheme
    if value.startswith("/") or value.startswith("~"):
        return True
    if "\\" in value:
        return True
    if _WIN_DRIVE_RE.match(value):
        return True
    return False


def _iter_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from _iter_strings(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            yield from _iter_strings(v)


def _has_path_leak(rec) -> bool:
    for field in ("public_locator", "canonical_repr", "selection",
                  "source_authority", "replay_location"):
        for text in _iter_strings(rec.get(field)):
            if _is_abs_local_path(text):
                return True
    return False


# ---------------------------------------------------------------------------
# snapshot / materialization predicates
# ---------------------------------------------------------------------------

def _locator_uri(locator):
    if isinstance(locator, dict):
        return locator.get("uri")
    return locator


def _locator_versioned(locator) -> bool:
    """A public locator is versioned/immutable when it pins a version or digest."""
    if isinstance(locator, dict):
        return bool(locator.get("version") or locator.get("immutable_digest"))
    if isinstance(locator, str):
        return "@" in locator  # e.g. "hf://ds/wells@sha256:..."
    return False


def _snapshot_pinned(rec) -> bool:
    """OPERATIVE pinned-snapshot predicate: byte snapshot identity AND versioned locator."""
    return bool(rec.get("snapshot_identity")) and _locator_versioned(rec.get("public_locator"))


def _content_hash(rec):
    """The record's content hash: content_digest, embedded-repr digest, or snapshot id.

    An artifact ``content_digest`` (via #3429) or an embedded ``canonical_repr``
    (hashed through :func:`artifact.structured_object_digest`, reusing the single
    canonicalization owner) is a materialized byte hash; a bare ``snapshot_identity``
    is a locator/provenance hash (not materialized bytes).
    """
    if rec.get("content_digest"):
        return rec["content_digest"]
    if rec.get("canonical_repr") is not None:
        return artifact.structured_object_digest(rec["canonical_repr"])
    if rec.get("snapshot_identity"):
        return rec["snapshot_identity"]
    return None


def _materialized(rec) -> bool:
    """Replay bytes are materialized (content-addressed HF object or embedded repr)."""
    return bool(rec.get("content_digest")) or rec.get("canonical_repr") is not None


# ---------------------------------------------------------------------------
# fail-closed admission
# ---------------------------------------------------------------------------

def admission_reason(rec) -> str | None:
    """Return the FIRST contract ``rejection_reason`` for ``rec``, or ``None`` if admissible.

    Fail-closed: order is deterministic so each rejection has a single stable reason.
    """
    kind = rec["kind"]
    rights = rec.get("redistribution_rights")

    if _has_path_leak(rec):
        return "path_leaking"

    schema_version = rec.get("schema_version")
    if not schema_version or not isinstance(schema_version, str):
        return "schema_invalid"

    if rec.get("residency") == "private":
        return "private"

    if rights in _RESTRICTED_RIGHTS:
        return "restricted"
    if rights is None or rights in _AMBIGUOUS_RIGHTS:
        return "ambiguous_license"

    # external public snapshots must be pinned to an immutable byte-snapshot.
    if kind in SNAPSHOT_KINDS and not _snapshot_pinned(rec):
        return "mutable_unpinned"

    if _content_hash(rec) is None:
        return "unhashed"

    # replay-critical bytes must be MATERIALIZED; a locator alone is provenance.
    if rec.get("required_for_replay", True) and not _materialized(rec):
        return "pointer_only"

    if rec.get("replay_location") not in ALLOWED_REPLAY_LOCATIONS:
        return "incomplete"
    if kind in SNAPSHOT_KINDS and not (rec.get("source_authority") and rec.get("data_as_of")):
        return "incomplete"
    return None


def admit(rec) -> dict:
    """Return ``rec`` if admissible, else raise :class:`AdmissionError` (fail-closed)."""
    reason = admission_reason(rec)
    if reason is not None:
        raise AdmissionError(reason, f"input {rec.get('kind')!r} rejected: {reason}")
    return rec


# ---------------------------------------------------------------------------
# snapshot identity + record/set identity (minted THROUGH the identity module)
# ---------------------------------------------------------------------------

def snapshot_identity_subset(rec) -> dict:
    """The identity-bearing snapshot subset (EXCLUDES retrieval_time + evidence)."""
    return {field: rec.get(field) for field in SNAPSHOT_IDENTITY_FIELDS}


def _source_snapshot_token(rec) -> str:
    """The ``source_snapshot`` identity component for a record.

    For snapshot kinds this is the domain-separated digest of the identity-bearing
    subset (via :func:`identity.canonical_digest`); for reference/embedded kinds the
    materialized content hash IS the source.
    """
    if rec["kind"] in SNAPSHOT_KINDS:
        return identity.canonical_digest(SOURCE_SNAPSHOT_ID_TYPE, snapshot_identity_subset(rec))
    return _content_hash(rec)


def _record_components(rec) -> dict:
    """Map an admitted record onto identity's seven ``input_record_id`` components."""
    return {
        "role": rec["role"],
        "native_schema_version": rec["schema_version"],
        "source_snapshot": _source_snapshot_token(rec),
        "transformation_id": rec.get("transformation_id") or "identity",
        "artifact_sha256": _content_hash(rec),
        "redistribution_rights": rec["redistribution_rights"],
        "complete_replay_location": rec["replay_location"],
    }


def input_record_id(rec) -> str:
    """Admit ``rec`` then mint its ``input_record_id`` via :func:`identity.input_record_id`."""
    admit(rec)
    return identity.input_record_id(_record_components(rec))


def canonical_input_set_digest(records) -> str:
    """Admit every record and mint the ``input_set_id`` over ``(role, input_record_id)``.

    Delegates to :func:`identity.input_set_id`, which sorts pairs so the set identity
    is order-independent. Canonically-equivalent inputs collapse to one identity.
    """
    pairs = [(rec["role"], input_record_id(rec)) for rec in records]
    return identity.input_set_id(pairs)


# ---------------------------------------------------------------------------
# parameter_set vs execution_parameters (cross-plan with #3428)
# ---------------------------------------------------------------------------

def check_no_parameter_double_count(parameter_set_records, execution_parameters) -> bool:
    """Assert no key is BOTH a parameter_set input and an execution_parameter.

    ``parameter_set`` inputs are replay DATA (they flow through the input-set digest);
    ``execution_parameters`` are #3428 run-control knobs. A key belongs to exactly one
    side; an overlap raises :class:`InputError`.
    """
    param_keys: set = set()
    for rec in parameter_set_records:
        if rec.get("kind") != "parameter_set":
            continue
        repr_ = rec.get("canonical_repr")
        if isinstance(repr_, dict):
            param_keys |= set(repr_)
    overlap = param_keys & set(execution_parameters or {})
    if overlap:
        raise InputError(
            "keys counted on BOTH the parameter_set (replay data) and "
            f"execution_parameters (run-control) sides: {sorted(overlap)}"
        )
    return True
