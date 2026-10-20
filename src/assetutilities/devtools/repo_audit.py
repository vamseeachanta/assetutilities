"""Offline, read-only consolidation review from an explicit inventory snapshot.

Field sources (online editions read in 2026):
https://docs.github.com/en/rest/repos/repos#get-a-repository
https://docs.github.com/en/rest/issues/issues#list-repository-issues
https://docs.github.com/en/rest/branches/branches#list-branches
https://docs.github.com/en/rest/pulls/pulls#list-pull-requests
https://docs.github.com/en/rest/commits/commits#get-a-commit
https://git-scm.com/docs/git-branch (the --merged reachability definition).

The review rules are application policy, documented in
docs/modules/repo_management/consolidation-audit.md. No retention duration or
engineering coefficient is assumed: the cutoff and destinations are inputs.
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence


def _timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a timezone-aware ISO timestamp")
    try:
        parsed = datetime.fromisoformat(
            value.removesuffix("Z") + "+00:00" if value.endswith("Z") else value
        )
    except ValueError:
        raise ValueError(f"{field} must be a timezone-aware ISO timestamp") from None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _name(value: Any) -> str:
    if not isinstance(value, str) or not value.strip() or not value.isprintable():
        raise ValueError("names must be nonempty printable strings")
    if value != value.strip():
        raise ValueError("names must not have surrounding whitespace")
    return value


def _named_rows(value: Any, field: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    names = set()
    for item in value:
        if not isinstance(item, dict):
            raise ValueError(f"{field} entries must be objects")
        name = _name(item.get("name"))
        if name in names:
            raise ValueError(f"duplicate name in {field}")
        names.add(name)
    return value


def _validate_fields(
    record: dict[str, Any], observed: datetime, *, branch: bool
) -> None:
    flags = ("protected", "merged") if branch else ("archived", "branches_complete")
    counts = (
        ("open_pull_requests",) if branch else ("open_issues", "open_pull_requests")
    )
    for field in flags:
        value = record.get(field)
        if value is not None and not isinstance(value, bool):
            raise ValueError(f"{field} must be a boolean or null")
    for field in counts:
        value = record.get(field)
        # Counts are cardinalities: zero means the empty set, not a fitted limit.
        if value is not None and (
            not isinstance(value, int) or isinstance(value, bool) or value < 0
        ):
            raise ValueError(f"{field} must be a nonnegative integer or null")
    field = "committed_at" if branch else "pushed_at"
    if record.get(field) is not None:
        if _timestamp(record[field], field) > observed:
            raise ValueError(f"{field} cannot be after observed_at")


def _check(status: str, reason: str) -> dict[str, str]:
    return {"status": status, "reason": reason}


def _consolidation(
    repo: dict[str, Any], cutoff: datetime, keep: set[str]
) -> dict[str, str]:
    if repo["name"] in keep:
        return _check("KEEP", "Explicitly retained by policy.")
    if repo.get("archived") is True:
        return _check("ARCHIVED", "Already archived; no consolidation action proposed.")
    required = ("archived", "pushed_at", "open_issues", "open_pull_requests")
    missing = [field for field in required if repo.get(field) is None]
    if missing:
        return _check("NOT_EVALUATED", "Missing evidence: " + ", ".join(missing))
    if repo["open_issues"] or repo["open_pull_requests"]:
        return _check("KEEP", "Open issues or pull requests require attention.")
    if _timestamp(repo["pushed_at"], "pushed_at") >= cutoff:
        return _check("KEEP", "Push timestamp is on or after the supplied cutoff.")
    return _check(
        "REVIEW_CONSOLIDATION", "Push predates cutoff; no open issues or pull requests."
    )


def _issue_routing(repo: dict[str, Any], destinations: set[str]) -> dict[str, str]:
    if repo["name"] in destinations:
        return _check("OK", "Permitted issue destination.")
    count = repo.get("open_issues")
    if count is None:
        return _check("NOT_EVALUATED", "Missing evidence: open_issues")
    # Issue #35 asks to concentrate issues even when the current backlog is empty.
    return _check(
        "REVIEW_ROUTING",
        f"Outside permitted destinations; {count} open issues. Review intake and transfers.",
    )


def _branch_check(
    branch: dict[str, Any], repo: dict[str, Any], cutoff: datetime
) -> dict[str, str]:
    if repo.get("archived") is True:
        return _check("KEEP", "Repository is archived.")
    default = repo.get("default_branch")
    if default is None:
        return _check("NOT_EVALUATED", "Missing evidence: default_branch")
    if branch["name"] == default:
        return _check("KEEP", "Default branch.")
    if branch.get("protected") is True:
        return _check("KEEP", "Protected branch.")
    if branch.get("merged") is False:
        return _check("KEEP", "Not fully merged into the default branch.")
    if branch.get("open_pull_requests"):
        return _check("KEEP", "Branch has open pull requests.")
    if branch.get("committed_at") is not None:
        if _timestamp(branch["committed_at"], "committed_at") >= cutoff:
            return _check(
                "KEEP", "Commit timestamp is on or after the supplied cutoff."
            )
    required = ("protected", "merged", "committed_at", "open_pull_requests")
    missing = [field for field in required if branch.get(field) is None]
    if repo.get("archived") is None:
        missing.append("archived")
    if missing:
        return _check("NOT_EVALUATED", "Missing evidence: " + ", ".join(missing))
    return _check(
        "REVIEW_DELETE",
        "Merged, unprotected, before cutoff, with no open pull requests.",
    )


def _branches(repo: dict[str, Any], cutoff: datetime) -> dict[str, Any]:
    complete = (
        repo.get("branches_complete") is True and repo.get("branches") is not None
    )
    result: dict[str, Any] = _check(
        "EVALUATED" if complete else "NOT_EVALUATED",
        "Complete listing supplied."
        if complete
        else "Complete branch listing not supplied.",
    )
    result["items"] = [
        {"name": branch["name"], **_branch_check(branch, repo, cutoff)}
        for branch in sorted(repo.get("branches") or [], key=lambda item: item["name"])
    ]
    return result


def _policy_names(values: Iterable[str], known: set[str], field: str) -> set[str]:
    if not isinstance(values, Iterable) or isinstance(values, (str, bytes)):
        raise ValueError(f"{field} must be a collection of names")
    names = [_name(value) for value in values]
    if len(names) != len(set(names)) or not set(names) <= known:
        raise ValueError(f"{field} contains duplicate or unknown names")
    return set(names)


def audit_inventory(
    inventory: dict[str, Any],
    *,
    stale_before: str,
    issue_repositories: Iterable[str],
    keep_repositories: Iterable[str] = (),
) -> dict[str, Any]:
    """Evaluate a normalized snapshot without accessing Git, the network or disk.

    Missing optional evidence yields NOT_EVALUATED. Malformed supplied evidence
    raises ValueError. Review statuses request human decisions and authorize no
    action. See the usage document for collection requirements and schema.
    """
    if not isinstance(inventory, dict):
        raise ValueError("inventory must be an object")
    observed = _timestamp(inventory.get("observed_at"), "observed_at")
    cutoff = _timestamp(stale_before, "stale_before")
    if cutoff >= observed:
        raise ValueError("stale_before must precede observed_at")
    repos = _named_rows(inventory.get("repositories"), "repositories")
    known = {repo["name"] for repo in repos}
    destinations = _policy_names(issue_repositories, known, "issue_repositories")
    if not destinations:
        raise ValueError("at least one issue destination is required")
    keep = _policy_names(keep_repositories, known, "keep_repositories")
    for repo in repos:
        _validate_fields(repo, observed, branch=False)
        if repo["name"] in destinations and repo.get("archived") is not False:
            raise ValueError("issue destinations must be confirmed unarchived")
        if repo.get("default_branch") is not None:
            _name(repo["default_branch"])
        if repo.get("branches") is not None:
            for branch in _named_rows(repo["branches"], "branches"):
                _validate_fields(branch, observed, branch=True)
        elif repo.get("branches_complete") is True:
            raise ValueError("branches_complete requires a branches list")
    results = [
        {
            "name": repo["name"],
            "consolidation": _consolidation(repo, cutoff, keep),
            "issue_routing": _issue_routing(repo, destinations),
            "branches": _branches(repo, cutoff),
        }
        for repo in sorted(repos, key=lambda item: item["name"])
    ]
    return {
        "observed_at": observed.isoformat(),
        "stale_before": cutoff.isoformat(),
        "issue_repositories": sorted(destinations),
        "keep_repositories": sorted(keep),
        "repositories": results,
        "summary": {
            "repositories": len(results),
            "consolidation_reviews": sum(
                repo["consolidation"]["status"] == "REVIEW_CONSOLIDATION"
                for repo in results
            ),
            "issue_routing_reviews": sum(
                repo["issue_routing"]["status"] == "REVIEW_ROUTING" for repo in results
            ),
            "branch_reviews": sum(
                branch["status"] == "REVIEW_DELETE"
                for repo in results
                for branch in repo["branches"]["items"]
            ),
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    """Render every check, including unknown evidence, with table-safe labels."""

    def cell(value: str) -> str:
        return html.escape(value).replace("|", "&#124;")

    lines = [
        "# Repository consolidation audit",
        "",
        f"Observed: {report['observed_at']}; stale before: {report['stale_before']}.",
        "",
        "Review statuses require maintainer decisions. No actions were executed.",
        "",
        "| Repository | Check | Status | Evidence |",
        "|---|---|---|---|",
    ]
    for repo in report["repositories"]:
        checks = [
            (field, repo[field])
            for field in ("consolidation", "issue_routing", "branches")
        ]
        checks.extend(
            ("branch: " + item["name"], item) for item in repo["branches"]["items"]
        )
        for label, check in checks:
            values = (repo["name"], label, check["status"], check["reason"])
            lines.append("| " + " | ".join(cell(value) for value in values) + " |")
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    """Read a snapshot and print a report; argparse handles invalid inputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "inventory", type=Path, help="Normalized JSON inventory snapshot"
    )
    parser.add_argument(
        "--stale-before", required=True, help="Timezone-aware ISO cutoff"
    )
    parser.add_argument(
        "--issue-repo",
        action="append",
        required=True,
        help="Permitted issue destination",
    )
    parser.add_argument(
        "--keep-repo", action="append", default=[], help="Repository to retain"
    )
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    args = parser.parse_args(argv)
    try:
        inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
        report = audit_inventory(
            inventory,
            stale_before=args.stale_before,
            issue_repositories=args.issue_repo,
            keep_repositories=args.keep_repo,
        )
    except OSError:
        parser.error("cannot read inventory file")
    except (ValueError, TypeError, UnicodeError) as error:
        parser.error(str(error))
    if args.format == "markdown":
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, sort_keys=True))  # JSON indentation only.
    return (
        0  # Successful report, including review findings; argparse errors exit with 2.
    )


if __name__ == "__main__":
    sys.exit(main())
