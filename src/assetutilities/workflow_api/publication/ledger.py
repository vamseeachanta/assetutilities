# ABOUTME: Append-only SOURCE-REPO publication ledger (workspace-hub#3433): re-validates
# ABOUTME: the evidence-bearing journal proofs before appending; SOLE eligibility authority;
# ABOUTME: append_rejected_disposition. Lives in the source repo, NOT the HF dataset.
"""The append-only ``publications.jsonl`` publication ledger.

The Publication acceptance ledger is the authority plane's SOLE eligibility source
and lives in the SOURCE REPO, never in the Hugging Face dataset. A run is
analysis-eligible iff an append-only Publication record accepts it here.

Design invariants (from the approved+remediated #3433 plan):

- **Re-validates the journal proofs before appending.** :meth:`Ledger.append_publication`
  re-runs :func:`promotion.verify_journal` over the FULL chain (emitted -> report_pinned)
  plus the acceptance proof; a malformed / skipped / reordered / hand-built journal is
  rejected. This is NOT a bare append.
- **Sole eligibility authority.** :meth:`Ledger.eligible_run_ids` (reused by
  :func:`report.eligible_run_ids`) is the only thing that makes a run displayable /
  analysis-eligible; Hugging Face visibility is never consulted.
- **Append-only + rejected dispositions.** Records are only ever appended;
  :meth:`Ledger.append_rejected_disposition` records an irreparable candidate's terminal
  disposition without mutating the run row (the run may still be re-published under a
  corrective revision).

Stdlib-only; composes :mod:`promotion` (journal re-validation) + :mod:`report`.
"""

from __future__ import annotations

import json

from assetutilities.workflow_api import report as report_mod
from assetutilities.workflow_api.publication import promotion as promotion_mod

# The ledger is a source-repo artifact (authority plane), never an HF data-plane table.
PUBLICATIONS_LEDGER_PATH = "publications.jsonl"
LEDGER_PLANE = "source_repo"


class LedgerError(ValueError):
    """Raised when a Publication append would violate the append-only / proof contract."""


class Ledger:
    """An append-only source-repo publication ledger (the sole eligibility authority)."""

    def __init__(self, path: str = PUBLICATIONS_LEDGER_PATH):
        self.path = path
        self.plane = LEDGER_PLANE
        self._entries: list[dict] = []

    # -- append-only writes ------------------------------------------------
    def append_publication(self, *, projection, journal_entries, accepted_proof) -> dict:
        """Re-validate the journal proofs, then APPEND a published Publication record."""
        # NOT a bare append: re-run the full evidence-bearing journal verification.
        try:
            promotion_mod.verify_journal(
                journal_entries, projection=projection, through_state="report_pinned"
            )
        except promotion_mod.PromotionError as exc:
            raise LedgerError(f"refusing to publish an invalid journal: {exc}") from exc

        self._validate_accepted_proof(journal_entries, accepted_proof)

        if self.is_eligible(projection.run_id):
            raise LedgerError(
                f"run {projection.run_id!r} is already published (append-only, no re-accept)"
            )

        record = {
            "run_id": projection.run_id,
            "algorithm_id": projection.algorithm_id,
            "hf_revision": accepted_proof["verified_hf_revision"],
            "report_commit": accepted_proof["verified_report_commit"],
            "state": "published",
            "published": True,
        }
        self._entries.append(record)
        return record

    def append_rejected_disposition(self, *, run_id, revision, reason) -> dict:
        """Append an irreparable candidate's terminal rejected disposition (append-only)."""
        record = {
            "run_id": run_id,
            "revision": revision,
            "disposition": "rejected",
            "reason": reason,
            "published": False,
        }
        self._entries.append(record)
        return record

    # -- proof re-validation ----------------------------------------------
    @staticmethod
    def _validate_accepted_proof(journal_entries, accepted_proof) -> None:
        for token in promotion_mod.REQUIREMENTS["accepted"]:
            if not accepted_proof.get(token):
                raise LedgerError(f"acceptance proof missing/false {token!r}")
        if accepted_proof.get("cross_system_verification") is not True:
            raise LedgerError("acceptance proof: cross_system_verification must be True")
        pinned = next(e for e in journal_entries if e["state"] == "report_pinned")
        if accepted_proof["verified_hf_revision"] != pinned["proof"]["exact_hf_revision"]:
            raise LedgerError(
                "acceptance verified_hf_revision disagrees with the pinned report revision"
            )
        if accepted_proof["verified_report_commit"] != pinned["proof"]["source_report_commit"]:
            raise LedgerError(
                "acceptance verified_report_commit disagrees with the pinned report commit"
            )

    # -- eligibility (SOLE authority) -------------------------------------
    def records(self) -> list:
        return list(self._entries)

    def eligible_run_ids(self) -> set:
        """The published run_ids (reuses :func:`report.eligible_run_ids`)."""
        return report_mod.eligible_run_ids(self._entries)

    def is_eligible(self, run_id) -> bool:
        return run_id in self.eligible_run_ids()

    # -- serialization -----------------------------------------------------
    def to_jsonl(self) -> str:
        return "".join(json.dumps(e, sort_keys=True) + "\n" for e in self._entries)
