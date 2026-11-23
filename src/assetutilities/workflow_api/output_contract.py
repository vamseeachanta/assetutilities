# ABOUTME: Curated-output + output-equality contract (workspace-hub#3431): curated
# ABOUTME: taxonomy, digest_contribution, digest-of-sorted-digests equality, fail disjointness.
"""Curated output records and the output-equality digest.

This module implements the on-main
``docs/architecture/algorithm-run-dataset-contract.yaml`` ``records.output`` +
``identity.output_equality`` + ``failure_policy`` blocks. It OWNS the
``output_equality_digest`` (which #3428 references while owning the
``mismatch -> reject_without_mutation`` POLICY, reused verbatim here via
:func:`identity.assert_output_equality`). It is stdlib-only (``hashlib``, ``re``
plus :mod:`identity`), matching :mod:`envelope`, :mod:`identity`, :mod:`artifact`.

Design invariants (from the approved+remediated #3431 plan):

- **Curated-vs-excluded taxonomy is a declared allowlist.** ``primary_result``,
  ``validation_evidence``, ``selected_report``, ``decision_support`` are the ONLY
  curated labels. Anything unlabeled defaults to EXCLUDED (fail-closed) -- it is
  never recorded and never digested (:func:`is_curated_label`,
  :func:`make_output_record`).
- **Output record is role-bearing; it references Artifacts by content_digest.**
  It never redefines an artifact (that is :mod:`artifact`'s concern). Fields:
  role, native_schema {id, version}, media_type, shape/row_count, per-field units,
  coordinate/sign convention (when applicable), validation_state, review_state,
  artifact_refs and ``digest_contribution``.
- **digest_contribution DEFAULTS to ``included``.** ``excluded`` is permitted ONLY
  via an explicitly declared + justified rule (fail-closed exactly like the semantic
  canonicalizer). An undeclared / silent exclusion fails closed -- an unguarded
  exclusion could silently drop a nondeterministic curated output so exact-rerun
  equality passes while bytes differ (a masked reproducibility defect).
- **output_equality_digest is a digest-of-sorted-digests.** default =
  ``raw_bytes_sha256`` = ``sha256(identity.canonicalize(sorted list of the per-artifact
  sha256 content_digests of every digest-eligible curated output))`` -- NOT raw byte
  concatenation (which is boundary-ambiguous). A semantic canonicalizer is allowed
  ONLY when all five fields (canonicalizer_id, canonicalizer_version, raw_hash,
  semantic_hash, explicit_approval) are declared; undeclared normalization is
  presentation_only. Exact-rerun mismatch fails publication and cannot overwrite the
  prior record (:func:`assert_output_equality` delegates to identity's policy).
- **Success vs failure requirement sets are provably disjoint.** A
  ``failure_signature`` presence/absence is the XOR discriminator: ``succeeded`` MUST
  NOT carry it; ``reproducible_failure`` MUST. Failure normalization requires
  failure_phase, failure_code, failure_signature, curated_diagnostic_digests,
  replay_evidence. The signature strips volatile paths/timestamps/pids/hosts and
  normalizes stack frames by module ``qualname`` (drop file path + line, keep
  module.func) so the same fault hashes identically cross-machine. Failed runs are
  eligible only for run_health / diagnostics and FORBIDDEN from metric_observations
  / insights / decision_briefs.
"""

from __future__ import annotations

import hashlib
import re

from assetutilities.workflow_api import identity

# ---- on-main contract constants -------------------------------------------
DATASET_TABLE = "outputs"
RESIDENCY = "hf_object_and_normalized_record"

# Default output-equality comparison (shared with identity's reference).
OUTPUT_EQUALITY_DEFAULT = identity.OUTPUT_EQUALITY_DEFAULT  # "raw_bytes_sha256"
# The digest algorithm is versioned so a scheme change mints new equality digests.
OUTPUT_EQUALITY_DIGEST_VERSION = "output-equality-1"

# Declared curated allowlist. Anything else -> EXCLUDED (fail-closed, not recorded).
CURATED_LABELS = frozenset(
    {"primary_result", "validation_evidence", "selected_report", "decision_support"}
)

# digest_contribution domain.
DIGEST_INCLUDED = "included"
DIGEST_EXCLUDED = "excluded"

# The five fields a declared semantic canonicalizer (equality exception) MUST carry.
SEMANTIC_EXCEPTION_REQUIRED = (
    "canonicalizer_id",
    "canonicalizer_version",
    "raw_hash",
    "semantic_hash",
    "explicit_approval",
)

