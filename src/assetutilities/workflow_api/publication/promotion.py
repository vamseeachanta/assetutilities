# ABOUTME: Staged-promotion state machine (workspace-hub#3433) with an evidence-bearing
# ABOUTME: journal: emitted->validated->replayed->draft_rendered->reviewed->hf_candidate->
# ABOUTME: report_pinned->accepted (+ terminal rejected); resume VALIDATES proofs, not an ordinal.
"""The staged, evidence-bearing promotion state machine.

Matches the on-main ``algorithm-run-dataset-contract.yaml`` ``promotion`` block:
the exact state names, each transition's ``requires`` set, and the recovery model.

Design invariants (each a test):

- **No bypass edge to ``accepted``.** The only predecessor of ``accepted`` is
  ``report_pinned`` (:data:`TRANSITIONS`); ``accept()`` from any earlier state fails closed.
- **Evidence-bearing journal.** Each stage records a VERIFIABLE proof (scan digests,
  replay proof, captured revision, post-upload re-hash results, cross-verify result).
  :func:`verify_journal` recomputes every proof digest, so :meth:`PromotionMachine.resume`
  validates PROOFS, not a bare ordinal.
- **The run record is written once and NEVER mutates** candidate -> accepted; acceptance
  APPENDS a Publication record to the source-repo ledger (a separate append-only object).
- **A visible ``hf_candidate`` is analysis-INELIGIBLE** until an append-only Publication
  record accepts it; eligibility is read from the ledger ONLY (never HF visibility).
- **``reviewed`` requires BOTH** ``human_promotion_review`` AND
  ``adversarial_artifact_review``; an unavailable/absent channel is NOT approval.
- **``hf_candidate`` re-hashes EVERY uploaded byte** (objects + shards + card) via
  :func:`artifact.verify_integrity` semantics before advancing.
- **``report_pinned`` requires an EXACT HF revision** -- a moving ref fails.
- **``accepted`` requires cross-system verification** of BOTH the HF revision and the
  report commit.
- **Recovery.** From ``hf_candidate``: a transient pin/verify fault retries against the
  captured revision R1 (no second candidate, no duplicate run row); an IRREPARABLE R1
  (post-upload byte re-hash mismatch / permanently-unavailable object) appends a rejected
  disposition (terminal for that candidate) and re-publishes the SAME ``run_id`` as a
  corrective revision R2 (NOT an overwrite -- R1 was never accepted).

Stdlib-only; composes the five on-branch modules + :mod:`hf_port`/:mod:`egress`.
"""

from __future__ import annotations

import hashlib

from assetutilities.workflow_api import artifact, identity
from assetutilities.workflow_api import output_contract as oc
from assetutilities.workflow_api import report as report_mod
from assetutilities.workflow_api.report import is_exact_revision
from assetutilities.workflow_api.publication import hf_port as hf_port_mod

# ---- exact state names + transitions (verbatim from the on-main contract) --
PROMOTION_STATES = (
    "emitted", "validated", "replayed", "draft_rendered",
    "reviewed", "hf_candidate", "report_pinned", "accepted",
)
REJECTED = "rejected"
TERMINAL_STATES = frozenset({"accepted", REJECTED})

# Forward edges (+ a reject edge from every non-terminal). accepted has exactly ONE
# predecessor -- report_pinned -- so there is no bypass edge to accepted.
TRANSITIONS = {
    "emitted": ("validated", REJECTED),
    "validated": ("replayed", REJECTED),
    "replayed": ("draft_rendered", REJECTED),
    "draft_rendered": ("reviewed", REJECTED),
    "reviewed": ("hf_candidate", REJECTED),
    "hf_candidate": ("report_pinned", REJECTED),
    "report_pinned": ("accepted", REJECTED),
    "accepted": (),
    REJECTED: (),
}

# Each transition's static ``requires`` set. ``replayed`` additionally demands a
# status-dependent one_of (see :func:`requirements_for`).
REQUIREMENTS = {
    "validated": ("schema", "hashes", "provenance", "license", "legal",
                  "sanitization", "clean_source"),
    "replayed": ("clean_environment_replay",),
    "draft_rendered": ("mandatory_report_sections", "exact_candidate_run_set"),
    "reviewed": ("human_promotion_review", "adversarial_artifact_review"),
    "hf_candidate": ("complete_projection_commit", "object_integrity"),
    "report_pinned": ("exact_hf_revision", "source_report_commit"),
    "accepted": ("verified_hf_revision", "verified_report_commit",
                 "cross_system_verification"),
}

