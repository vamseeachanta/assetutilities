# Decision Memo: ACMA Source Files — Sync vs. Copy

- Issue: [#31 — tech debt | ACMA | Source Files | Sync vs. Copy](https://github.com/vamseeachanta/assetutilities/issues/31)
- Status: decided (memo)
- Date: 2026-06-19
- Owners: @vamseeachanta (direction), @getsivakumar (architecture + gitignore boilerplate)
- Scope of this memo: choose a method for organizing ACMA (WLNG) project source files and ship the **reusable, folder-level `.gitignore` boilerplate** here in `assetutilities`. The ACMA-specific rollout is tracked in the ACMA project repo (`acma-projects`).

## Background

Issue #31 asks two things:

1. Pick the best way to bring/keep ACMA source files in sync between where work
   *runs* and where it is *tracked*.
2. Provide boilerplate for ignoring at the **folder level, not file level**.

The settled direction from the 2025-01 discussion (captured in the issue
comments) is: **use an explicit `.gitignore` with documented conventions and
the reasoning written down — no implicit naming conventions such as a leading
`.` or `_` to signal "don't track this".** This memo formalizes that.

### What "ACMA source files" are

ACMA is the `acma-projects` repository (engineering project management /
multi-disciplinary coordination), one of the tracked hub repos
(`hub-config.yaml` line 55: `name: "acma-projects"`; also listed in
`distribution_summary.md` and `DEPLOYMENT_SUMMARY.md`). It is a **separate
GitHub repo**, not a directory inside `assetutilities`. The "source files" are
the project's run inputs (config `.yml`, decks) plus large run *outputs*
(simulation/result artifacts like `.h5`, `.sim`, `.dat`) that should generally
**not** be committed.

`assetutilities` is the right home only for the *generic, reusable* piece: the
folder-level gitignore convention (and, optionally, a thin sync helper). The
M1/M2/M3 choice for ACMA itself is a project decision adopted in `acma-projects`.

## The Methods

### Method 1 — Run + sync in the same location (one tree, explicit folder-level `.gitignore`)

Work runs in place; the same directory tree is the git working tree. A
folder-level `.gitignore` allow-lists what is tracked and ignores everything
else (outputs, scratch, vendored binaries).

- **Maintenance:** lowest. One location, no copy step, nothing to keep in sync.
- **Drift risk:** none — there is only one copy, so the tracked state *is* the
  run state.
- **History:** clean and complete for tracked files; outputs never pollute history.
- **Tooling:** native git only. No batch/rsync/cron. Works the same on every machine.
- **Who owns truth:** the single working tree, governed by the committed `.gitignore`.
- **Cons:** runs happen inside the repo, so a careless `git add -A` or a missing
  ignore rule can commit large outputs. Requires discipline + a well-maintained
  `.gitignore` (mitigated by the boilerplate below and, optionally, a pre-commit
  size guard). Large output files sit next to source on disk.

### Method 2 — Separate locations + copy/sync batch (`run_location` → `sync_location`)

Work runs in `run_location` (untracked scratch); a batch/rsync step copies the
relevant files into `sync_location` (the git working tree) to be committed.

- **Maintenance:** higher. A copy script must be written, run, and kept correct;
  its include/exclude list duplicates the gitignore intent in a second place.
- **Drift risk:** **high** — two copies that diverge whenever someone forgets to
  run the sync, runs it partially, or edits the wrong copy. Classic source of
  "works on my run, not in the repo" bugs.
- **History:** can be clean, but commits reflect *the last sync*, not the actual
  run state, so provenance is weaker.
- **Tooling:** needs a maintained copy tool (rsync/robocopy/batch), and ideally
  scheduling, plus error handling for partial copies.
- **Who owns truth:** ambiguous — `run_location` has the real run, `sync_location`
  has what got committed. Two candidates for "truth" is the core weakness.
- **Pros:** keeps a heavy/noisy run area fully out of the repo by construction;
  the working tree only ever sees curated files. Useful when runs produce huge
  volumes or run on a machine that should not hold a clone.

### Method 3 — Alternatives ("another method")

The issue leaves M3 open. Two realistic alternatives, neither recommended here:

- **3a. Git submodule / subtree.** ACMA source pulled into `assetutilities` (or
  vice-versa) as a submodule/subtree. *Rejected:* this couples two repos at the
  git level, adds submodule pointer/detached-HEAD friction, and conflates a
  *client project* with a *shared utility library* — wrong ownership boundary.
  ACMA source belongs in `acma-projects`, not vendored into `assetutilities`.
- **3b. Symlink** from `run_location` into the tracked tree. *Rejected:* symlinks
  are fragile cross-platform (Windows behavior differs, git stores them as link
  files), they hide what is actually tracked, and they reintroduce an implicit
  convention — exactly what the issue says to avoid.

## Recommendation

**Adopt Method 1 (run + sync in the same location, governed by an explicit
folder-level `.gitignore`) for ACMA**, and ship the reusable folder-level
gitignore boilerplate from `assetutilities` (this memo + the snippet below).

Rationale, grounded in this repo and the issue's own constraints:

- **It is the issue's stated "Ideal" (M1)** and matches @getsivakumar's settled
  guidance: *explicit `.gitignore`, documented convention, no implicit `.`/`_`
  naming.* M1 needs exactly one artifact — a good `.gitignore` — and that
  artifact is the thing #31 asks us to make reusable.
- **Single source of truth.** M2's defining weakness is two diverging copies and
  an ambiguous owner of truth; M1 has none of that. Drift is the dominant
  long-run cost, and M1 removes it structurally rather than relying on a copy
  step being run correctly every time.
- **Lowest tooling burden, most portable.** M1 is native git, identical on Linux,
  macOS, and Windows. M2 needs rsync/robocopy + scheduling; M3a/M3b add
  submodule or symlink fragility. `assetutilities` is a cross-platform utility
  library, so the lowest-dependency, most-portable option is correct.
- **Right ownership boundary.** M3a would vendor a client project into a shared
  library — wrong. M1 keeps ACMA source in `acma-projects` and keeps
  `assetutilities`'s contribution to a generic, copyable convention.

M2 remains a documented fallback **only** for the narrow case where runs produce
output volumes too large to live beside the repo, or run on a machine that must
not hold a clone. In that case, keep `run_location` fully untracked and treat
the copy step as a deliberate publish, not a background sync.

## Boilerplate: folder-level `.gitignore`

Place a `.gitignore` **inside the folder** it governs (not only at repo root).
This keeps the convention local, explicit, and self-documenting — anyone opening
the folder sees the rule and its reason.

```gitignore
# ACMA / WLNG run folder — folder-level ignore policy (issue #31, Method 1)
#
# Convention: this folder is BOTH the run location and the tracked location.
# We TRACK curated source/config and IGNORE generated run outputs. The rules
# are explicit here (no implicit "." or "_" prefixes signal tracking state).
#
# Reason: a single tree = single source of truth, zero drift, native git only.

# 1) Ignore everything in this folder by default...
*

# 2) ...but always keep this .gitignore itself...
!.gitignore

# 3) ...and re-include the curated source we DO want tracked.
#    Add directories with a trailing slash, then their contents.
!*.yml
!*.yaml
!*.csv
!*.md
!inputs/
!inputs/**
!decks/
!decks/**

# 4) Belt-and-braces: never track heavy/derived run outputs even if a
#    broad allow-list above would otherwise catch them.
*.h5
*.sim
*.dat
*.log
*.tmp
results/
runs/
__pycache__/
```

Two usable shapes (pick per folder, document the choice in a header comment):

- **Allow-list (shown above):** ignore `*`, then re-include the few tracked
  globs/dirs. Best when a folder is mostly outputs with a small curated source set.
- **Deny-list (inverse):** track everything, then ignore the known-heavy
  extensions/dirs (`*.h5`, `*.sim`, `results/`, `runs/`). Best when a folder is
  mostly source with a few large outputs.

Notes for the allow-list shape:
- To re-include files **inside** an ignored directory you must un-ignore the
  directory first (`!inputs/`) and then its contents (`!inputs/**`); git will not
  descend into an ignored directory otherwise.
- Keep the rules and their **reason** in the header comment, per the issue's
  "explicitly put down the convention and the reason behind."

## Rollout / next steps

- `assetutilities`: this memo is the reusable deliverable. Optionally add a thin,
  `--dry-run`-default sync helper (`scripts/sync-folder.sh`, rsync wrapper) for
  the M2 fallback only; not required for the recommended M1 path.
- `acma-projects`: file a follow-up issue to adopt M1 — drop the folder-level
  `.gitignore` above into each run folder, remove any implicit `.`/`_` naming,
  and document the convention in that repo's README. (Tracked there, not here.)
- Close #31 once the boilerplate lands here and the ACMA-side adoption issue is
  open in `acma-projects`.