# Failure normalization required set (verbatim from failure_policy.normalization_requires).
FAILURE_NORMALIZATION_REQUIRED = (
    "failure_phase",
    "failure_code",
    "failure_signature",
    "curated_diagnostic_digests",
    "replay_evidence",
)

# A failed run may only surface here; everything else is forbidden.
FAILURE_ELIGIBLE_SURFACES = frozenset({"run_health", "diagnostics"})
FAILURE_FORBIDDEN_SURFACES = frozenset(
    {"metric_observations", "insights", "decision_briefs"}
)

# Terminal run statuses this contract reasons about.
_SUCCEEDED = "succeeded"
_REPRODUCIBLE_FAILURE = "reproducible_failure"

FAILURE_SIGNATURE_VERSION = "fsig-1"


class OutputContractError(ValueError):
    """Raised when an output/report violates the curated-output contract."""


# ---------------------------------------------------------------------------
# curated taxonomy
# ---------------------------------------------------------------------------

def is_curated_label(label) -> bool:
    """True iff ``label`` is a declared curated label; unlabeled -> ``False``.

    An unlabeled or unknown output defaults to EXCLUDED (fail-closed): it is never
    recorded and never contributes to the equality digest.
    """
    return label in CURATED_LABELS


# ---------------------------------------------------------------------------
# digest helpers
# ---------------------------------------------------------------------------

def _is_hex_sha256(value) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(c in "0123456789abcdef" for c in value)
    )


def _validate_artifact_refs(artifact_refs):
    if not isinstance(artifact_refs, (list, tuple)) or not artifact_refs:
        raise OutputContractError("artifact_refs must be a non-empty list")
    normalized = []
    for ref in artifact_refs:
        if isinstance(ref, str):
            content_digest = ref
            ref = {"content_digest": content_digest}
        elif isinstance(ref, dict):
            content_digest = ref.get("content_digest")
        else:
            raise OutputContractError(
                f"artifact_ref must be a dict or content_digest string, got {type(ref).__name__}"
            )
        if not _is_hex_sha256(content_digest):
            raise OutputContractError(
                f"artifact_ref.content_digest must be a 64-char hex sha256, got {content_digest!r}"
            )
        normalized.append(dict(ref))
    return normalized


def _validate_exclusion_rule(rule):
    """A digest exclusion is permitted ONLY via a declared + justified rule."""
    if not isinstance(rule, dict):
        raise OutputContractError(
            "digest_contribution 'excluded' requires a declared exclusion_rule dict "
            "(fail-closed: an undeclared exclusion could mask a reproducibility defect)"
        )
    rule_id = rule.get("rule_id")
    justification = rule.get("justification")
    if not rule_id or not isinstance(rule_id, str):
        raise OutputContractError("exclusion_rule requires a non-empty 'rule_id'")
    if not justification or not isinstance(justification, str):
        raise OutputContractError("exclusion_rule requires a non-empty 'justification'")
    return {"rule_id": rule_id, "justification": justification}


# ---------------------------------------------------------------------------
# output record construction
# ---------------------------------------------------------------------------

