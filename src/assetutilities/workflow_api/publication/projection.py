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

    def dataset_card(self) -> bytes:
        """The dataset card bytes (a generated default unless a card was supplied)."""
        if self._card is not None:
            return self._card
        return (
            f"# Algorithm dataset: {self.algorithm_id}\n\n"
            f"run_id: {self.run_id}\n"
            f"algorithm_version_id: {self.algorithm_version_id}\n"
            f"terminal_status: {self.terminal_status}\n"
        ).encode("utf-8")

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
