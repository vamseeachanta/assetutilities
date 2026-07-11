# ABOUTME: TDD tests for the content-addressed artifact + HF-residency contract
# ABOUTME: (workspace-hub#3429): physical-byte vs structured digests, role-free identity,
# ABOUTME: integrity-from-bytes, storage-locator safety, and projection-time residency.
"""Artifact contract tests (no engine dependency).

These pin the normative rules from the on-main
``docs/architecture/algorithm-run-dataset-contract.yaml`` ``artifact`` record
(``identity: content_digest``, ``residency:
content_addressed_hf_object_or_explicit_exclusion``, ``dataset_table: artifacts``):

- content_digest is SHA-256 of the EXACT STORED bytes (physical) or of the
  ``identity.canonicalize`` JCS form (structured object). Compression is purely
  descriptive metadata and NEVER triggers decode-before-hash.
- The Artifact record is role-free / byte-intrinsic: identical bytes -> one record
  regardless of how many runs/roles reference it. Residency ``class``/role/
  ``eligible`` never live on the record.
- Integrity is re-validated from the object's actual bytes; a manifest-asserted
  digest that disagrees is rejected (bytes win, manifest is untrusted).
- storage_locator must be shard-sharded + tied to the record digest and reject
  path-leaking locators.
- Residency eligibility is computed at projection time as (byte-intrinsic license
  evidence) x (per-reference role); a dataset-level license can never grant rights
  absent from the artifact's own ``license_evidence_ref``. Excluded roles get a
  VISIBLE ``class: excluded`` marker, never silent omission.
"""

from __future__ import annotations

import gzip
import hashlib

import pytest

from assetutilities.workflow_api import artifact, identity


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _public_license() -> dict:
    return {"redistribution": "public", "license": "CC-BY-4.0"}


# ---------------------------------------------------------------------------
# 1. physical artifact hashes the stored bytes, never the decoded bytes
# ---------------------------------------------------------------------------

def test_physical_artifact_hashes_stored_bytes_not_decoded():
    decoded = b"replay-critical payload" * 64
    stored = gzip.compress(decoded)
    assert stored != decoded

    art = artifact.physical_artifact(
        stored, media_type="application/octet-stream",
        native_format="ndjson", compression="gzip",
    )

    # TRUE content addressing: digest is over the exact immutable STORED bytes.
    assert art["content_digest"] == _sha256(stored)
    assert art["size_bytes"] == len(stored)
    # compression is PURELY DESCRIPTIVE metadata; it must NOT decode-before-hash.
    assert art["compression"] == "gzip"
    assert art["content_digest"] != _sha256(decoded)

    # a publisher re-hashing the exact stored bytes agrees.
    assert artifact.verify_integrity(art, stored_bytes=stored) is True
    # re-hashing the DECODED bytes must NOT be accepted as the same object.
    with pytest.raises(artifact.IntegrityError):
        artifact.verify_integrity(art, stored_bytes=decoded)


# ---------------------------------------------------------------------------
# 2. structured object uses the canonical (JCS) form
# ---------------------------------------------------------------------------

def test_structured_object_uses_canonical_form():
    obj_a = {"b": 1, "a": {"y": 2, "x": 3}}
    obj_b = {"a": {"x": 3, "y": 2}, "b": 1}  # different key ordering, same object

    d_a = artifact.structured_object_digest(obj_a)
    d_b = artifact.structured_object_digest(obj_b)
    assert d_a == d_b, "two key-orderings of one object must yield one digest"

    # digest is derived through identity.canonicalize (the JCS owner), not raw dict repr.
    assert identity.canonicalize(obj_a) == identity.canonicalize(obj_b)

    art_a = artifact.structured_artifact(obj_a)
    art_b = artifact.structured_artifact(obj_b)
    assert art_a["content_digest"] == art_b["content_digest"] == d_a
    assert art_a == art_b  # one artifact record regardless of key order


# ---------------------------------------------------------------------------
# 3. identical bytes -> ONE artifact record, no role/residency on the record
# ---------------------------------------------------------------------------

def test_identical_bytes_one_artifact_record_across_roles():
    payload = b"shared immutable object bytes"
    art_seen_as_input = artifact.physical_artifact(
        payload, media_type="text/csv", native_format="csv")
    art_seen_as_output = artifact.physical_artifact(
        payload, media_type="text/csv", native_format="csv")

    # identical bytes -> identical record (deduplicated to one content_digest).
    assert art_seen_as_input == art_seen_as_output
    assert art_seen_as_input["content_digest"] == _sha256(payload)

    # the record carries ONLY byte-intrinsic fields; role/residency live elsewhere.
    for banned in ("class", "role", "eligible", "residency", "residency_class"):
        assert banned not in art_seen_as_input
    assert set(art_seen_as_input) == {
        "content_digest", "size_bytes", "media_type", "native_format",
        "compression", "schema_ref", "storage_locator", "license_evidence_ref",
    }