def make_output_record(
    *,
    role,
    native_schema,
    media_type,
    curated_label,
    artifact_refs,
    shape=None,
    row_count=None,
    units=None,
    convention=None,
    validation_state=None,
    review_state=None,
    digest_contribution=None,
    exclusion_rule=None,
) -> dict:
    """Build a curated Output record referencing Artifacts by content_digest.

    Fail-closed rules:

    - ``curated_label`` MUST be in :data:`CURATED_LABELS`; an unlabeled / unknown
      output is EXCLUDED and cannot be recorded.
    - ``native_schema`` MUST carry an ``id`` + ``version``.
    - ``digest_contribution`` DEFAULTS to ``included``; ``excluded`` is permitted
      ONLY with a declared + justified ``exclusion_rule``.
    - ``artifact_refs`` reference existing Artifacts by 64-hex ``content_digest``
      (this module never redefines an artifact -- see :mod:`artifact`).
    """
    if not is_curated_label(curated_label):
        raise OutputContractError(
            f"output label {curated_label!r} is not curated (allowlist={sorted(CURATED_LABELS)}); "
            "unlabeled outputs default to EXCLUDED and are never recorded/digested"
        )
    if not role:
        raise OutputContractError("output record requires a non-empty role")
    if not media_type:
        raise OutputContractError("output record requires a media_type")
    if not isinstance(native_schema, dict) or not native_schema.get("id") or not native_schema.get("version"):
        raise OutputContractError("native_schema must be a dict carrying an 'id' and 'version'")

    refs = _validate_artifact_refs(artifact_refs)

    if digest_contribution is None:
        digest_contribution = DIGEST_INCLUDED
    if digest_contribution not in (DIGEST_INCLUDED, DIGEST_EXCLUDED):
        raise OutputContractError(
            f"digest_contribution must be 'included' or 'excluded', got {digest_contribution!r}"
        )
    resolved_rule = None
    if digest_contribution == DIGEST_EXCLUDED:
        resolved_rule = _validate_exclusion_rule(exclusion_rule)
    elif exclusion_rule is not None:
        raise OutputContractError(
            "exclusion_rule only applies when digest_contribution == 'excluded'"
        )

    return {
        "role": role,
        "native_schema": dict(native_schema),
        "media_type": media_type,
        "curated_label": curated_label,
        "shape": shape,
        "row_count": row_count,
        "units": dict(units) if isinstance(units, dict) else units,
        "convention": convention,
        "validation_state": validation_state,
        "review_state": review_state,
        "artifact_refs": refs,
        "digest_contribution": digest_contribution,
        "exclusion_rule": resolved_rule,
    }


def _is_digest_eligible(record) -> bool:
    """A curated output contributes to the equality digest iff it is labelled
    curated AND its ``digest_contribution`` is ``included``."""
    if not isinstance(record, dict):
        raise OutputContractError("output record must be a dict")
    if not is_curated_label(record.get("curated_label")):
        return False
    return record.get("digest_contribution", DIGEST_INCLUDED) == DIGEST_INCLUDED


# ---------------------------------------------------------------------------
# native-schema validation
# ---------------------------------------------------------------------------

def _type_ok(spec: str, value) -> bool:
    if spec == "any":
        return True
    if spec == "null":
        return value is None
    if spec == "boolean":
        return isinstance(value, bool)
    if spec == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if spec == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if spec == "string":
        return isinstance(value, str)
    if spec == "array":
        return isinstance(value, (list, tuple))
    if spec == "object":
        return isinstance(value, dict)
    raise OutputContractError(f"unknown native_schema field type {spec!r}")


def assert_payload_conforms(native_schema, payload) -> bool:
    """Reject a payload that violates its declared ``native_schema``.

    The schema declares ``fields`` (name -> type) and optional ``required``. A
    missing required field, a wrong-typed field, or an undeclared extra field all
    fail closed (:class:`OutputContractError`). Returns ``True`` when conforming.
    """
    if not isinstance(native_schema, dict):
        raise OutputContractError("native_schema must be a dict")
    fields = native_schema.get("fields")
    if not isinstance(fields, dict):
        raise OutputContractError("native_schema must declare a 'fields' mapping to validate a payload")
    if not isinstance(payload, dict):
        raise OutputContractError("payload must be a dict")
    required = native_schema.get("required", [])

    for name in required:
        if name not in payload:
            raise OutputContractError(f"payload missing required field {name!r}")
    extra = set(payload) - set(fields)
    if extra:
        raise OutputContractError(
            f"payload has undeclared field(s) not in native_schema: {sorted(extra)}"
        )
    for name, value in payload.items():
        spec = fields[name]
        if not _type_ok(spec, value):
            raise OutputContractError(
                f"payload field {name!r}={value!r} violates declared type {spec!r}"
            )
    return True


# ---------------------------------------------------------------------------
# output_equality_digest (owned here; policy owned by identity)
# ---------------------------------------------------------------------------

def _validate_semantic_declaration(decl) -> dict:
    """A semantic canonicalizer is allowed ONLY when all five fields are declared."""
    if not isinstance(decl, dict):
        raise OutputContractError("semantic_canonicalizer declaration must be a dict")
    missing = [k for k in SEMANTIC_EXCEPTION_REQUIRED if not decl.get(k)]
    if missing:
        raise OutputContractError(
            "semantic canonicalizer fails closed; declaration missing required fields: "
            f"{missing} (required={list(SEMANTIC_EXCEPTION_REQUIRED)})"
        )
    return decl


