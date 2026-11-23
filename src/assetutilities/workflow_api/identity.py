# ABOUTME: Deterministic run-identity contract (workspace-hub#3428): canonical
# ABOUTME: serialization + domain-separated SHA-256 digests + fail-closed identity.
"""Deterministic run identity.

This module OWNS the canonical serialization for the deterministic-workflow epic
(workspace-hub#3281) and mints the type-separated SHA-256 identities defined by
the on-main ``docs/architecture/algorithm-run-dataset-contract.yaml`` ``identity``
block. It is stdlib-only (``hashlib``, ``decimal``, ``unicodedata``, ``json``,
``re``) to keep the shared library dependency-free, matching :mod:`envelope`.

Design invariants:

- **Canonical serialization owner = identity.** :func:`canonicalize` implements a
  compact RFC 8785 (JCS) serializer: UTF-8, object keys sorted by UTF-16 code-unit
  order, no insignificant whitespace, arrays in declared order. Strings are
  Unicode-NFC-normalized before hashing; numbers normalize through
  :class:`decimal.Decimal` with no float round-trip (``1e3 == 1000``,
  ``5.0 == 5.00 == 5``); ``null``/NA is explicit and never omitted. A physical
  quantity MUST be an explicit ``{"value": ..., "unit": ...}`` pair -- a bare
  units-bearing numeric string (``"5 kg"``) is rejected.
- **Domain separation.** Every digest is prefixed with its identity type AND the
  :data:`CANONICALIZATION_VERSION`, so different id types never collide on equal
  component bytes and a scheme change mints new ids deterministically.
- **Identity is re-derived from a VERIFIED clean context** (a proven-clean commit
  + declared env/schema pins + canonical inputs). The :class:`ResultEnvelope`
  ``input_hash`` (volatile-key-pruned) and ``code_version.git_sha`` (best-effort,
  no clean-tree proof) are EVIDENCE, never identity inputs;
  :func:`derive_run_identity` deliberately consumes neither.
- **Fail-closed.** :func:`check_eligibility` rejects dirty tree / unknown-or-shallow
  revision / unpinned schema / missing environment digest / implicit seed /
  implicit execution default before any id is minted.
- ``run_id`` EXCLUDES outputs -- an exact rerun is the SAME ``run_id``. Output
  equality is a separate ``output_equality_digest`` (owned by #3431) that this
  module only references as an opaque injected value while owning the
  mismatch -> reject-without-mutation POLICY (:func:`assert_output_equality`).
  ``input_set_id`` per-input canonical field membership is #3430's concern; this
  module consumes ``input_record_id`` values as given.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from decimal import Decimal

# A change to this constant is a change to the serialization scheme; because it
# participates in every digest, bumping it deterministically mints new ids.
CANONICALIZATION_VERSION = "identity-jcs-1"

# Default output-equality comparison (the digest itself is owned by #3431).
OUTPUT_EQUALITY_DEFAULT = "raw_bytes_sha256"

# ---- component contracts (verbatim from the on-main contract yaml) ----------
ALGORITHM_VERSION_ID_REQUIRED = (
    "algorithm_id",
    "semantic_version",
    "clean_git_commit",
    "input_schema_version",
    "output_schema_version",
    "environment_digest",
)
INPUT_RECORD_ID_REQUIRED = (
    "role",
    "native_schema_version",
    "source_snapshot",
    "transformation_id",
    "artifact_sha256",
    "redistribution_rights",
    "complete_replay_location",
)
INPUT_RECORD_ID_FORBIDDEN = (
    "run_id",
    "algorithm_version_id",
    "output_set_id",
    "attempt_id",
    "retry_count",
    "publication_state",
    "tenant_id",
    "customer_id",
    "request_id",
    "session_id",
    "user_id",
)
RUN_ID_FORBIDDEN = (
    "output_set_id",
    "attempt_id",
    "retry_count",
    "publication_state",
    "tenant_id",
    "customer_id",
    "request_id",
    "api_request_id",
    "session_id",
    "user_id",
)

# Terminal, identity-bearing run statuses. ``indeterminate_failure`` is
# non-terminal and mints NO identity (no attempt/retry identity ever exists:
# a rerun of the same canonical inputs is the same run_id).
IDENTITY_BEARING_STATUSES = frozenset({"succeeded", "reproducible_failure"})
NON_TERMINAL_STATUSES = frozenset({"indeterminate_failure"})


class IdentityError(ValueError):
    """Raised when identity inputs violate the canonical-serialization contract."""


class EligibilityError(IdentityError):
    """Raised (fail-closed) when a run is not eligible to mint an identity."""


class OutputMismatchError(IdentityError):
    """Raised when an exact rerun's output digest differs from the recorded one."""