# ---------------------------------------------------------------------------
# 4. integrity is revalidated from the bytes; a manifest lie is rejected
# ---------------------------------------------------------------------------

def test_integrity_revalidated_from_bytes_rejects_manifest_lie():
    payload = b"authentic bytes"
    art = artifact.physical_artifact(
        payload, media_type="application/octet-stream", native_format="bin")

    # (a) tampered bytes: the stored bytes changed, the asserted digest no longer holds.
    with pytest.raises(artifact.IntegrityError):
        artifact.verify_integrity(art, stored_bytes=b"tampered bytes")

    # (b) a wrong manifest-asserted digest is rejected even for the genuine bytes:
    # bytes win, the manifest is untrusted.
    lying = dict(art)
    lying["content_digest"] = "0" * 64
    lying["storage_locator"] = artifact.storage_locator_for("0" * 64)
    with pytest.raises(artifact.IntegrityError):
        artifact.verify_integrity(lying, stored_bytes=payload)


# ---------------------------------------------------------------------------
# 5. storage_locator must equal objects/<d[:2]>/<d> for the record's own digest
# ---------------------------------------------------------------------------

def test_storage_locator_matches_record_digest():
    payload = b"locator bytes"
    art = artifact.physical_artifact(
        payload, media_type="application/octet-stream", native_format="bin")
    d = art["content_digest"]
    assert art["storage_locator"] == "objects/" + d[:2] + "/" + d
    assert artifact.validate_storage_locator(art["storage_locator"], d) is True

    # a locator that points at a DIFFERENT digest is rejected.
    other = "f" * 64
    with pytest.raises(artifact.StorageLocatorError):
        artifact.validate_storage_locator("objects/" + other[:2] + "/" + other, d)
    # right digest but wrong shard prefix is rejected.
    with pytest.raises(artifact.StorageLocatorError):
        artifact.validate_storage_locator("objects/zz/" + d, d)
    # constructing a record with a mismatched supplied locator is rejected.
    with pytest.raises(artifact.StorageLocatorError):
        artifact.make_artifact(
            content_digest=d, size_bytes=len(payload), media_type="x",
            native_format="bin", storage_locator="objects/00/" + other)


# ---------------------------------------------------------------------------
# 6. unsafe storage locators (absolute / ~ / UNC / ..) are rejected
# ---------------------------------------------------------------------------

def test_unsafe_storage_locator_rejected():
    d = _sha256(b"whatever")
    unsafe = [
        "/etc/passwd",                       # absolute
        "/objects/" + d[:2] + "/" + d,       # absolute even if otherwise shaped
        "~/objects/" + d[:2] + "/" + d,      # home
        "~root/secret",                      # home
        "\\\\server\\share\\" + d,           # UNC
        "C:\\objects\\" + d,                 # windows drive / backslash
        "objects/../" + d[:2] + "/" + d,     # parent traversal
        "objects/" + d[:2] + "/../" + d,     # parent traversal
    ]
    for loc in unsafe:
        with pytest.raises(artifact.StorageLocatorError):
            artifact.validate_storage_locator(loc, d)


# ---------------------------------------------------------------------------
# 7. restricted / ambiguous / client-specific / path-leak / non-redist FAIL
# ---------------------------------------------------------------------------

def test_restricted_ambiguous_client_pathleak_nonredist_fail_projection():
    payload = b"sensitive object"
    role = "curated_native_output"  # an otherwise HF-eligible role

    failing_licenses = {
        "restricted": {"redistribution": "restricted", "license": "MIT"},
        "ambiguous": {"redistribution": "public", "license": "ambiguous"},
        "client_specific": {"redistribution": "client_specific", "license": "MIT"},
        "path_leak": {"redistribution": "public", "license": "MIT",
                       "evidence_path": "/home/vamsee/client/LICENSE.txt"},
        "non_redistributable": {"redistribution": "non_redistributable", "license": "MIT"},
    }
    for label, lic in failing_licenses.items():
        art = artifact.physical_artifact(
            payload, media_type="text/plain", native_format="txt",
            license_evidence_ref=lic)
        proj = artifact.project_reference_residency(art, role)
        assert proj["class"] == artifact.CLASS_EXCLUDED, f"{label} must fail projection"
        assert proj["reason"], "an excluded projection must carry a visible reason"


# ---------------------------------------------------------------------------
# 8. transient/cache/regenerable roles are VISIBLY excluded, not silently dropped
# ---------------------------------------------------------------------------

