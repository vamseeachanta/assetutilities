# ABOUTME: RunProjection builder (workspace-hub#3433): binds the five record types
# ABOUTME: (identity/artifact/inputs/output/metrics) under ONE run_id, strict-identity-bound,
# ABOUTME: with the HF data-plane vs source-repo authority-plane dataset layout constants.
"""Project a completed run into a publishable ``RunProjection``.

A :class:`RunProjection` binds the five on-branch record types under a SINGLE
identity and is the unit the promotion machine drives to Hugging Face + the
source-repo report.

Design invariants (from the approved+remediated #3433 plan):

- **Strict identity bind.** Identity is RE-DERIVED via :func:`identity.derive_run_identity`
  from the declared clean context; the input RECORDS' :func:`inputs.canonical_input_set_digest`
  MUST equal that identity's ``input_set_id`` (the records and the identity agree), every
  metric observation MUST carry the projection's ``run_id`` + ``algorithm_id``, and every
  output ``artifact_ref`` MUST resolve to a projected artifact. Envelope hashes are stored
  as EVIDENCE only and never participate in identity.
- **Object integrity at projection time.** Each artifact's ``content_digest`` is re-hashed
  against the supplied ``object_bytes`` via :func:`artifact.verify_integrity`, so a tampered
  byte is rejected before anything is staged for upload.
- **Two planes.** The HF **data plane** holds content-addressed runs/inputs/outputs/metrics/
  objects (objects at :func:`artifact.storage_locator_for` paths). The SOURCE-REPO **authority
  plane** holds the rolling report + the append-only ``publications.jsonl`` ledger. The
  Publication acceptance ledger lives in the SOURCE REPO, NOT the HF dataset.

Stdlib-only (composes :mod:`identity`, :mod:`artifact`, :mod:`inputs`,
:mod:`output_contract`).
"""

from __future__ import annotations

from assetutilities.workflow_api import artifact, identity, inputs

# ---- dataset layout constants ---------------------------------------------
# HF DATA plane: content-addressed tables + the objects store.
HF_DATA_PLANE_TABLES = ("runs", "inputs", "outputs", "metrics", "objects")
# SOURCE-REPO AUTHORITY plane: the rolling report + the append-only publication ledger.
SOURCE_REPO_AUTHORITY_PLANE = ("report", "publications_ledger")

# The rolling report's stable path pattern (moving revision NOT allowed; see promotion).
REPORT_PATH_PATTERN = "reports/algorithms/{algorithm_id}/index.html"


# ---- dataset card (valid HF dataset card: YAML frontmatter + Markdown body) ---
# The run-ledger is aceengineer's own algorithm-run data (a content-addressed object
# store, NOT tabular parquet), so the license is the HF ``other`` identifier and NO
# ``configs:`` block is emitted (a fabricated one would make the datasets viewer error
# on a store that has no tabular tables).
DATASET_CARD_LICENSE = "other"
DATASET_CARD_TAGS = ("algorithm-runs", "reproducible", "digitalmodel")


