"""Repository inspection without YAML-controlled write operations."""

from pathlib import Path

from git import Repo
import yaml


class GitUtilities:
    def router(self, cfg):
        analysis = cfg["Analysis"]
        root = Path(analysis.get("analysis_root_folder", "."))
        reports = []
        for entry in cfg["repos"]:
            source = Path(entry["io"])
            if not source.is_absolute():
                source = root / source
            with (
                Repo(source, search_parent_directories=True) as repo,
                repo.git.custom_environment(GIT_OPTIONAL_LOCKS="0"),
            ):
                valid_head = repo.head.is_valid()
                detached = valid_head and repo.head.is_detached
                # Issue #91 implementation plan (2026-07-06): at most five commits.
                commits = list(repo.iter_commits(max_count=5)) if valid_head else []
                reports.append(
                    {
                        "input": Path(entry["io"]).as_posix(),
                        "current_branch": "DETACHED"
                        if detached
                        else repo.active_branch.name,
                        "head": repo.head.commit.hexsha if valid_head else None,
                        "is_dirty": repo.is_dirty(untracked_files=True),
                        "recent_commits": [
                            {"sha": c.hexsha, "subject": c.summary} for c in commits
                        ],
                    }
                )
        # Legacy base configuration enables commit/push. These flags are never executed.
        report = {
            "repositories": reports,
            "write_operations": "skipped: write operations not supported",
        }
        folder = Path(analysis["result_folder"])
        folder.mkdir(parents=True, exist_ok=True)
        output = folder / "gitpython_report.yml"
        output.write_text(
            yaml.safe_dump(report, sort_keys=False), encoding="utf-8", newline="\n"
        )
        cfg["gitpython"] = {"output_file": output.as_posix(), **report}
        return cfg