def test_excluded_roles_are_visibly_excluded():
    payload = b"regenerable dump"
    # a perfectly public license does NOT rescue a transient/regenerable role.
    art = artifact.physical_artifact(
        payload, media_type="text/plain", native_format="log",
        license_evidence_ref=_public_license())

    for role in ("transient_log", "cache", "large_regenerable_dump"):
        proj = artifact.project_reference_residency(art, role)
        assert proj is not None, "exclusion must be an explicit marker, not silent omission"
        assert proj["class"] == artifact.CLASS_EXCLUDED
        assert role in proj["reason"]
        assert proj["content_digest"] == art["content_digest"]


# ---------------------------------------------------------------------------
# 9. a dataset-level license can NOT grant rights the artifact itself lacks
# ---------------------------------------------------------------------------

def test_dataset_license_cannot_grant_missing_rights():
    payload = b"no license evidence on this object"
    art = artifact.physical_artifact(
        payload, media_type="text/plain", native_format="txt",
        license_evidence_ref=None)  # NO byte-intrinsic license evidence

    dataset_license = {"redistribution": "public", "license": "CC-BY-4.0"}
    proj = artifact.project_reference_residency(
        art, "curated_native_output", dataset_license=dataset_license)
    assert proj["class"] == artifact.CLASS_EXCLUDED, (
        "a dataset-level license must never grant rights absent from the "
        "artifact's own license_evidence_ref")


# ---------------------------------------------------------------------------
# 10. an input reference and an output reference share ONE artifact, no dup
# ---------------------------------------------------------------------------

def test_input_and_output_reference_same_artifact_without_duplication():
    obj = {"grid": [1, 2, 3], "coeff": 0.5}
    art = artifact.structured_artifact(obj, license_evidence_ref=_public_license())

    # referenced as a replay-critical input in run A and a curated output in run B:
    # both point at the SAME content_digest; the record is identical (no role on it).
    as_input = artifact.project_reference_residency(art, "replay_critical_input")
    as_output = artifact.project_reference_residency(art, "curated_native_output")
    assert as_input["content_digest"] == as_output["content_digest"] == art["content_digest"]
    assert as_input["class"] == as_output["class"] == artifact.CLASS_HF_OBJECT
    # the artifact record itself is unchanged by projection (role lives on the reference).
    assert "role" not in art and "class" not in art


# ---------------------------------------------------------------------------
# 11. a dedicated forbidden-residency fixture is rejected at construction
# ---------------------------------------------------------------------------

def test_forbidden_residency_fixture_rejected():
    payload = b"attempt to stamp residency onto the record"
    d = _sha256(payload)
    # stamping residency/role/eligibility onto the byte-intrinsic record is forbidden.
    for forbidden_field in ("residency", "class", "role", "eligible"):
        with pytest.raises(artifact.ArtifactError):
            artifact.make_artifact(
                content_digest=d, size_bytes=len(payload), media_type="x",
                native_format="bin", **{forbidden_field: "excluded"})

    # a fixture whose license is explicitly a forbidden residency also fails projection.
    art = artifact.physical_artifact(
        payload, media_type="text/plain", native_format="txt",
        license_evidence_ref={"redistribution": "forbidden", "license": "MIT"})
    proj = artifact.project_reference_residency(art, "curated_native_output")
    assert proj["class"] == artifact.CLASS_EXCLUDED


# ---------------------------------------------------------------------------
# 12. eligibility == (byte-license) x (reference-role), computed at projection
# ---------------------------------------------------------------------------

def test_eligibility_is_byte_license_times_reference_role():
    payload = b"one object, many references"

    public_art = artifact.physical_artifact(
        payload, media_type="text/plain", native_format="txt",
        license_evidence_ref=_public_license())
    restricted_art = artifact.physical_artifact(
        payload + b"x", media_type="text/plain", native_format="txt",
        license_evidence_ref={"redistribution": "restricted", "license": "MIT"})

    # public license x eligible role -> HF object
    assert artifact.project_reference_residency(
        public_art, "curated_native_output")["class"] == artifact.CLASS_HF_OBJECT
    # public license x excluded role -> excluded (role gate)
    assert artifact.project_reference_residency(
        public_art, "cache")["class"] == artifact.CLASS_EXCLUDED
    # restricted license x eligible role -> excluded (license gate)
    assert artifact.project_reference_residency(
        restricted_art, "curated_native_output")["class"] == artifact.CLASS_EXCLUDED

    # the product is computed at projection time, NOT stamped on the record.
    assert "eligible" not in public_art and "class" not in public_art
    assert artifact.RESIDENCY_CONTRACT == "content_addressed_hf_object_or_explicit_exclusion"
    assert artifact.DATASET_TABLE == "artifacts"