# ---------------------------------------------------------------------------
# canonical serialization (RFC 8785 / JCS, compact, stdlib-only)
# ---------------------------------------------------------------------------

# A bare "units-bearing numeric": a number immediately followed by a unit token
# (letters / % / common symbols) with nothing else. Dates ("2026-07-11") and
# plain identifiers do not match, so they are not falsely rejected.
_UNITS_BEARING_RE = re.compile(
    r"^\s*[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?\s*[A-Za-z%µμ°Ω/·]+\s*$"
)


def _reject_if_units_bearing(text: str) -> None:
    if _UNITS_BEARING_RE.match(text):
        raise IdentityError(
            f"bare units-bearing numeric {text!r} rejected; represent a physical "
            "quantity as an explicit {'value': ..., 'unit': ...} pair"
        )


def _number_canonical(value) -> str:
    """Canonical decimal string for a number (no float round-trip, no exponent)."""
    if isinstance(value, bool):  # defensive; bool handled before this is reached
        raise IdentityError("bool is not a number")
    if isinstance(value, float):
        # str(float) yields the shortest round-trippable decimal, so we never
        # bake in binary-float noise the way Decimal(float) would.
        if value != value or value in (float("inf"), float("-inf")):
            raise IdentityError(f"non-finite number not permitted: {value!r}")
        dec = Decimal(str(value))
    elif isinstance(value, int):
        dec = Decimal(value)
    elif isinstance(value, Decimal):
        if not value.is_finite():
            raise IdentityError(f"non-finite number not permitted: {value!r}")
        dec = value
    else:  # pragma: no cover - guarded by caller
        raise IdentityError(f"unsupported numeric type: {type(value).__name__}")
    if dec == 0:
        return "0"
    # normalize() collapses 5.00 -> 5 and 1000 -> 1E+3; format 'f' re-expands to
    # plain decimal so 1e3, 1000 and Decimal('1E3') all render as "1000".
    return format(dec.normalize(), "f")


def _canon(value) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        _reject_if_units_bearing(value)
        return json.dumps(unicodedata.normalize("NFC", value), ensure_ascii=False)
    if isinstance(value, (int, float, Decimal)):
        return _number_canonical(value)
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(_canon(v) for v in value) + "]"
    if isinstance(value, dict):
        parts = []
        # RFC 8785: sort object keys by UTF-16 code-unit order.
        for key in sorted(value, key=lambda k: _utf16_sort_key(k)):
            if not isinstance(key, str):
                raise IdentityError(
                    f"object keys must be strings, got {type(key).__name__}"
                )
            enc_key = json.dumps(unicodedata.normalize("NFC", key), ensure_ascii=False)
            parts.append(enc_key + ":" + _canon(value[key]))
        return "{" + ",".join(parts) + "}"
    raise IdentityError(f"cannot canonicalize value of type {type(value).__name__}")


def _utf16_sort_key(key) -> bytes:
    if not isinstance(key, str):
        raise IdentityError(f"object keys must be strings, got {type(key).__name__}")
    return unicodedata.normalize("NFC", key).encode("utf-16-be")


def canonicalize(value) -> str:
    """Return the canonical (JCS) serialization of ``value`` as text.

    This is the single canonical-serialization owner for the epic. It is
    total for JSON-shaped values (``dict``/``list``/``str``/``int``/``float``/
    ``Decimal``/``bool``/``None``) and raises :class:`IdentityError` for
    non-serializable values or bare units-bearing numeric strings.
    """
    return _canon(value)


def canonical_digest(identity_type: str, components) -> str:
    """SHA-256 hex digest of ``components``, domain-separated by ``identity_type``.

    The digest input is ``"{identity_type}\\n{CANONICALIZATION_VERSION}\\n{canon}"``
    so (a) different id types never collide on equal component bytes and (b) a
    serialization-scheme bump mints new ids for the same components.
    """
    if not isinstance(identity_type, str) or not identity_type:
        raise IdentityError("identity_type must be a non-empty string")
    canon = canonicalize(components)
    payload = f"{identity_type}\n{CANONICALIZATION_VERSION}\n{canon}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# membership validation
# ---------------------------------------------------------------------------