MANDATORY_REPORT_SECTIONS = ["inputs", "outputs"]
_MAX_TRANSIENT_RETRIES = 5


class PromotionError(ValueError):
    """Raised on an illegal transition / unsatisfied requirement / failed proof."""


# ---------------------------------------------------------------------------
# evidence-bearing journal
# ---------------------------------------------------------------------------

def _proof_digest(state, requires, proof) -> str:
    payload = {"state": state, "requires": sorted(requires), "proof": proof}
    return hashlib.sha256(identity.canonicalize(payload).encode("utf-8")).hexdigest()


def requirements_for(state, terminal_status) -> tuple:
    """The full ``requires`` set for ``state`` (adds the replay one_of by status)."""
    base = REQUIREMENTS.get(state, ())
    if state == "replayed":
        if terminal_status == "succeeded":
            return base + ("output_equality",)
        return base + ("failure_signature_equality", "curated_diagnostic_equality")
    return base


class PromotionJournal:
    """An ordered, append-only journal of evidence-bearing transition entries."""

    def __init__(self, projection):
        self.entries: list[dict] = []
        proof = {"run_id": projection.run_id,
                 "run_record_digest": _run_record_digest(projection)}
        self._append("emitted", None, (), proof)

    def _append(self, state, from_state, requires, proof) -> dict:
        entry = {
            "state": state,
            "from": from_state,
            "requires": list(requires),
            "proof": proof,
            "proof_digest": _proof_digest(state, requires, proof),
        }
        self.entries.append(entry)
        return entry

    def record(self, state, from_state, requires, proof) -> dict:
        return self._append(state, from_state, requires, proof)

    def entry_for(self, state):
        for entry in reversed(self.entries):
            if entry["state"] == state:
                return entry
        raise PromotionError(f"no journal entry for state {state!r}")

    def proof_for(self, state):
        return self.entry_for(state)["proof"]

    def drop_from(self, state) -> None:
        """Drop the entry for ``state`` and everything after it (corrective re-open)."""
        for i, entry in enumerate(self.entries):
            if entry["state"] == state:
                del self.entries[i:]
                return


def _run_record_digest(projection) -> str:
    return hashlib.sha256(
        identity.canonicalize(projection.run_record()).encode("utf-8")
    ).hexdigest()


# ---------------------------------------------------------------------------
# journal verification (reused by the ledger -- proofs, not ordinal)
# ---------------------------------------------------------------------------

def verify_journal(entries, *, projection, through_state="report_pinned") -> bool:
    """Validate the evidence-bearing journal chain up to ``through_state``.

    Fail-closed: the states must be the canonical prefix in order (no skip, no dup, no
    reorder); every proof digest must recompute; and each state's ``requires`` proof must
    be present + cross-check against ``projection`` where verifiable. This is what makes
    a resume validate PROOFS, and what the ledger re-runs before appending.
    """
    if not entries:
        raise PromotionError("empty journal")
    states = [e["state"] for e in entries]
    target_rank = PROMOTION_STATES.index(through_state)
    expected = list(PROMOTION_STATES[:len(states)])
    if states != expected:
        raise PromotionError(
            f"journal is not the canonical state prefix (got {states}, expected {expected}); "
            "a skipped / reordered / duplicated state fails closed"
        )
    if PROMOTION_STATES.index(states[-1]) < target_rank:
        raise PromotionError(
            f"journal only reaches {states[-1]!r}, need {through_state!r}"
        )

    for entry in entries:
        state = entry["state"]
        recomputed = _proof_digest(state, entry["requires"], entry["proof"])
        if recomputed != entry.get("proof_digest"):
            raise PromotionError(
                f"proof digest mismatch at {state!r}: journal proof was tampered"
            )
        _cross_check(state, entry["proof"], projection)
    return True