def output_equality_digest(outputs, *, semantic_canonicalizer=None) -> dict:
    """Compute the versioned ``output_equality_digest`` over curated outputs.

    Default (``raw_bytes_sha256``) = ``sha256(identity.canonicalize(sorted list of
    the per-artifact sha256 content_digests of every digest-eligible curated
    output))`` -- a digest-of-sorted-digests, boundary-safe (NOT raw concatenation).
    Only outputs that are curated AND ``digest_contribution == included`` are counted.

    A semantic canonicalizer is honoured ONLY when fully declared (the five
    :data:`SEMANTIC_EXCEPTION_REQUIRED` fields); its ``semantic_hash`` becomes the
    digest. Undeclared normalization is presentation_only and never alters equality.
    Returns ``{"algorithm", "version", "digest", "input_digest_count"}``.
    """
    if semantic_canonicalizer is not None:
        decl = _validate_semantic_declaration(semantic_canonicalizer)
        return {
            "algorithm": f"semantic:{decl['canonicalizer_id']}@{decl['canonicalizer_version']}",
            "version": OUTPUT_EQUALITY_DIGEST_VERSION,
            "digest": decl["semantic_hash"],
            "raw_hash": decl["raw_hash"],
            "explicit_approval": decl["explicit_approval"],
        }

    content_digests = []
    for record in outputs:
        if not _is_digest_eligible(record):
            continue
        for ref in record["artifact_refs"]:
            content_digests.append(ref["content_digest"])
    ordered = sorted(content_digests)
    digest = hashlib.sha256(identity.canonicalize(ordered).encode("utf-8")).hexdigest()
    return {
        "algorithm": OUTPUT_EQUALITY_DEFAULT,
        "version": OUTPUT_EQUALITY_DIGEST_VERSION,
        "digest": digest,
        "input_digest_count": len(ordered),
    }


def assert_output_equality(recorded_digest, observed_digest, *, prior_record=None) -> bool:
    """Enforce the exact-rerun equality policy (owned by :mod:`identity`).

    Delegates to :func:`identity.assert_output_equality`: an exact-rerun mismatch
    raises :class:`identity.OutputMismatchError` and mutates NOTHING
    (``reject_without_mutation``); equal digests are accepted.
    """
    return identity.assert_output_equality(
        recorded_digest, observed_digest, prior_record=prior_record
    )


# ---------------------------------------------------------------------------
# success vs failure: provably disjoint via the failure_signature XOR
# ---------------------------------------------------------------------------

def make_failure_normalization(
    *,
    failure_phase,
    failure_code,
    failure_signature,
    curated_diagnostic_digests,
    replay_evidence,
) -> dict:
    """Build a reproducible-failure normalization record (all five fields required)."""
    record = {
        "failure_phase": failure_phase,
        "failure_code": failure_code,
        "failure_signature": failure_signature,
        "curated_diagnostic_digests": curated_diagnostic_digests,
        "replay_evidence": replay_evidence,
    }
    missing = [k for k in FAILURE_NORMALIZATION_REQUIRED if not record.get(k)]
    if missing:
        raise OutputContractError(
            f"failure normalization missing required fields: {missing}"
        )
    return record


def assert_status_requirements(status, record) -> bool:
    """Enforce that success/failure requirement sets are disjoint via the signature.

    ``failure_signature`` is the XOR discriminator: a ``succeeded`` record MUST NOT
    carry one; a ``reproducible_failure`` record MUST carry one AND the full
    normalization set. Raises :class:`OutputContractError` on violation.
    """
    if not isinstance(record, dict):
        raise OutputContractError("run record must be a dict")
    has_signature = bool(record.get("failure_signature"))
    if status == _SUCCEEDED:
        if has_signature:
            raise OutputContractError(
                "a succeeded run MUST NOT carry a failure_signature (disjointness violated)"
            )
        return True
    if status == _REPRODUCIBLE_FAILURE:
        if not has_signature:
            raise OutputContractError(
                "a reproducible_failure run MUST carry a failure_signature (XOR discriminator)"
            )
        missing = [k for k in FAILURE_NORMALIZATION_REQUIRED if not record.get(k)]
        if missing:
            raise OutputContractError(
                f"reproducible_failure missing required normalization fields: {missing}"
            )
        return True
    raise OutputContractError(f"unknown / non-terminal status for surfacing: {status!r}")


# ---------------------------------------------------------------------------
# failure_signature: stable cross-machine
# ---------------------------------------------------------------------------

