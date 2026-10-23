"""Read-only branch report; no fetch, checkout, merge, push or deletion.

Policy source: issue 19 and docs/plans/2026-05-05-issue-19-monthly-branch-and-multiuser-merge.md.
Git command semantics follow the existing scripts/au_git_sync branch inspector.
Monthly retention is optional policy, not a test of commit reachability.
"""

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path


class GitError(RuntimeError):
    """A Git failure with only operation and exit code, without raw stderr."""

    def __init__(self, operation, returncode):
        self.returncode = returncode
        super().__init__(f"Git {operation} failed (exit {returncode})")


def git(repo, *args):
    """Run a captured read command without caller repository bindings."""
    environment = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    result = subprocess.run(
        ["git", *args], cwd=repo, env=environment, shell=False, check=False,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if result.returncode:
        raise GitError(args[0], result.returncode)
    # Git can report an ambiguous ref on stderr while returning success.
    if args[0] == "rev-parse" and "--symbolic-full-name" in args and result.stderr:
        raise ValueError("base reference must resolve without ambiguity")
    return result.stdout.rstrip("\r\n")


def retention_months(month):
    """Current and previous calendar months, per the issue plan's policy."""
    if not re.fullmatch(r"[0-9]{6}", month):
        raise ValueError("month must use YYYYMM")
    current = dt.date(int(month[:4]), int(month[4:]), 1)
    previous = current - dt.timedelta(days=1)
    return {month, f"{previous.year:04d}{previous.month:02d}"}


def branch_name(ref, remotes=()):
    """Remove the namespace and optional remote, preserving nested branch names."""
    if ref.startswith("refs/remotes/"):
        short = ref.removeprefix("refs/remotes/")
        for remote in sorted(remotes, key=len, reverse=True):
            prefix = f"{remote}/"
            if short.startswith(prefix):
                return short.removeprefix(prefix)
        # Preserve cached refs without a configured remote and legacy layouts.
        return short.split("/", 1)[1] if "/" in short else short
    return ref.removeprefix("refs/heads/")


def classify(refs, merged, current, base, month=None, remotes=()):
    """Classify reachability independently of the optional monthly convention."""
    retained = retention_months(month) if month is not None else set()
    merged = set(merged)
    base_branch = branch_name(base, remotes) if base.startswith(("refs/heads/", "refs/remotes/")) else None
    rows = []
    for ref in refs:
        remote = ref.startswith("refs/remotes/")
        branch = branch_name(ref, remotes)
        if branch in {"main", "master", base_branch} or ref == base:
            status = "protected"
        elif not remote and ref == current:
            status = "current"
        else:
            status = "merged_review" if ref in merged else "unmerged"
        row = {"ref": ref, "status": status}
        if month is not None:
            row["monthly"] = (
                "retained" if branch in retained else
                "outside_window" if re.fullmatch(r"[0-9]{4}(0[1-9]|1[0-2])", branch)
                else "not_monthly"
            )
        rows.append(row)
    return rows


def inspect(repo, base, month=None):
    """Inspect local state against a pinned base commit; never contact a remote."""
    if not base or base.startswith("-"):
        raise ValueError("base must be a commit reference")
    if month is not None:
        retention_months(month)
    base_commit = git(repo, "rev-parse", "--verify", "--end-of-options", f"{base}^{{commit}}")
    # Commit expressions have no symbolic ref and do not protect other branches.
    base_ref = git(repo, "rev-parse", "--symbolic-full-name", "--verify",
                   "--end-of-options", base)
    remotes = git(repo, "remote").splitlines()
    try:
        current = git(repo, "symbolic-ref", "--quiet", "HEAD")
    except GitError as error:
        # git symbolic-ref --quiet uses exit 1 when HEAD is detached.
        if error.returncode != 1:
            raise
        current = None
    listing = git(repo, "for-each-ref", "--format=%(refname)%09%(symref)",
                  "refs/heads/", "refs/remotes/")
    refs = []
    for line in listing.splitlines():
        ref, symbolic = line.split("\t", 1)
        if not symbolic:
            refs.append(ref)
    merged = git(repo, "for-each-ref", "--merged", base_commit,
                 "--format=%(refname)", "refs/heads/", "refs/remotes/").splitlines()
    return {
        "base": base, "base_commit": base_commit,
        "current": current.removeprefix("refs/heads/") if current else None,
        "remote_state": "local_cache_only",
        "branches": classify(refs, merged, current, base_ref, month, remotes),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--base", required=True, help="explicit integration base")
    parser.add_argument("--month", help="optional YYYYMM convention report")
    parser.add_argument("--fail-on-findings", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = inspect(args.repo, args.base, args.month)
        output = json.dumps(report, indent=2, sort_keys=True)
        findings = any(row["status"] == "merged_review" for row in report["branches"])
        print(output)
        return int(args.fail_on_findings and findings)
    except Exception:
        # Unexpected inspection errors use the same redacted exit contract.
        print("Branch report failed; verify repository, base, month and Git availability.",
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
