# ABOUTME: Rolling per-algorithm report renderer (workspace-hub#3431): mandatory
# ABOUTME: Inputs/Outputs, failed-run separation, exact-HF-revision pinning, ledger eligibility.
"""Rolling algorithm report (one per algorithm).

Renders a single HTML report per algorithm summarizing its latest + historical
runs. Implements the #3431 report contract:

- **Mandatory Inputs + Outputs sections**, plus ONLY the optional sections a run
  actually declares (no empty optional scaffolding).
- **Failed runs are clearly separated** from succeeded runs.
- **Every displayed run links to an EXACT Hugging Face revision.** A finalized
  (``pinned``) report REJECTS a moving ref (``main``, ``HEAD``, a branch/tag, a
  short sha); a ``main``/moving ref fails. A draft (unpinned) report tolerates a
  not-yet-pinned revision and is banner-marked ``DRAFT``. This matches the #3433
  Gate B/D lifecycle: drafted UNPINNED, finalized PINNED to an exact revision.
- **Eligibility comes from a SOURCE-REPO ledger** (``publications.jsonl``), NOT
  Hugging Face visibility. A run is displayed iff it is published in the ledger; a
  run's HF ``visible`` flag is deliberately ignored.
- **Output is HTML-safe**: every interpolated value is escaped, so injected markup
  (e.g. ``<script>``) can never survive into the rendered page.

Stdlib-only (``html``, ``re``) plus :mod:`output_contract` for its error type.
"""

from __future__ import annotations

import html
import re

from assetutilities.workflow_api.output_contract import OutputContractError

# A run's terminal statuses this report distinguishes.
_SUCCEEDED = "succeeded"
_REPRODUCIBLE_FAILURE = "reproducible_failure"

# Mandatory sections always rendered for every displayed run.
MANDATORY_SECTIONS = ("inputs", "outputs")

# An EXACT git/HF revision: a full 40-char lowercase hex commit sha. A moving ref
# (branch/tag/HEAD/short sha) is NOT exact and fails a finalized report.
_EXACT_REVISION_RE = re.compile(r"^[0-9a-f]{40}$")


def is_exact_revision(revision) -> bool:
    """True iff ``revision`` is an exact (full 40-hex) commit sha.

    A moving ref -- ``main``, ``HEAD``, ``refs/heads/*``, a tag like ``v1.0.0``, or a
    truncated sha -- is NOT exact and returns ``False``.
    """
    return isinstance(revision, str) and bool(_EXACT_REVISION_RE.match(revision))


def eligible_run_ids(ledger) -> set:
    """Return the set of published run_ids from a source-repo ``publications.jsonl``.

    ``ledger`` is a list of entries (dicts). An entry makes its run eligible when it
    is published (``published`` truthy, or ``state == "published"``). This is the
    SOLE source of display eligibility -- Hugging Face visibility is never consulted.
    """
    published = set()
    for entry in ledger or ():
        if not isinstance(entry, dict):
            raise OutputContractError("each ledger entry must be a dict")
        run_id = entry.get("run_id")
        if not run_id:
            continue
        if entry.get("published") or entry.get("state") == "published":
            published.add(run_id)
    return published


def _esc(value) -> str:
    """HTML-escape any interpolated value (never trust caller-supplied text)."""
    return html.escape("" if value is None else str(value), quote=True)


def _render_kv_section(title, items) -> str:
    rows = []
    for item in items or ():
        name = _esc(item.get("name") if isinstance(item, dict) else item)
        value = _esc(item.get("value") if isinstance(item, dict) else "")
        rows.append(f"<li><span class='k'>{name}</span>: <span class='v'>{value}</span></li>")
    body = "\n".join(rows) if rows else "<li class='empty'>(none)</li>"
    return f"<section class='{_esc(title.lower())}'><h4>{_esc(title)}</h4><ul>{body}</ul></section>"


def _render_optional_sections(optional) -> str:
    """Render ONLY the optional sections a run actually declares (non-empty)."""
    if not optional:
        return ""
    parts = []
    for name, content in optional.items():
        if content in (None, "", [], {}):
            continue  # only-applicable: skip empty optional sections
        parts.append(
            f"<section class='optional optional-{_esc(name)}'>"
            f"<h4>{_esc(name)}</h4><div class='v'>{_esc(content)}</div></section>"
        )
    return "\n".join(parts)


def _render_run(run, *, pinned, latest) -> str:
    run_id = _esc(run.get("run_id"))
    status = run.get("status")
    revision = run.get("hf_revision")

    if pinned and not is_exact_revision(revision):
        raise OutputContractError(
            f"finalized (pinned) report requires an EXACT HF revision for run "
            f"{run.get('run_id')!r}; a moving ref {revision!r} fails"
        )

    is_failed = status == _REPRODUCIBLE_FAILURE
    css = "run failed-run" if is_failed else "run succeeded-run"
    if latest:
        css += " latest"
    status_label = _esc(status)
    rev_label = _esc(revision) if revision else "(unpinned)"
    rev_html = (
        f"<a class='hf-revision' href='hf://revision/{rev_label}'>{rev_label}</a>"
        if revision else "<span class='hf-revision unpinned'>(unpinned)</span>"
    )

    inputs = _render_kv_section("Inputs", run.get("inputs"))
    outputs = _render_kv_section("Outputs", run.get("outputs"))
    optional = _render_optional_sections(run.get("optional"))
    return (
        f"<article class='{css}' data-run-id='{run_id}'>"
        f"<header><h3>Run {run_id}</h3>"
        f"<span class='status'>{status_label}</span> "
        f"<span class='revision'>{rev_html}</span></header>"
        f"{inputs}{outputs}{optional}</article>"
    )


def render_report(*, algorithm, runs, ledger, pinned=False, title=None) -> str:
    """Render the rolling HTML report for one algorithm.

    ``runs`` is ordered latest-first. Only runs published in the source-repo
    ``ledger`` are displayed (HF visibility ignored). Failed runs are separated into
    their own section. When ``pinned`` (finalized), every displayed run MUST link to
    an EXACT HF revision or :class:`OutputContractError` is raised; otherwise the
    report is banner-marked ``DRAFT (unpinned)``.
    """
    eligible = eligible_run_ids(ledger)
    displayed = [r for r in (runs or ()) if r.get("run_id") in eligible]

    succeeded, failed = [], []
    first = True
    for run in displayed:
        rendered = _render_run(run, pinned=pinned, latest=first)
        first = False
        if run.get("status") == _REPRODUCIBLE_FAILURE:
            failed.append(rendered)
        else:
            succeeded.append(rendered)

    banner = "FINAL (pinned)" if pinned else "DRAFT (unpinned)"
    heading = _esc(title or f"Rolling report: {algorithm}")

    succeeded_html = (
        "<section class='successful-runs'><h2>Successful runs (latest first)</h2>"
        + ("\n".join(succeeded) if succeeded else "<p class='empty'>(no successful runs)</p>")
        + "</section>"
    )
    failed_html = (
        "<section class='failed-runs'><h2>Failed runs (separated)</h2>"
        + ("\n".join(failed) if failed else "<p class='empty'>(no failed runs)</p>")
        + "</section>"
    )

    return (
        f"<main class='algorithm-report' data-algorithm='{_esc(algorithm)}'>"
        f"<header><h1>{heading}</h1>"
        f"<div class='lifecycle-banner'>{_esc(banner)}</div></header>"
        f"{succeeded_html}{failed_html}</main>"
    )
