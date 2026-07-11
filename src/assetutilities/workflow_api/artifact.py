# ABOUTME: Content-addressed artifact + HF-residency contract (workspace-hub#3429):
# ABOUTME: byte-intrinsic SHA-256 identity, integrity-from-bytes, projection-time residency.
"""Content-addressed artifacts and Hugging Face residency projection.

This module implements the on-main
``docs/architecture/algorithm-run-dataset-contract.yaml`` ``artifact`` record --
``identity: content_digest``, ``residency:
content_addressed_hf_object_or_explicit_exclusion``, ``dataset_table: artifacts``.
It is stdlib-only (``hashlib``, ``json`` via :mod:`identity`) to keep the shared
library dependency-free, matching :mod:`envelope` and :mod:`identity`.

Design invariants (from the approved+remediated #3429 plan):

- **Physical-byte artifact.** ``content_digest = sha256(exact immutable STORED
  bytes)`` -- TRUE content addressing: this is exactly what a publisher re-hashes
  from the object on disk. ``compression`` is PURELY DESCRIPTIVE metadata and
  MUST NEVER trigger decode-before-hash (hashing "decoded" bytes is a rejected
  design). ``size_bytes`` is the stored byte length.
- **Structured-object artifact.** ``content_digest`` is derived through
  :func:`identity.canonical_digest` over :func:`identity.canonicalize` (the single
  JCS canonical-serialization owner), reusing identity's domain-separation
  convention. Two key-orderings of one object -> one digest.
- **Role-free identity.** The Artifact record carries ONLY byte-intrinsic fields
  (``content_digest, size_bytes, media_type, native_format, compression,
  schema_ref, storage_locator, license_evidence_ref``). Residency ``class``/role/
  ``eligible`` live on the referencing Input/Output record, never here. Identical
  bytes -> ONE artifact record regardless of how many runs/roles reference it.
- **Integrity-from-bytes.** A reader re-hashes the object's actual bytes and
  REJECTS any manifest-asserted digest that disagrees -- bytes win, the manifest
  is untrusted (:func:`verify_integrity`).
- **Storage-locator safety.** :func:`validate_storage_locator` rejects absolute
  paths / ``~`` home / UNC (``\\``) / ``..`` traversal and enforces
  ``storage_locator == "objects/" + content_digest[:2] + "/" + content_digest``.
- **Residency / exclusion.** Eligibility is computed AT PROJECTION TIME as
  (byte-intrinsic license evidence) x (per-reference role)
  (:func:`project_reference_residency`), never stamped on the record. Excluded
  roles (transient logs / caches / large regenerable dumps) get a VISIBLE
  ``class: excluded`` marker, never silent omission. A dataset-level license can
  NEVER grant rights absent from a specific artifact's ``license_evidence_ref``.
"""

from __future__ import annotations

import hashlib

from assetutilities.workflow_api import identity

# The residency contract value from the on-main artifact record.
RESIDENCY_CONTRACT = "content_addressed_hf_object_or_explicit_exclusion"
DATASET_TABLE = "artifacts"

# Projection outcome classes: an eligible reference lands as a content-addressed
# HF object; anything else is an EXPLICIT exclusion (never silent omission).
CLASS_HF_OBJECT = "content_addressed_hf_object"
CLASS_EXCLUDED = "excluded"

# Domain-separation type for a structured-object content_digest, so a structured
# artifact never collides with a physical blob whose bytes equal the JCS form.
STRUCTURED_CONTENT_ID_TYPE = "artifact_structured_content"

# The exhaustive byte-intrinsic field set of an Artifact record. Any other field
# (notably residency class/role/eligible) is forbidden on the record.
ARTIFACT_FIELDS = (
    "content_digest",
    "size_bytes",
    "media_type",
    "native_format",
    "compression",
    "schema_ref",
    "storage_locator",
    "license_evidence_ref",
)