def _yaml_dq(value) -> str:
    """A double-quoted YAML scalar with the two structural chars escaped.

    Stdlib-only (this module imports no yaml); sufficient for the plain string values we
    emit (algorithm ids / repo ids), which never contain control characters.
    """
    text = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def render_dataset_card(
    *,
    algorithm_id,
    run_id=None,
    algorithm_version_id=None,
    terminal_status=None,
    repo_id=None,
    run_count=None,
    license=DATASET_CARD_LICENSE,
    tags=DATASET_CARD_TAGS,
) -> bytes:
    """Render a VALID Hugging Face dataset card for an algorithm-run ledger.

    Returns ``<YAML frontmatter>\\n<Markdown body>`` bytes. The frontmatter carries a
    valid ``license`` / ``pretty_name`` / ``tags`` (so the hub does not warn about missing
    metadata) and deliberately NO ``configs:`` block -- this is a content-addressed object
    store, not tabular parquet, so a fabricated configs block would make the datasets
    viewer error. The body documents the actual (workspace-hub#3433) contract.

    Parameterized (``algorithm_id`` / ``repo_id`` / ``run_count`` ...) so it is generic
    across repos and pilots, never hardcoded to one dataset.
    """
    pretty = f"{algorithm_id} algorithm-run ledger"
    front = [
        "---",
        f"license: {license}",
        f"pretty_name: {_yaml_dq(pretty)}",
        "tags:",
        *[f"- {t}" for t in tags],
        "---",
    ]

    repo_line = f"`{repo_id}`" if repo_id else "this Hugging Face dataset"
    count_note = (
        f" It currently holds {run_count} accepted run(s)."
        if run_count is not None
        else ""
    )
    version_line = (
        f"- **algorithm version:** `{algorithm_version_id}`\n"
        if algorithm_version_id
        else ""
    )
    latest_lines = ""
    if run_id:
        latest_lines = (
            f"- **latest run id:** `{run_id}`"
            + (f" (`{terminal_status}`)" if terminal_status else "")
            + "\n"
        )

    body = f"""# {pretty}

A repository-linked, content-addressed **algorithm-run ledger** for the `{algorithm_id}`
algorithm, produced by the workspace-hub#3433 publication pipeline. {repo_line} is the
**data plane**: it stores the immutable, reproducible artifacts of individual algorithm
runs.{count_note}

{version_line}{latest_lines}
## Layout

```
objects/<sha256[:2]>/<sha256>
```

Every run artifact is stored **content-addressed** at a path derived from the SHA-256
digest of its bytes. The path is a pure function of the content, so the objects are
immutable and their integrity is **re-verifiable by re-hashing**: download an object and
confirm its SHA-256 equals the digest in its path (and in the run record).

## Immutability & authority

- Each run is committed at an **immutable revision** (an exact 40-hex commit sha). A
  corrective re-publish is a *new* revision, never an overwrite of an earlier one.
- Eligibility is **not** read from Hugging Face visibility. Each accepted run is referenced
  by the source repository's rolling report and pinned in an append-only `publications.jsonl`
  ledger. **That ledger is the sole eligibility authority** -- an object visible here but
  absent from the ledger is not an accepted run.

## Consuming a run

```python
import hashlib
from huggingface_hub import hf_hub_download

digest = "<sha256-of-the-object>"                       # from the report / ledger
path = f"objects/{{digest[:2]}}/{{digest}}"
local = hf_hub_download(
    repo_id={_yaml_dq(repo_id) if repo_id else '"<owner>/<dataset>"'},
    filename=path,
    revision="<exact-40-hex-revision>",                 # pin the immutable revision
    repo_type="dataset",
)
with open(local, "rb") as fh:
    data = fh.read()
assert hashlib.sha256(data).hexdigest() == digest       # re-hash to verify integrity
```

Pin the exact `revision` and re-hash the bytes: a run is trustworthy only when its
content re-hashes to the digest by which you fetched it.
"""
    return (("\n".join(front) + "\n\n" + body)).encode("utf-8")


class ProjectionError(ValueError):
    """Raised when a run cannot be projected under a single strict identity."""


class RunProjection:
    """An immutable projection of one run's five records under a single identity."""

    __slots__ = (
        "run_id", "algorithm_id", "algorithm_version_id", "input_set_id",
        "terminal_status", "input_records", "artifacts", "outputs",
        "output_equality_digest", "metric_observations", "object_bytes",
        "evidence", "_card",
    )

    def __init__(self, *, run_id, algorithm_id, algorithm_version_id, input_set_id,
                 terminal_status, input_records, artifacts, outputs,
                 output_equality_digest, metric_observations, object_bytes,
                 evidence, card=None):
        self.run_id = run_id
        self.algorithm_id = algorithm_id
        self.algorithm_version_id = algorithm_version_id
        self.input_set_id = input_set_id
        self.terminal_status = terminal_status
        self.input_records = tuple(input_records)
        self.artifacts = tuple(artifacts)
        self.outputs = tuple(outputs)
        self.output_equality_digest = dict(output_equality_digest)
        self.metric_observations = tuple(metric_observations)
        self.object_bytes = dict(object_bytes)
        self.evidence = dict(evidence or {})
        self._card = card

    # -- derived views -----------------------------------------------------
    def object_digests(self):
        """The content_digests of every projected artifact (content-addressed)."""
        return tuple(a["content_digest"] for a in self.artifacts)

    def storage_locators(self):
        """``{content_digest: objects/<..>/<digest>}`` for each artifact."""
        return {d: artifact.storage_locator_for(d) for d in self.object_digests()}

    def run_record(self):
        """The stable, identity-bearing run row (written ONCE, never mutated)."""
        return {
            "run_id": self.run_id,
            "algorithm_id": self.algorithm_id,
            "algorithm_version_id": self.algorithm_version_id,
            "input_set_id": self.input_set_id,
            "terminal_status": self.terminal_status,
            "output_equality_digest": self.output_equality_digest.get("digest"),
            "object_digests": sorted(self.object_digests()),
        }

    def dataset_card(self, *, repo_id=None, run_count=None) -> bytes:
        """The dataset card bytes (a generated default unless a card was supplied).

        The generated default is a VALID Hugging Face dataset card -- YAML frontmatter
        (``license`` / ``pretty_name`` / ``tags``) plus a Markdown body that describes the
        content-addressed algorithm-run ledger contract -- so a live publish no longer
        emits the "empty or missing yaml metadata in repo card" warning. ``repo_id`` and
        ``run_count`` are optional context (the projection is a single run and does not
        itself know the destination repo id or the repo-wide run total); pass them from the
        publisher when known.
        """
        if self._card is not None:
            return self._card
        return render_dataset_card(
            algorithm_id=self.algorithm_id,
            run_id=self.run_id,
            algorithm_version_id=self.algorithm_version_id,
            terminal_status=self.terminal_status,
            repo_id=repo_id,
            run_count=run_count,
        )

    def report_path(self) -> str:
        return REPORT_PATH_PATTERN.format(algorithm_id=self.algorithm_id)

    def with_card(self, card: bytes) -> "RunProjection":
        """Return a copy carrying a replacement dataset card (used to test Gate C)."""
        return RunProjection(
            run_id=self.run_id, algorithm_id=self.algorithm_id,
            algorithm_version_id=self.algorithm_version_id, input_set_id=self.input_set_id,
            terminal_status=self.terminal_status, input_records=self.input_records,
            artifacts=self.artifacts, outputs=self.outputs,
            output_equality_digest=self.output_equality_digest,
            metric_observations=self.metric_observations, object_bytes=self.object_bytes,
            evidence=self.evidence, card=card,
        )


