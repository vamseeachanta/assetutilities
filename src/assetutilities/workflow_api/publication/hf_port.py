# ABOUTME: Injectable Hugging Face port (workspace-hub#3433): abstract HfPort +
# ABOUTME: InMemoryHfPort fake (immutable revisions, content-addressed objects) +
# ABOUTME: a REAL, env-token-backed huggingface_hub adapter (mock-tested; never faked green).
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
- **The real adapter is env-token-backed and re-verifiable, never faked green.**
  :class:`HuggingFaceHubHfPort` wraps ``huggingface_hub`` (imported LAZILY, per method):
  it reads its token only from the standard huggingface_hub sources (``HF_TOKEN`` env /
  cached ``~/.cache/huggingface/token``) -- never taken as an argument, never logged,
  never stored on the instance, never returned in a record; and it captures the EXACT
  commit oid the hub reports (no local minting). Its tests mock ``huggingface_hub`` so no
  byte ever crosses the network; a fake body that "passes" without a real upload is not
  possible because the promotion machine re-fetches + re-hashes every uploaded byte.

The :class:`InMemoryHfPort` fake remains the default test/dev port; the real adapter is
opt-in (construct it explicitly with a ``repo_id``).

.. note::

   LIVE verification against a real Hugging Face dataset (an actual ``create_commit`` +
   ``hf_hub_download`` round-trip over the network) is DEFERRED to a user-authorized
   pilot run, because it publishes externally. Nothing in this module or its test suite
   ever contacts huggingface.co: the adapter is proven only against a mocked
   ``huggingface_hub``. Do not wire it into an automated/CI publish path until that
   pilot has been run and signed off.

Stdlib for the fake (``hashlib`` plus :mod:`artifact` for content-addressed locators);
``huggingface_hub`` is a lazily-imported optional dependency used only by the real
adapter.
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
# real adapter -- env-token-backed huggingface_hub, mock-tested, never faked green
# ---------------------------------------------------------------------------

_IMPORT_HINT = (
    "huggingface_hub is not importable; install it (`pip install huggingface_hub`) to "
    "use the real HuggingFaceHubHfPort. Tests inject InMemoryHfPort instead."
)

# Exception class names that denote a transient, retryable network/server fault. Matched
# by name across the raised exception's MRO so we never have to import huggingface_hub /
# requests at module scope (keeps this module importable when the lib is absent).
_TRANSIENT_TYPE_NAMES = frozenset({
    "ConnectionError", "ConnectTimeout", "ConnectTimeoutError", "ReadTimeout",
    "ReadTimeoutError", "Timeout", "TimeoutError", "ChunkedEncodingError",
    "ProxyError", "SSLError", "RemoteDisconnected", "IncompleteRead",
    "ProtocolError", "NewConnectionError", "MaxRetryError",
})
# Class names that denote a missing object/repo (irreparable for this revision).
_NOT_FOUND_TYPE_NAMES = frozenset({
    "EntryNotFoundError", "RepositoryNotFoundError", "RevisionNotFoundError",
    "HFValidationError",
})
# Class names that denote auth/permission (a normal, non-transient HfError).
_AUTH_TYPE_NAMES = frozenset({
    "GatedRepoError", "HfHubHTTPError401", "HfHubHTTPError403",
})


def _status_code(exc):
    resp = getattr(exc, "response", None)
    code = getattr(resp, "status_code", None)
    if code is None:
        code = getattr(exc, "status_code", None)
    try:
        return int(code) if code is not None else None
    except (TypeError, ValueError):
        return None


def _classify(exc: BaseException) -> HfError:
    """Map a huggingface_hub / network exception onto the port's error taxonomy.

    network / 5xx / 429 / timeouts -> :class:`HfTransientError` (drives the machine's
    retry-R1 path); not-found -> :class:`HfUnavailableError`; auth/permission and anything
    else -> :class:`HfError`. Auth failures deliberately DON'T echo the original message
    (defence-in-depth: never surface anything token-adjacent).
    """
    if isinstance(exc, HfError):
        return exc
    names = {t.__name__ for t in type(exc).__mro__}
    code = _status_code(exc)
    if code is not None:
        if code == 429 or 500 <= code <= 599:
            return HfTransientError(f"transient Hugging Face fault (HTTP {code})")
        if code in (401, 403):
            return HfError(f"Hugging Face auth/permission denied (HTTP {code})")
        if code == 404:
            return HfUnavailableError(f"Hugging Face object not found (HTTP {code})")
        return HfError(f"Hugging Face request failed (HTTP {code})")
    if names & _TRANSIENT_TYPE_NAMES or isinstance(exc, (ConnectionError, TimeoutError, OSError)):
        return HfTransientError(f"transient Hugging Face network fault: {type(exc).__name__}")
    if names & _AUTH_TYPE_NAMES:
        return HfError("Hugging Face auth/permission denied")
    if names & _NOT_FOUND_TYPE_NAMES:
        return HfUnavailableError(f"Hugging Face resource not found: {type(exc).__name__}")
    return HfError(f"Hugging Face error: {type(exc).__name__}")