def _validate_membership(id_type, components, *, required, forbidden=()):
    if not isinstance(components, dict):
        raise IdentityError(f"{id_type} components must be a dict")
    present = set(components)
    forb = present & set(forbidden)
    if forb:
        raise IdentityError(f"{id_type} forbids run-scoped/PII components: {sorted(forb)}")
    missing = [k for k in required if k not in components or components[k] is None]
    if missing:
        raise IdentityError(f"{id_type} missing required components: {missing}")
    extra = present - set(required)
    if extra:
        raise IdentityError(f"{id_type} has unexpected components: {sorted(extra)}")


# ---------------------------------------------------------------------------
# identity constructors
# ---------------------------------------------------------------------------

def algorithm_version_id(
    *,
    algorithm_id,
    semantic_version,
    clean_git_commit,
    input_schema_version,
    output_schema_version,
    environment_digest,
) -> str:
    """Mint an ``algorithm_version_id`` binding all six required components.

    ``clean_git_commit`` MUST be a commit already VERIFIED clean/known upstream
    (see :func:`check_eligibility`); this constructor only binds it.
    """
    components = {
        "algorithm_id": algorithm_id,
        "semantic_version": semantic_version,
        "clean_git_commit": clean_git_commit,
        "input_schema_version": input_schema_version,
        "output_schema_version": output_schema_version,
        "environment_digest": environment_digest,
    }
    _validate_membership(
        "algorithm_version_id", components, required=ALGORITHM_VERSION_ID_REQUIRED
    )
    return canonical_digest("algorithm_version_id", components)


def input_record_id(components: dict) -> str:
    """Mint an ``input_record_id`` from its required components.

    Rejects the forbidden run-scoped / PII components. The exact canonical field
    membership beyond required/forbidden is #3430's concern; values are consumed
    as given.
    """
    _validate_membership(
        "input_record_id",
        components,
        required=INPUT_RECORD_ID_REQUIRED,
        forbidden=INPUT_RECORD_ID_FORBIDDEN,
    )
    return canonical_digest("input_record_id", components)


def input_set_id(inputs) -> str:
    """Mint an ``input_set_id`` from ``(role, input_record_id)`` pairs.

    ``inputs`` is an iterable of ``(role, input_record_id)`` tuples or
    ``{"role": ..., "input_record_id": ...}`` mappings. Pairs are sorted so the
    set identity is order-independent. ``input_record_id`` values are opaque
    (they may be produced by #3430) -- this constructor does not re-derive them.
    """
    pairs = []
    for item in inputs:
        if isinstance(item, dict):
            role = item["role"]
            rec_id = item["input_record_id"]
        else:
            role, rec_id = item
        if role is None or rec_id is None:
            raise IdentityError("each input needs an explicit (role, input_record_id)")
        pairs.append((role, rec_id))
    pairs.sort(key=lambda p: (_utf16_sort_key(str(p[0])), _utf16_sort_key(str(p[1]))))
    components = {
        "inputs": [{"role": r, "input_record_id": rid} for r, rid in pairs]
    }
    return canonical_digest("input_set_id", components)


def run_id(*, algorithm_version_id, input_set_id, execution_parameters, seed) -> str:
    """Mint a ``run_id`` from ``algorithm_version_id`` + ``input_set_id`` +
    ``execution_parameters`` + ``seed``.

    EXCLUDES outputs (an exact rerun -> same ``run_id``). ``input_set_id`` is an
    opaque injected digest. ``execution_parameters`` are run-control knobs only
    (distinct from #3430 ``parameter_set`` inputs) and must not smuggle any
    run-scoped/PII forbidden component. Seed and execution_parameters must be
    explicit (fail-closed against implicit defaults).
    """
    if seed is None:
        raise IdentityError("implicit_seed: an explicit seed is required")
    if execution_parameters is None:
        raise IdentityError(
            "implicit_execution_default: explicit execution_parameters are required"
        )
    if not isinstance(execution_parameters, dict):
        raise IdentityError("execution_parameters must be a dict")
    forb = set(execution_parameters) & set(RUN_ID_FORBIDDEN)
    if forb:
        raise IdentityError(
            f"run_id forbids run-scoped/PII components in execution_parameters: {sorted(forb)}"
        )
    if algorithm_version_id is None or input_set_id is None:
        raise IdentityError("run_id requires algorithm_version_id and input_set_id")
    components = {
        "algorithm_version_id": algorithm_version_id,
        "input_set_id": input_set_id,
        "execution_parameters": execution_parameters,
        "seed": seed,
    }
    return canonical_digest("run_id", components)


# ---------------------------------------------------------------------------
# fail-closed eligibility
# ---------------------------------------------------------------------------