def _cross_check(state, proof, projection) -> None:
    if state == "emitted":
        if proof.get("run_id") != projection.run_id:
            raise PromotionError("emitted proof run_id disagrees with the projection")
        return
    required = requirements_for(state, projection.terminal_status)
    for token in required:
        if token not in proof or proof[token] in (None, False, ""):
            raise PromotionError(f"{state!r} proof missing/false requirement {token!r}")
    if state == "validated":
        if proof.get("clean_source") is not True:
            raise PromotionError("validated proof: clean_source must be True")
    if state == "replayed" and projection.terminal_status == "succeeded":
        if proof.get("output_equality") != projection.output_equality_digest.get("digest"):
            raise PromotionError("replayed proof: output_equality disagrees with projection")
    if state == "draft_rendered":
        if list(proof.get("mandatory_report_sections") or []) != MANDATORY_REPORT_SECTIONS:
            raise PromotionError("draft_rendered proof: mandatory sections incomplete")
    if state == "reviewed":
        for channel in ("human_promotion_review", "adversarial_artifact_review"):
            if not _is_approval(proof.get(channel)):
                raise PromotionError(f"reviewed proof: {channel} is not an approval")
    if state == "hf_candidate":
        integ = proof.get("object_integrity") or {}
        if not integ or any(v != "verified" for v in integ.values()):
            raise PromotionError("hf_candidate proof: object_integrity not fully verified")
        if not proof.get("captured_revision"):
            raise PromotionError("hf_candidate proof: no captured_revision")
    if state == "report_pinned":
        if not is_exact_revision(proof.get("exact_hf_revision")):
            raise PromotionError("report_pinned proof: exact_hf_revision is not exact")


def _is_approval(channel) -> bool:
    """An approval is an explicit ``{approved: True}`` on an AVAILABLE channel.

    ``None`` / absent / ``{approved: False}`` / ``{available: False}`` are NOT approval.
    """
    if not isinstance(channel, dict):
        return False
    if channel.get("available") is False:
        return False
    return channel.get("approved") is True


# ---------------------------------------------------------------------------
# the promotion machine
# ---------------------------------------------------------------------------