class HuggingFaceHubHfPort(HfPort):
    """Real ``huggingface_hub`` dataset adapter (env-token-backed, mock-tested).

    Construct with the target dataset ``repo_id`` (e.g. ``"aceengineer/wed-runs"``); the
    token is NEVER passed here -- it is resolved by ``huggingface_hub`` itself from
    ``HF_TOKEN`` / the cached login, so it is never held on this object, logged, or
    returned.

    - :meth:`create_commit` ensures the dataset repo exists (``create_repo`` with
      ``exist_ok=True``, ``repo_type="dataset"``, ``private=...``) then issues ONE
      ``HfApi.create_commit`` of ``CommitOperationAdd`` operations -- one per
      content-addressed object at its :func:`artifact.storage_locator_for` path plus the
      dataset card at :data:`CARD_PATH`. It returns the EXACT commit oid the hub reports
      (captured verbatim), and never force-pushes/deletes/overwrites.
    - :meth:`fetch_object` / :meth:`fetch_card` map to ``hf_hub_download`` pinned to the
      EXACT ``revision`` (a moving ref is passed through verbatim, never silently
      re-resolved) and return the downloaded bytes for the machine's post-upload re-hash.

    ``huggingface_hub`` is imported lazily inside each method, so this module still imports
    when the library is absent; an import failure raises :class:`HfUnavailableError`.
    """

    def __init__(self, *, repo_id: str, private: bool = True):
        if not repo_id or not isinstance(repo_id, str):
            raise HfError("HuggingFaceHubHfPort requires a non-empty dataset repo_id")
        self._repo_id = repo_id
        self._private = bool(private)

    def __repr__(self) -> str:
        # No token is ever held on this object, so none can leak here.
        return f"HuggingFaceHubHfPort(repo_id={self._repo_id!r}, private={self._private})"

    # -- lazy import -------------------------------------------------------
    @staticmethod
    def _import():
        try:
            import huggingface_hub  # noqa: F401  (imported for its symbols below)
            from huggingface_hub import HfApi, CommitOperationAdd, hf_hub_download
        except ImportError as exc:
            raise HfUnavailableError(_IMPORT_HINT) from exc
        return HfApi, CommitOperationAdd, hf_hub_download

    def _api(self):
        HfApi, _, _ = self._import()
        # No token argument: huggingface_hub resolves it from HF_TOKEN / the cached login.
        return HfApi()

    # -- commit ------------------------------------------------------------
    def create_commit(self, *, objects: Mapping[str, bytes], card: bytes, message: str = "") -> str:
        _, CommitOperationAdd, _ = self._import()
        api = self._api()
        operations = [
            CommitOperationAdd(
                path_in_repo=artifact.storage_locator_for(digest),
                path_or_fileobj=bytes(blob),
            )
            for digest, blob in objects.items()
        ]
        operations.append(
            CommitOperationAdd(path_in_repo=CARD_PATH, path_or_fileobj=bytes(card))
        )
        try:
            api.create_repo(
                repo_id=self._repo_id,
                repo_type="dataset",
                exist_ok=True,
                private=self._private,
            )
            info = api.create_commit(
                repo_id=self._repo_id,
                repo_type="dataset",
                operations=operations,
                commit_message=message or f"publish projection ({len(objects)} objects)",
            )
        except Exception as exc:  # noqa: BLE001 -- re-raised via the port taxonomy
            raise _classify(exc) from exc
        # Capture the exact oid the hub reports -- never a locally minted value.
        oid = getattr(info, "oid", None)
        if not oid:
            raise HfError("Hugging Face create_commit returned no commit oid")
        return str(oid)

    # -- fetch -------------------------------------------------------------
    def _download(self, revision: str, path: str) -> bytes:
        _, _, hf_hub_download = self._import()
        try:
            local_path = hf_hub_download(
                repo_id=self._repo_id,
                filename=path,
                revision=revision,  # pinned EXACTLY -- no silent moving-ref resolution
                repo_type="dataset",
            )
        except Exception as exc:  # noqa: BLE001
            raise _classify(exc) from exc
        with open(local_path, "rb") as handle:
            return handle.read()

    def fetch_object(self, revision: str, digest: str) -> bytes:
        return self._download(revision, artifact.storage_locator_for(digest))

    def fetch_card(self, revision: str) -> bytes:
        return self._download(revision, CARD_PATH)

    # -- listings ----------------------------------------------------------
    def list_objects(self, revision: str):
        api = self._api()
        try:
            files = api.list_repo_files(
                repo_id=self._repo_id, revision=revision, repo_type="dataset"
            )
        except Exception as exc:  # noqa: BLE001
            raise _classify(exc) from exc
        return tuple(f.rsplit("/", 1)[-1] for f in files if f.startswith("objects/"))

    def list_revisions(self):
        api = self._api()
        try:
            commits = api.list_repo_commits(repo_id=self._repo_id, repo_type="dataset")
        except Exception as exc:  # noqa: BLE001
            raise _classify(exc) from exc
        return tuple(getattr(c, "commit_id", str(c)) for c in commits)
