# ABOUTME: Injectable Hugging Face port (workspace-hub#3433): abstract HfPort +
# ABOUTME: InMemoryHfPort fake (immutable revisions, content-addressed objects) +
# ABOUTME: a documented real huggingface_hub adapter shim that is NEVER faked.
"""The Hugging Face egress port for publication.

The publisher NEVER imports ``huggingface_hub`` directly. It talks to an abstract
:class:`HfPort` so tests can inject an in-memory fake and the real network adapter
is a single, clearly-marked thin shim.

Design invariants (from the approved+remediated #3433 plan):

- **Immutable revisions, content-addressed objects.** Every :meth:`HfPort.create_commit`
  yields a NEW, immutable revision (an exact 40-hex git/HF commit sha). Objects inside a
  revision are addressed by their content ``digest`` and stored at
  :func:`artifact.storage_locator_for` paths, so a re-fetch by ``(revision, digest)``
  returns exactly the committed bytes. Two commits of identical content still yield
  DISTINCT revisions (git semantics), so a corrective re-publish is a new revision R2,
  never an overwrite of R1.
- **Post-upload verification re-fetches + re-hashes EVERY uploaded byte** (objects,
  shards, and the dataset card) through :func:`artifact.verify_integrity` semantics --
  this port only stores/returns bytes; the promotion machine owns the re-hash.
- **The real adapter is a documented shim, never faked.** :class:`HuggingFaceHubHfPort`
  raises ``NotImplementedError`` with a wiring note; it is never given a fake body that
  could masquerade as a real upload.

Stdlib-only (``hashlib`` plus :mod:`artifact` for content-addressed locators).
"""

from __future__ import annotations

import hashlib
from typing import Mapping

from assetutilities.workflow_api import artifact


# A dataset-card path is reserved (the card is not a content-addressed object).
CARD_PATH = "README.md"


class HfError(Exception):
    """Base class for Hugging Face port faults."""


class HfTransientError(HfError):
    """A transient, retryable fault (network blip / rate limit) -- retry the SAME revision."""


class HfUnavailableError(HfError):
    """A permanently-unavailable object -- irreparable for this revision."""


class HfPort:
    """Abstract Hugging Face dataset port (create commit / fetch object / list)."""

    def create_commit(self, *, objects: Mapping[str, bytes], card: bytes, message: str = "") -> str:
        raise NotImplementedError

    def fetch_object(self, revision: str, digest: str) -> bytes:
        raise NotImplementedError

    def fetch_card(self, revision: str) -> bytes:
        raise NotImplementedError

    def list_objects(self, revision: str):
        raise NotImplementedError

    def list_revisions(self):
        raise NotImplementedError


# ---------------------------------------------------------------------------
# in-memory fake (tests only)
# ---------------------------------------------------------------------------