def check_eligibility(
    *,
    clean_tree: bool,
    commit,
    commit_known: bool,
    input_schema_version,
    output_schema_version,
    environment_digest,
    seed,
    execution_parameters,
) -> bool:
    """Fail-closed gate: raise :class:`EligibilityError` unless a run may mint id.

    Rejects (all -> reject): ``dirty_source``, ``unknown_revision`` (unknown or
    shallow commit), ``unpinned_schema``, ``missing_environment_digest``,
    ``implicit_seed``, ``implicit_execution_default``.
    """
    reasons = []
    if not clean_tree:
        reasons.append("dirty_source")
    if not commit_known or not commit:
        reasons.append("unknown_revision")
    if not input_schema_version or not output_schema_version:
        reasons.append("unpinned_schema")
    if not environment_digest:
        reasons.append("missing_environment_digest")
    if seed is None:
        reasons.append("implicit_seed")
    if execution_parameters is None:
        reasons.append("implicit_execution_default")
    if reasons:
        raise EligibilityError(f"run not eligible to mint identity: {reasons}")
    return True


# ---------------------------------------------------------------------------
# high-level derivation from a VERIFIED clean context
# ---------------------------------------------------------------------------

def derive_run_identity(
    *,
    algorithm_id,
    semantic_version,
    clean_git_commit,
    input_schema_version,
    output_schema_version,
    environment_digest,
    inputs,
    execution_parameters,
    seed,
    commit_known: bool = True,
    clean_tree: bool = True,
) -> dict:
    """Re-derive ``{algorithm_version_id, input_set_id, run_id}`` from a VERIFIED
    clean context.

    Deliberately consumes NEITHER the envelope ``input_hash`` NOR the best-effort
    ``code_version.git_sha`` -- those are evidence, not identity. Identity binds
    the ``clean_git_commit`` proven clean here (fail-closed via
    :func:`check_eligibility`) plus declared env/schema pins plus canonical inputs.
    Reads nothing from the process environment or cwd, so the same canonical
    inputs yield the same ``run_id`` on any machine.
    """
    check_eligibility(
        clean_tree=clean_tree,
        commit=clean_git_commit,
        commit_known=commit_known,
        input_schema_version=input_schema_version,
        output_schema_version=output_schema_version,
        environment_digest=environment_digest,
        seed=seed,
        execution_parameters=execution_parameters,
    )
    avid = algorithm_version_id(
        algorithm_id=algorithm_id,
        semantic_version=semantic_version,
        clean_git_commit=clean_git_commit,
        input_schema_version=input_schema_version,
        output_schema_version=output_schema_version,
        environment_digest=environment_digest,
    )
    isid = input_set_id(inputs)
    rid = run_id(
        algorithm_version_id=avid,
        input_set_id=isid,
        execution_parameters=execution_parameters,
        seed=seed,
    )
    return {"algorithm_version_id": avid, "input_set_id": isid, "run_id": rid}


# ---------------------------------------------------------------------------
# terminal-status identity semantics
# ---------------------------------------------------------------------------

def mints_identity(status: str) -> bool:
    """True iff ``status`` is terminal + identity-bearing (succeeded /
    reproducible_failure). ``indeterminate_failure`` is non-terminal -> False."""
    return status in IDENTITY_BEARING_STATUSES


def is_terminal_status(status: str) -> bool:
    return status in IDENTITY_BEARING_STATUSES


def run_identity_for_status(status: str, run_id_value: str):
    """Return ``run_id_value`` for an identity-bearing terminal status, else
    ``None`` for a non-terminal status (no attempt/retry identity is ever minted).
    """
    if status in IDENTITY_BEARING_STATUSES:
        return run_id_value
    if status in NON_TERMINAL_STATUSES:
        return None
    raise IdentityError(f"unknown run status: {status!r}")


# ---------------------------------------------------------------------------
# output-equality POLICY (digest owned by #3431; policy owned here)
# ---------------------------------------------------------------------------

def assert_output_equality(recorded_digest, observed_digest, *, prior_record=None) -> bool:
    """Enforce the output-equality policy for an exact rerun.

    The ``output_equality_digest`` itself is #3431's concern; here we only apply
    the ``mismatch_action: reject_without_mutation`` POLICY. On mismatch we raise
    :class:`OutputMismatchError` and mutate NOTHING (``prior_record`` is never
    written to). Equal digests are accepted.
    """
    if recorded_digest != observed_digest:
        raise OutputMismatchError(
            "output_equality mismatch under "
            f"{OUTPUT_EQUALITY_DEFAULT}: recorded={recorded_digest!r} "
            f"observed={observed_digest!r}; reject_without_mutation"
        )
    return True