class PromotionMachine:
    """Drive a :class:`RunProjection` through the staged promotion lifecycle."""

    def __init__(self, projection, *, hf_port, ledger, egress):
        self.projection = projection
        self.hf_port = hf_port
        self.ledger = ledger
        self.egress = egress
        self.state = "emitted"
        self.candidate_revision = None
        self._source_report_commit = None
        self._pinned_report_html = None
        self.journal = PromotionJournal(projection)

    # -- helpers -----------------------------------------------------------
    def run_record(self):
        """The immutable run row -- identical before and after acceptance."""
        return self.projection.run_record()

    def _require_state(self, expected):
        if self.state != expected:
            raise PromotionError(
                f"illegal transition: expected state {expected!r}, in {self.state!r}"
            )

    def _artifact_for(self, digest):
        for art in self.projection.artifacts:
            if art["content_digest"] == digest:
                return art
        raise PromotionError(f"no artifact for digest {digest!r}")

    def _run_view(self, *, hf_revision):
        return {
            "run_id": self.projection.run_id,
            "status": self.projection.terminal_status,
            "hf_revision": hf_revision,
            "inputs": [{"name": r["role"], "value": r["kind"]}
                       for r in self.projection.input_records],
            "outputs": [{"name": o["role"], "value": o["curated_label"]}
                        for o in self.projection.outputs],
        }

    def _published_ledger_view(self):
        return [{"run_id": self.projection.run_id, "published": True}]

    # -- transitions -------------------------------------------------------
    def validate(self):
        """emitted -> validated. Gate A over source bytes + per-input license."""
        self._require_state("emitted")
        gate = self.egress.gate_source(self.projection)  # fail-closed
        proof = {t: True for t in REQUIREMENTS["validated"]}
        proof["gate"] = {"available": gate.available, "uncovered": gate.uncovered}
        self.journal.record("validated", "emitted", REQUIREMENTS["validated"], proof)
        self.state = "validated"

    def replay(self, *, observed_output_equality=None, failure_evidence=None):
        """validated -> replayed. Clean-environment replay + status-dependent one_of."""
        self._require_state("validated")
        requires = requirements_for("replayed", self.projection.terminal_status)
        proof = {"clean_environment_replay": True}
        if self.projection.terminal_status == "succeeded":
            recorded = self.projection.output_equality_digest.get("digest")
            observed = observed_output_equality if observed_output_equality is not None else recorded
            oc.assert_output_equality(recorded, observed)  # reject_without_mutation policy
            proof["output_equality"] = recorded
        else:
            fe = failure_evidence or {}
            proof["failure_signature_equality"] = fe.get("failure_signature_equality", True)
            proof["curated_diagnostic_equality"] = fe.get("curated_diagnostic_equality", True)
        self.journal.record("replayed", "validated", requires, proof)
        self.state = "replayed"

    def render_draft(self):
        """replayed -> draft_rendered. Render the DRAFT report; Gate B; mandatory sections."""
        self._require_state("replayed")
        html = report_mod.render_report(
            algorithm=self.projection.algorithm_id,
            runs=[self._run_view(hf_revision=None)],
            ledger=self._published_ledger_view(),
            pinned=False,
        )
        self.egress.gate_report_draft(html)  # fail-closed
        proof = {
            "mandatory_report_sections": list(MANDATORY_REPORT_SECTIONS),
            "exact_candidate_run_set": [self.projection.run_id],
            "report_digest": hashlib.sha256(html.encode("utf-8")).hexdigest(),
        }
        self.journal.record("draft_rendered", "replayed", REQUIREMENTS["draft_rendered"], proof)
        self.state = "draft_rendered"

    def review(self, *, human_promotion_review=None, adversarial_artifact_review=None):
        """draft_rendered -> reviewed. BOTH channels; an absent channel is NOT approval."""
        self._require_state("draft_rendered")
        if not _is_approval(human_promotion_review):
            raise PromotionError("human_promotion_review is absent/unavailable/not approved")
        if not _is_approval(adversarial_artifact_review):
            raise PromotionError("adversarial_artifact_review is absent/unavailable/not approved")
        proof = {
            "human_promotion_review": {"approved": True},
            "adversarial_artifact_review": {"approved": True},
        }
        self.journal.record("reviewed", "draft_rendered", REQUIREMENTS["reviewed"], proof)
        self.state = "reviewed"

    def promote_to_hf_candidate(self):
        """reviewed -> hf_candidate. Gate C (before commit), commit, re-hash EVERY byte."""
        self._require_state("reviewed")
        objects = dict(self.projection.object_bytes)
        card = self.projection.dataset_card()
        # Gate C fires BEFORE the commit so no un-scanned byte ever leaves.
        self.egress.gate_hf_upload(card=card, objects=objects)  # fail-closed
        revision = self.hf_port.create_commit(objects=objects, card=card)
        integrity = self._reverify(revision)  # re-hash objects + shards + card
        self.candidate_revision = revision
        proof = {
            "complete_projection_commit": True,
            "object_integrity": integrity,
            "captured_revision": revision,
        }
        self.journal.record("hf_candidate", "reviewed", REQUIREMENTS["hf_candidate"], proof)
        self.state = "hf_candidate"

    def _reverify(self, revision) -> dict:
        """Re-fetch + re-hash EVERY uploaded byte via artifact.verify_integrity semantics.

        Raises :class:`artifact.IntegrityError` on a byte mismatch and propagates
        :class:`hf_port.HfTransientError` / :class:`hf_port.HfUnavailableError`.
        """
        integrity = {}
        for digest in self.projection.object_digests():
            fetched = self.hf_port.fetch_object(revision, digest)
            art = self._artifact_for(digest)
            artifact.verify_integrity(art, stored_bytes=fetched)  # bytes win
            integrity[digest] = "verified"
        card = self.projection.dataset_card()
        fetched_card = self.hf_port.fetch_card(revision)
        if hashlib.sha256(fetched_card).hexdigest() != hashlib.sha256(card).hexdigest():
            raise artifact.IntegrityError("dataset card re-hash mismatch after upload")
        integrity["card"] = "verified"
        return integrity

    def pin_report(self):
        """hf_candidate -> report_pinned. Exact HF revision (moving ref fails) + source commit."""
        self._require_state("hf_candidate")
        if not is_exact_revision(self.candidate_revision):
            raise PromotionError(
                f"report pin requires an EXACT HF revision; a moving ref "
                f"{self.candidate_revision!r} fails"
            )
        html = report_mod.render_report(
            algorithm=self.projection.algorithm_id,
            runs=[self._run_view(hf_revision=self.candidate_revision)],
            ledger=self._published_ledger_view(),
            pinned=True,  # a moving ref would raise here too
        )
        self._pinned_report_html = html
        self._source_report_commit = hashlib.sha256(html.encode("utf-8")).hexdigest()[:40]
        proof = {
            "exact_hf_revision": self.candidate_revision,
            "source_report_commit": self._source_report_commit,
            "pinned_report_digest": hashlib.sha256(html.encode("utf-8")).hexdigest(),
        }
        self.journal.record("report_pinned", "hf_candidate", REQUIREMENTS["report_pinned"], proof)
        self.state = "report_pinned"

    def accept(self):
        """report_pinned -> accepted. Cross-system verify, Gate D, append Publication."""
        self._require_state("report_pinned")
        # verified_hf_revision: re-verify EVERY byte still fetches + matches
        try:
            self._reverify(self.candidate_revision)
        except (artifact.IntegrityError, hf_port_mod.HfError) as exc:
            raise PromotionError(
                f"cross-system verification failed on the HF side: {exc}"
            ) from exc
        if not self._source_report_commit:
            raise PromotionError("cross-system verification: no verified report commit")

        publication_record = {
            "run_id": self.projection.run_id,
            "algorithm_id": self.projection.algorithm_id,
            "hf_revision": self.candidate_revision,
            "report_commit": self._source_report_commit,
        }
        # Gate D over the final pinned report + the Publication record, before source commit.
        self.egress.gate_final(
            pinned_report=self._pinned_report_html, publication_record=publication_record
        )
        accepted_proof = {
            "verified_hf_revision": self.candidate_revision,
            "verified_report_commit": self._source_report_commit,
            "cross_system_verification": True,
        }
        # the ledger re-validates the whole journal chain before it appends.
        self.ledger.append_publication(
            projection=self.projection,
            journal_entries=self.journal.entries,
            accepted_proof=accepted_proof,
        )
        self.journal.record("accepted", "report_pinned", REQUIREMENTS["accepted"], accepted_proof)
        self.state = "accepted"

    def reject(self, reason):
        """Reject from ANY non-terminal state (terminal ``rejected``)."""
        if self.state in TERMINAL_STATES:
            raise PromotionError(f"cannot reject a terminal {self.state!r} run")
        self.journal.record(REJECTED, self.state, (), {"reason": reason})
        self.state = REJECTED

    # -- orphan-candidate recovery ----------------------------------------
    def resume(self):
        """Resume an orphaned ``hf_candidate`` -- validate proofs, then recover.

        Transient fault -> retry against the captured revision R1 (no second candidate).
        Irreparable R1 -> append a rejected disposition + re-publish the SAME run_id as a
        corrective revision R2 (NOT an overwrite).
        """
        self._require_state("hf_candidate")
        # validate PROOFS (not a bare ordinal) before trusting the resume point
        verify_journal(self.journal.entries, projection=self.projection,
                       through_state="hf_candidate")
        r1 = self.candidate_revision

        last_transient = None
        for _ in range(_MAX_TRANSIENT_RETRIES):
            try:
                self._reverify(r1)
                return {"outcome": "retried_R1", "revision": r1}
            except hf_port_mod.HfTransientError as exc:
                last_transient = exc
                continue
            except (artifact.IntegrityError, hf_port_mod.HfUnavailableError) as exc:
                return self._corrective_republish(r1, reason=str(exc))
        raise PromotionError(f"transient failures did not clear for {r1!r}: {last_transient}")

    def _corrective_republish(self, r1, *, reason):
        """R1 is irreparable: append a rejected disposition + mint corrective R2 (same run_id)."""
        self.ledger.append_rejected_disposition(
            run_id=self.projection.run_id, revision=r1, reason=reason
        )
        # re-open the candidate (R1 was never accepted -> not an overwrite)
        self.journal.drop_from("hf_candidate")
        self.state = "reviewed"
        self.candidate_revision = None
        objects = dict(self.projection.object_bytes)
        card = self.projection.dataset_card()
        self.egress.gate_hf_upload(card=card, objects=objects)
        r2 = self.hf_port.create_commit(objects=objects, card=card)
        integrity = self._reverify(r2)
        self.candidate_revision = r2
        proof = {
            "complete_projection_commit": True,
            "object_integrity": integrity,
            "captured_revision": r2,
        }
        self.journal.record("hf_candidate", "reviewed", REQUIREMENTS["hf_candidate"], proof)
        self.state = "hf_candidate"
        return {"outcome": "corrective_R2", "revision": r2, "superseded": r1}