class InMemoryHfPort(HfPort):
    """An in-memory :class:`HfPort` fake with immutable, content-addressed revisions.

    Faithful to the real contract:

    - each :meth:`create_commit` mints a NEW exact 40-hex revision (a per-commit nonce
      is mixed in, so identical content still yields a distinct revision -- git semantics);
    - objects are stored at :func:`artifact.storage_locator_for` paths and fetched by
      content ``digest``; and
    - revisions are immutable once committed.

    Test fault injection (never present in the real adapter):

    - :meth:`inject_transient_fetch_failures` -- the next N fetches raise
      :class:`HfTransientError` (a retryable blip);
    - :meth:`corrupt_stored_object` / :meth:`make_object_unavailable` -- simulate an
      irreparable post-commit storage fault; and
    - ``corrupt_objects`` / ``corrupt_card`` -- arm a corruption applied to the NEXT
      created revision (so the promotion re-hash catches it before advancing).
    - ``force_revision`` -- force a fixed (possibly MOVING) ref, to prove a finalized
      report rejects a non-exact revision.
    """

    def __init__(self, *, force_revision: str | None = None):
        self._revisions: dict[str, dict] = {}
        self._order: list[str] = []
        self.commit_count = 0
        self._force_revision = force_revision
        # fault-injection state
        self._transient_remaining = 0
        self._corrupted: dict[tuple[str, str], bytes] = {}
        self._unavailable: set[tuple[str, str]] = set()
        # armed-for-next-commit corruption
        self.corrupt_objects: set[str] = set()
        self.corrupt_card: bool = False

    # -- commit ------------------------------------------------------------
    def create_commit(self, *, objects: Mapping[str, bytes], card: bytes, message: str = "") -> str:
        for digest, blob in objects.items():
            actual = hashlib.sha256(bytes(blob)).hexdigest()
            if actual != digest:
                raise HfError(
                    f"refusing to commit object whose bytes hash to {actual} but are "
                    f"addressed as {digest!r} (content-addressing violated)"
                )
        self.commit_count += 1
        revision = self._mint_revision(objects, card)
        stored_objects = {d: bytes(b) for d, b in objects.items()}
        self._revisions[revision] = {
            "objects": stored_objects,
            "card": bytes(card),
            "paths": self._paths(objects),
        }
        self._order.append(revision)
        # apply any armed corruption to THIS revision (simulates a storage fault)
        for digest in self.corrupt_objects:
            if digest in stored_objects:
                self._corrupted[(revision, digest)] = b"CORRUPTED::" + stored_objects[digest]
        if self.corrupt_card:
            self._corrupted[(revision, CARD_PATH)] = b"CORRUPTED::" + bytes(card)
        self.corrupt_objects = set()
        self.corrupt_card = False
        return revision

    def _mint_revision(self, objects, card) -> str:
        if self._force_revision is not None:
            return self._force_revision
        manifest = "\n".join(sorted(objects)) + "\n" + hashlib.sha256(bytes(card)).hexdigest()
        # a per-commit nonce guarantees a distinct revision even for identical content
        nonce = f"{self.commit_count}:{len(self._order)}"
        payload = (manifest + "\n" + nonce).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()[:40]

    @staticmethod
    def _paths(objects) -> dict:
        return {digest: artifact.storage_locator_for(digest) for digest in objects}

    # -- fetch -------------------------------------------------------------
    def _tick_transient(self):
        if self._transient_remaining > 0:
            self._transient_remaining -= 1
            raise HfTransientError("transient fetch failure (retryable)")

    def fetch_object(self, revision: str, digest: str) -> bytes:
        self._tick_transient()
        if (revision, digest) in self._unavailable:
            raise HfUnavailableError(f"object {digest!r} permanently unavailable at {revision!r}")
        rev = self._revisions.get(revision)
        if rev is None:
            raise HfError(f"unknown revision {revision!r}")
        if (revision, digest) in self._corrupted:
            return self._corrupted[(revision, digest)]
        if digest not in rev["objects"]:
            raise HfError(f"no object {digest!r} in revision {revision!r}")
        return rev["objects"][digest]

    def fetch_card(self, revision: str) -> bytes:
        self._tick_transient()
        rev = self._revisions.get(revision)
        if rev is None:
            raise HfError(f"unknown revision {revision!r}")
        if (revision, CARD_PATH) in self._corrupted:
            return self._corrupted[(revision, CARD_PATH)]
        return rev["card"]

    # -- listings ----------------------------------------------------------
    def list_objects(self, revision: str):
        rev = self._revisions.get(revision)
        if rev is None:
            raise HfError(f"unknown revision {revision!r}")
        return tuple(rev["objects"])

    def list_revisions(self):
        return tuple(self._order)

    def list_paths(self, revision: str):
        rev = self._revisions.get(revision)
        if rev is None:
            raise HfError(f"unknown revision {revision!r}")
        return (CARD_PATH,) + tuple(rev["paths"].values())

    # -- fault injection (tests only) --------------------------------------
    def inject_transient_fetch_failures(self, n: int) -> None:
        self._transient_remaining = int(n)

    def corrupt_stored_object(self, revision: str, digest: str, replacement: bytes | None = None) -> None:
        rev = self._revisions.get(revision)
        base = rev["objects"].get(digest, b"") if rev else b""
        self._corrupted[(revision, digest)] = replacement if replacement is not None else b"IRREPARABLE::" + base

    def make_object_unavailable(self, revision: str, digest: str) -> None:
        self._unavailable.add((revision, digest))


# ---------------------------------------------------------------------------
# real adapter -- a documented shim, NEVER faked
# ---------------------------------------------------------------------------

class HuggingFaceHubHfPort(HfPort):
    """Real ``huggingface_hub`` adapter -- a documented thin shim, deliberately NOT faked.

    Wiring (left unimplemented on purpose): :meth:`create_commit` maps to
    ``huggingface_hub.HfApi.create_commit`` with ``CommitOperationAdd`` for each
    content-addressed object + the dataset card, returning the resulting commit sha;
    :meth:`fetch_object` / :meth:`fetch_card` map to ``hf_hub_download`` pinned to an
    exact ``revision``. Giving this a fake body would let a "real upload" silently pass
    without touching the network, so it fails closed with :class:`NotImplementedError`.
    """

    _SHIM = (
        "HuggingFaceHubHfPort is an unimplemented shim: wire it to "
        "huggingface_hub.HfApi.create_commit / hf_hub_download. It is intentionally "
        "not faked -- inject InMemoryHfPort in tests."
    )

    def create_commit(self, *, objects=None, card=None, message: str = "") -> str:
        raise NotImplementedError(self._SHIM)

    def fetch_object(self, revision: str, digest: str) -> bytes:
        raise NotImplementedError(self._SHIM)

    def fetch_card(self, revision: str) -> bytes:
        raise NotImplementedError(self._SHIM)

    def list_objects(self, revision: str):
        raise NotImplementedError(self._SHIM)

    def list_revisions(self):
        raise NotImplementedError(self._SHIM)