# Per-reference role policy. HF eligibility is only ever available to a
# replay-critical public input or a curated native output; transient logs,
# caches and large regenerable dumps are EXPLICITLY excluded by role. Any other
# (unknown/ambiguous) role fails closed.
ELIGIBLE_ROLE_KINDS = frozenset({"replay_critical_input", "curated_native_output"})
EXCLUDED_ROLE_KINDS = frozenset({"transient_log", "cache", "large_regenerable_dump"})

# License-evidence ``redistribution`` values that fail public projection.
_NON_PUBLIC_REDISTRIBUTION = frozenset(
    {"restricted", "client_specific", "non_redistributable", "forbidden"}
)


class ArtifactError(ValueError):
    """Raised when an artifact record violates the byte-intrinsic contract."""


class IntegrityError(ArtifactError):
    """Raised when actual bytes disagree with a manifest-asserted content_digest."""


class StorageLocatorError(ArtifactError):
    """Raised for an unsafe or record-digest-mismatched storage locator."""


# ---------------------------------------------------------------------------
# content digests
# ---------------------------------------------------------------------------

def physical_byte_digest(stored_bytes) -> str:
    """SHA-256 of the EXACT immutable stored bytes (true content addressing).

    ``stored_bytes`` are the bytes as they physically reside in the object store.
    Compression/encoding is never decoded first -- the digest is what a publisher
    re-hashes from disk.
    """
    if not isinstance(stored_bytes, (bytes, bytearray, memoryview)):
        raise ArtifactError(
            f"physical artifact needs raw bytes, got {type(stored_bytes).__name__}"
        )
    return hashlib.sha256(bytes(stored_bytes)).hexdigest()


def structured_stored_bytes(obj) -> bytes:
    """The exact bytes a structured artifact resides as: its JCS canonical form.

    These are the bytes the object store persists, so a plain re-hash of them
    reproduces ``content_digest`` (see :func:`structured_object_digest`).
    """
    return identity.canonicalize(obj).encode("utf-8")


def structured_object_digest(obj) -> str:
    """Content_digest of a structured object = plain SHA-256 of its stored bytes.

    A ``content_digest`` is a CONTENT ADDRESS, not an identity: it must equal a
    plain ``sha256`` of the exact bytes that reside in the object store so any
    third party (e.g. the publisher's object-store re-hash in workspace-hub#3433)
    can revalidate integrity without knowing the artifact's type. The stored bytes
    of a structured object are its JCS canonical form (:func:`structured_stored_bytes`),
    so two key-orderings of one object still yield one digest. Domain separation is
    an *identity* concern (distinguishing algorithm_version_id/run_id) and is
    deliberately NOT applied here -- it would make the address disagree with a plain
    byte re-hash.
    """
    return hashlib.sha256(structured_stored_bytes(obj)).hexdigest()


# ---------------------------------------------------------------------------
# storage locator
# ---------------------------------------------------------------------------

def _digest_ok(content_digest) -> bool:
    return (
        isinstance(content_digest, str)
        and len(content_digest) == 64
        and all(c in "0123456789abcdef" for c in content_digest)
    )


def _validate_digest(content_digest) -> None:
    if not _digest_ok(content_digest):
        raise ArtifactError(
            f"content_digest must be a 64-char lowercase hex SHA-256, got {content_digest!r}"
        )


def storage_locator_for(content_digest) -> str:
    """Return the canonical sharded locator ``objects/<d[:2]>/<d>`` for a digest."""
    _validate_digest(content_digest)
    return "objects/" + content_digest[:2] + "/" + content_digest


def _is_unsafe_locator(locator: str) -> bool:
    if locator.startswith("/") or locator.startswith("~"):
        return True  # absolute path or home reference
    if "\\" in locator:
        return True  # UNC (\\server\share) or a windows/backslash path
    if ".." in locator.split("/"):
        return True  # parent-directory traversal
    return False


