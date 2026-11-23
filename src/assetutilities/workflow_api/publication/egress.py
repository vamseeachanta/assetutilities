# ABOUTME: Composed fail-closed egress gate (workspace-hub#3433): four gate points
# ABOUTME: (source / report draft / HF card+bytes / final pinned report + publication),
# ABOUTME: legal deny-list + env-token/secret scan (redacted) + absolute-path + per-input license.
"""The composed, fail-closed egress gate.

Every byte that leaves the trust boundary passes a gate. Four gate points mirror
the promotion lifecycle:

- **Gate A** -- source bytes at ``validated``;
- **Gate B** -- the rendered report DRAFT at ``draft_rendered``;
- **Gate C** -- the dataset card + EVERY upload byte at ``hf_candidate`` (before commit);
- **Gate D** -- the final pinned report + the Publication record before their
  source-repo commits.

The local subset (always enforced, fail-closed):

- a **legal deny-list** (injectable) of forbidden substrings;
- a **secret/token scan** -- token VALUES are read from an injected env mapping ONLY,
  plus a few token SHAPES; any hit is denied and the token is REDACTED from every
  emitted string (deny messages, findings) so a secret never reaches a log or record;
- an **absolute-path** check (``/``-rooted, ``~``, UNC, ``file:``, Windows drive); and
- a **per-input license** check reusing :func:`inputs.admission_reason`.

The ecosystem **#3013 validator is an injectable interface**. When absent, a bounded
shim enforces the covered subset FAIL-CLOSED and records
``{available: false, uncovered: ["public_identity_registry_id_check"]}`` so the missing
coverage is visible, never silently assumed clean.

Stdlib-only (``re`` plus :mod:`identity`/:mod:`inputs`).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from assetutilities.workflow_api import identity, inputs

REDACTION = "***REDACTED***"

# Checks the bounded shim CANNOT cover on its own (named so the gap is visible).
SHIM_UNCOVERED = ["public_identity_registry_id_check"]

# A few common secret/token SHAPES (value-independent) so an unlisted token still trips.
_TOKEN_SHAPES = (
    re.compile(r"hf_[A-Za-z0-9]{16,}"),
    re.compile(r"ghp_[A-Za-z0-9]{16,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
)

# Absolute / home / UNC / file: / Windows-drive path shapes (an absolute-path leak).
_ABS_PATH_SHAPES = (
    re.compile(r"(?<![\w.])file:/{0,3}\S+"),
    re.compile(r"(?<![\w./])~/[^\s'\"]+"),
    re.compile(r"(?<![\w.:])/(?:home|mnt|Users|root|etc|var|tmp|srv|opt)/[^\s'\"]*"),
    re.compile(r"[A-Za-z]:\\[^\s'\"]+"),
    re.compile(r"\\\\[^\s'\"]+"),  # UNC
)


class EgressDenied(Exception):
    """Raised (fail-closed) when a gate finds a policy violation. Findings are REDACTED."""

    def __init__(self, gate: str, findings):
        self.gate = gate
        self.findings = findings
        super().__init__(f"egress gate {gate!r} denied: {findings}")


@dataclass
class GateResult:
    """The outcome of a passed gate (recorded in the promotion journal)."""

    gate: str
    ok: bool = True
    available: bool = False
    uncovered: list = field(default_factory=list)
    findings: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# redaction + scanning
# ---------------------------------------------------------------------------

def _redact(text: str, secret_values) -> str:
    """Replace every known secret VALUE and token-shaped substring with the redaction."""
    if not text:
        return ""
    out = text
    for value in secret_values:
        if value:
            out = out.replace(value, REDACTION)
    for shape in _TOKEN_SHAPES:
        out = shape.sub(REDACTION, out)
    return out


class EgressGate:
    """A composed, fail-closed egress gate reused at all four gate points."""

    def __init__(self, *, legal_deny_list=(), env_tokens=None, external_validator=None):
        self.legal_deny_list = tuple(legal_deny_list or ())
        # token VALUES come from the injected env mapping ONLY (never read os.environ here).
        self.env_tokens = dict(env_tokens or {})
        self._secret_values = [v for v in self.env_tokens.values() if v]
        self.external_validator = external_validator

    # -- the core scan -----------------------------------------------------
    def _scan(self, gate: str, texts) -> GateResult:
        findings: list = []
        for raw in texts:
            if raw is None:
                continue
            text = raw if isinstance(raw, str) else raw.decode("utf-8", "replace")

            # secret token VALUES (from env) -- redacted in the finding
            for value in self._secret_values:
                if value and value in text:
                    findings.append({"type": "secret", "match": REDACTION, "source": "env_token"})
            # token SHAPES
            for shape in _TOKEN_SHAPES:
                if shape.search(text):
                    findings.append({"type": "secret", "match": REDACTION, "source": "token_shape"})
            # legal deny-list
            for term in self.legal_deny_list:
                if term and term in text:
                    findings.append({"type": "legal", "term": term})
            # absolute-path leak
            for shape in _ABS_PATH_SHAPES:
                m = shape.search(text)
                if m:
                    findings.append({"type": "absolute_path",
                                     "match": _redact(m.group(0), self._secret_values)})

        # external #3013 validator, or a bounded fail-closed shim
        if self.external_validator is not None and getattr(self.external_validator, "available", True):
            verdict = self.external_validator.validate(list(texts))
            available = True
            uncovered = list(verdict.get("uncovered", []))
            if not verdict.get("ok", False):
                findings.append({"type": "external_validator", "detail": REDACTION})
        else:
            available = False
            uncovered = list(SHIM_UNCOVERED)

        if findings:
            # never let a raw secret ride out inside the exception text
            safe = [_deep_redact(f, self._secret_values) for f in findings]
            raise EgressDenied(gate, safe)
        return GateResult(gate=gate, ok=True, available=available, uncovered=uncovered)

    # -- the four gate points ---------------------------------------------
    def gate_source_texts(self, texts) -> GateResult:
        """Gate A: raw source text/bytes about to be emitted."""
        return self._scan("A_source", texts)

    def gate_source(self, projection) -> GateResult:
        """Gate A over a :class:`RunProjection`: metadata text + per-input license."""
        # per-input license: reuse the inputs admission layer (fail-closed)
        for rec in projection.input_records:
            reason = inputs.admission_reason(rec)
            if reason is not None:
                raise EgressDenied("A_source", [{"type": "license", "reason": reason,
                                                 "role": rec.get("role")}])
        texts = [identity.canonicalize(projection.run_record())]
        for blob in projection.object_bytes.values():
            texts.append(blob)
        return self._scan("A_source", texts)

    def gate_report_draft(self, report_html) -> GateResult:
        """Gate B: the rendered (unpinned) report draft."""
        return self._scan("B_report_draft", [report_html])

    def gate_hf_upload(self, *, card, objects) -> GateResult:
        """Gate C: the dataset card + EVERY upload byte, BEFORE the HF commit."""
        texts = [card]
        for blob in objects.values():
            texts.append(blob)
        return self._scan("C_hf_upload", texts)

    def gate_final(self, *, pinned_report, publication_record) -> GateResult:
        """Gate D: the final pinned report + the Publication record before source commit."""
        texts = [pinned_report, identity.canonicalize(publication_record)]
        return self._scan("D_final", texts)


def _deep_redact(finding, secret_values):
    """Redact secret values from every string inside a finding dict."""
    out = {}
    for key, value in finding.items():
        out[key] = _redact(value, secret_values) if isinstance(value, str) else value
    return out