# ---------------------------------------------------------------------------
# builder (strict identity + object integrity)
# ---------------------------------------------------------------------------

def build_projection(*, identity_context, input_records, artifacts, outputs,
                     output_equality_digest, metric_observations, object_bytes,
                     terminal_status, metric_store=None, evidence=None) -> RunProjection:
    """Build a strict-identity-bound :class:`RunProjection` from the five records."""
    if terminal_status not in identity.IDENTITY_BEARING_STATUSES:
        raise ProjectionError(
            f"terminal_status {terminal_status!r} is not identity-bearing "
            f"{sorted(identity.IDENTITY_BEARING_STATUSES)}"
        )

    try:
        ident = identity.derive_run_identity(**identity_context)
    except identity.IdentityError as exc:
        raise ProjectionError(f"identity derivation failed: {exc}") from exc

    algorithm_id = identity_context["algorithm_id"]

    # strict bind: the input RECORDS must reproduce the identity's input_set_id
    records_digest = inputs.canonical_input_set_digest(input_records)
    if records_digest != ident["input_set_id"]:
        raise ProjectionError(
            "input records do not match the declared identity input_set_id "
            f"(records={records_digest!r} identity={ident['input_set_id']!r}); "
            "identity binds the records, not the envelope"
        )

    # object integrity: re-hash every artifact against the supplied bytes
    digests = set()
    for art in artifacts:
        digest = art["content_digest"]
        digests.add(digest)
        if digest not in object_bytes:
            raise ProjectionError(f"artifact {digest!r} has no bytes in object_bytes")
        try:
            artifact.verify_integrity(art, stored_bytes=object_bytes[digest])
        except artifact.ArtifactError as exc:
            raise ProjectionError(
                f"artifact {digest!r} bytes fail integrity at projection time: {exc}"
            ) from exc

    # every output artifact_ref must resolve to a projected artifact
    for out in outputs:
        for ref in out.get("artifact_refs", ()):
            ref_digest = ref["content_digest"] if isinstance(ref, dict) else ref
            if ref_digest not in digests:
                raise ProjectionError(
                    f"output role {out.get('role')!r} references artifact {ref_digest!r} "
                    "not present in the projection"
                )

    # every metric observation must belong to THIS run + algorithm
    for obs in metric_observations:
        if obs.get("run_id") != ident["run_id"]:
            raise ProjectionError(
                f"metric observation run_id {obs.get('run_id')!r} != projection run_id "
                f"{ident['run_id']!r} (strict identity bind)"
            )
        if obs.get("algorithm_id") != algorithm_id:
            raise ProjectionError(
                f"metric observation algorithm_id {obs.get('algorithm_id')!r} != "
                f"{algorithm_id!r}"
            )
        if metric_store is not None and not metric_store.is_registered(
            obs.get("metric_definition_id")
        ):
            raise ProjectionError(
                f"metric observation references an unregistered definition "
                f"{obs.get('metric_definition_id')!r}"
            )

    return RunProjection(
        run_id=ident["run_id"],
        algorithm_id=algorithm_id,
        algorithm_version_id=ident["algorithm_version_id"],
        input_set_id=ident["input_set_id"],
        terminal_status=terminal_status,
        input_records=input_records,
        artifacts=artifacts,
        outputs=outputs,
        output_equality_digest=output_equality_digest,
        metric_observations=metric_observations,
        object_bytes=object_bytes,
        evidence=evidence,
    )