def validate_storage_locator(locator, content_digest) -> bool:
    """Validate a storage locator: reject unsafe paths and enforce digest binding.

    Raises :class:`StorageLocatorError` for an absolute / ``~`` / UNC / ``..``
    locator, or when ``locator != "objects/" + content_digest[:2] + "/" +
    content_digest`` (shard prefix + full digest tied to the record's digest).
    """
    if not isinstance(locator, str) or not locator:
        raise StorageLocatorError(f"storage_locator must be a non-empty string, got {locator!r}")
    if _is_unsafe_locator(locator):
        raise StorageLocatorError(
            f"unsafe storage_locator {locator!r}: absolute/home/UNC/.. paths are forbidden"
        )
    _validate_digest(content_digest)
    expected = "objects/" + content_digest[:2] + "/" + content_digest
    if locator != expected:
        raise StorageLocatorError(
            f"storage_locator {locator!r} does not match this record's digest "
            f"(expected {expected!r})"
        )
    return True


# ---------------------------------------------------------------------------
# artifact record construction (role-free, byte-intrinsic only)
# ---------------------------------------------------------------------------

def make_artifact(
    *,
    content_digest,
    size_bytes,
    media_type,
    native_format,
    compression=None,
    schema_ref=None,
    storage_locator=None,
    license_evidence_ref=None,
    **forbidden,
) -> dict:
    """Build a byte-intrinsic Artifact record.

    Rejects any residency ``class``/role/``eligible`` (or otherwise unexpected)
    field via ``**forbidden`` -- those live on the referencing Input/Output
    record, never on the artifact. When ``storage_locator`` is omitted it is
    derived from the digest; when supplied it is validated against the digest.
    """
    if forbidden:
        raise ArtifactError(
            "artifact record is role-free / byte-intrinsic; forbidden fields: "
            f"{sorted(forbidden)} (residency class/role/eligible live on the reference)"
        )
    _validate_digest(content_digest)
    if not isinstance(size_bytes, int) or isinstance(size_bytes, bool) or size_bytes < 0:
        raise ArtifactError(f"size_bytes must be a non-negative int, got {size_bytes!r}")
    if not media_type or not native_format:
        raise ArtifactError("media_type and native_format are required byte-intrinsic fields")
    if storage_locator is None:
        storage_locator = storage_locator_for(content_digest)
    else:
        validate_storage_locator(storage_locator, content_digest)
    return {
        "content_digest": content_digest,
        "size_bytes": size_bytes,
        "media_type": media_type,
        "native_format": native_format,
        "compression": compression,
        "schema_ref": schema_ref,
        "storage_locator": storage_locator,
        "license_evidence_ref": license_evidence_ref,
    }


def physical_artifact(
    stored_bytes,
    *,
    media_type,
    native_format,
    compression=None,
    schema_ref=None,
    license_evidence_ref=None,
) -> dict:
    """Build an Artifact record from the exact stored bytes (content-addressed)."""
    digest = physical_byte_digest(stored_bytes)
    return make_artifact(
        content_digest=digest,
        size_bytes=len(bytes(stored_bytes)),
        media_type=media_type,
        native_format=native_format,
        compression=compression,
        schema_ref=schema_ref,
        license_evidence_ref=license_evidence_ref,
    )


def structured_artifact(
    obj,
    *,
    media_type="application/json",
    native_format="jcs",
    compression=None,
    schema_ref=None,
    license_evidence_ref=None,
) -> dict:
    """Build an Artifact record from a structured object via its JCS canonical form.

    ``size_bytes`` is the byte length of the canonical serialization, so identical
    objects (any key ordering) produce one identical record.
    """
    canon = identity.canonicalize(obj)
    return make_artifact(
        content_digest=structured_object_digest(obj),
        size_bytes=len(canon.encode("utf-8")),
        media_type=media_type,
        native_format=native_format,
        compression=compression,
        schema_ref=schema_ref,
        license_evidence_ref=license_evidence_ref,
    )


# ---------------------------------------------------------------------------
# integrity: re-hash the actual bytes; the manifest is untrusted
# ---------------------------------------------------------------------------