# Volatile substrings to strip before hashing so the same fault hashes identically
# on any machine: absolute paths, ISO/space timestamps, pids, hostnames.
_VOL_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?")
_VOL_PID = re.compile(r"\bpid[=: ]\s*\d+", re.IGNORECASE)
_VOL_HOST = re.compile(r"\bhost[=: ]\s*\S+", re.IGNORECASE)
_VOL_WIN_PATH = re.compile(r"[A-Za-z]:\\[^\s'\"]+")
_VOL_UNIX_PATH = re.compile(r"(?:/[\w.\-]+)+/?")

# Markers after which the remainder of a file path is an importable module path.
_MODULE_ROOT_MARKERS = ("site-packages/", "dist-packages/")
_STDLIB_RE = re.compile(r"/lib/python\d+\.\d+/")


def _strip_volatile(text: str) -> str:
    if not text:
        return ""
    text = _VOL_TIMESTAMP.sub("<ts>", text)
    text = _VOL_PID.sub("pid=<pid>", text)
    text = _VOL_HOST.sub("host=<host>", text)
    text = _VOL_WIN_PATH.sub("<path>", text)
    text = _VOL_UNIX_PATH.sub("<path>", text)
    return text


def _module_from_file(path: str) -> str:
    """Derive an importable module qualname from a (machine-varying) file path.

    Drops everything up to and including the venv/stdlib root marker, then converts
    the remaining ``pkg/sub/mod.py`` tail into ``pkg.sub.mod``. This makes a
    third-party/stdlib/venv frame identical across machines (path + line dropped).
    """
    tail = path
    for marker in _MODULE_ROOT_MARKERS:
        idx = path.rfind(marker)
        if idx != -1:
            tail = path[idx + len(marker):]
            break
    else:
        m = _STDLIB_RE.search(path)
        if m:
            tail = path[m.end():]
        else:
            # project frame: keep only the basename component chain we can see;
            # fall back to the file's own name (still line/path-free).
            tail = path.rsplit("/", 1)[-1]
    if tail.endswith(".py"):
        tail = tail[:-3]
    return tail.strip("/").replace("/", ".")


def _normalize_frame(frame) -> str:
    """Reduce a stack frame to ``module.func`` (drop file path + line number)."""
    if not isinstance(frame, dict):
        raise OutputContractError("each frame must be a dict")
    func = frame.get("func") or frame.get("name") or "<unknown>"
    module = frame.get("module")
    if not module:
        file_path = frame.get("file") or frame.get("filename")
        if not file_path:
            raise OutputContractError("frame needs a 'module' or 'file' to normalize")
        module = _module_from_file(file_path)
    return f"{module}.{func}"


def failure_signature(*, phase, code, frames=(), detail="") -> str:
    """Compute a stable, cross-machine failure signature.

    Strips volatile paths/timestamps/pids/hosts from ``detail`` and normalizes each
    stack frame to its module ``qualname`` (``module.func``, dropping file path and
    line number) so the same fault hashes identically on any machine. The result is
    versioned (``fsig-1:<hex>``).
    """
    normalized_frames = [_normalize_frame(f) for f in frames]
    payload = {
        "phase": phase,
        "code": code,
        "frames": normalized_frames,
        "detail": _strip_volatile(detail),
    }
    digest = hashlib.sha256(identity.canonicalize(payload).encode("utf-8")).hexdigest()
    return f"{FAILURE_SIGNATURE_VERSION}:{digest}"


# ---------------------------------------------------------------------------
# surface eligibility for failed runs
# ---------------------------------------------------------------------------

def assert_surface_allowed(status, surface) -> bool:
    """Reject a failed run published to a forbidden surface (fail-closed).

    A ``reproducible_failure`` may surface only in run_health / diagnostics; it is
    FORBIDDEN from metric_observations / insights / decision_briefs (and any unknown
    surface fails closed). A ``succeeded`` run may surface anywhere.
    """
    if status == _SUCCEEDED:
        return True
    if status == _REPRODUCIBLE_FAILURE:
        if surface in FAILURE_ELIGIBLE_SURFACES:
            return True
        if surface in FAILURE_FORBIDDEN_SURFACES:
            raise OutputContractError(
                f"a failed run is forbidden from the {surface!r} surface "
                f"(eligible only for {sorted(FAILURE_ELIGIBLE_SURFACES)})"
            )
        raise OutputContractError(
            f"a failed run may not surface on the unknown surface {surface!r} (fail-closed)"
        )
    raise OutputContractError(f"unknown / non-terminal status: {status!r}")