def verify_integrity(record, *, stored_bytes=None, structured_object=None) -> bool:
    """Re-hash the object's actual bytes and reject any disagreeing manifest.

    Exactly one of ``stored_bytes`` / ``structured_object`` must be given. The
    digest is recomputed from that actual object; if it disagrees with
    ``record["content_digest"]`` we raise :class:`IntegrityError` (bytes win,
    the manifest is never trusted). This covers both tampered bytes and a
    hand-forged manifest digest. The storage locator is also re-checked against
    the recomputed digest.
    """
    if (stored_bytes is None) == (structured_object is None):
        raise ArtifactError("provide exactly one of stored_bytes / structured_object")
    asserted = record.get("content_digest")
    if stored_bytes is not None:
        actual = physical_byte_digest(stored_bytes)
    else:
        actual = structured_object_digest(structured_object)
    if actual != asserted:
        raise IntegrityError(
            f"content_digest mismatch: actual bytes hash to {actual} but the "
            f"manifest asserts {asserted!r}; bytes win, manifest rejected"
        )
    locator = record.get("storage_locator")
    if locator is not None:
        validate_storage_locator(locator, actual)
    return True


# ---------------------------------------------------------------------------
# residency projection: eligibility = (byte-license) x (reference-role)
# ---------------------------------------------------------------------------

def _role_kind(role):
    return role.get("kind") if isinstance(role, dict) else role


def _license_permits_public(evidence):
    """Return ``(permits, reason)`` for byte-intrinsic license evidence.

    Only unambiguous, publicly-redistributable, non-path-leaking evidence
    permits public projection. Missing evidence never permits it.
    """
    if evidence is None:
        return False, "no_license_evidence"
    if not isinstance(evidence, dict):
        return False, "unstructured_license_evidence"
    redistribution = evidence.get("redistribution")
    if redistribution in _NON_PUBLIC_REDISTRIBUTION:
        return False, f"redistribution_{redistribution}"
    if redistribution != "public":
        return False, "redistribution_not_public"
    license_id = evidence.get("license")
    if not license_id or license_id == "ambiguous":
        return False, "ambiguous_license"
    # a license reference that leaks a filesystem path is not publicly projectable.
    for value in evidence.values():
        if isinstance(value, str) and _is_unsafe_locator(value):
            return False, "path_leak"
    return True, "public_redistributable"


def _excluded(record, reason) -> dict:
    """A VISIBLE exclusion marker (never silent omission)."""
    return {
        "class": CLASS_EXCLUDED,
        "reason": reason,
        "content_digest": record.get("content_digest"),
        "storage_locator": record.get("storage_locator"),
    }


def project_reference_residency(record, role, *, dataset_license=None) -> dict:
    """Compute residency for one ``(artifact, referencing role)`` at projection time.

    Returns a ``class: content_addressed_hf_object`` marker only when the role is
    HF-eligible AND the artifact's OWN ``license_evidence_ref`` permits public
    redistribution; otherwise a VISIBLE ``class: excluded`` marker with a reason.
    ``dataset_license`` is accepted but can only ever RESTRICT -- it never grants
    rights absent from the artifact's byte-intrinsic evidence.
    """
    kind = _role_kind(role)
    if kind in EXCLUDED_ROLE_KINDS:
        return _excluded(record, f"role_excluded:{kind}")
    if kind not in ELIGIBLE_ROLE_KINDS:
        return _excluded(record, f"ambiguous_role:{kind}")

    permits, reason = _license_permits_public(record.get("license_evidence_ref"))
    if not permits:
        # a dataset-level license is deliberately NOT consulted to grant rights.
        return _excluded(record, reason)
    return {
        "class": CLASS_HF_OBJECT,
        "reason": f"eligible:{kind}:{reason}",
        "content_digest": record.get("content_digest"),
        "storage_locator": record.get("storage_locator"),
    }
