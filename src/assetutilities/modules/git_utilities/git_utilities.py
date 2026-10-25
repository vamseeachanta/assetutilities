"""Repository status and history without YAML-driven repository mutations."""

from pathlib import Path

from git import Repo
import yaml


class GitUtilities:
    def router(self, cfg):
        # The issue's workflow contract chooses a short log, not an engineering
        # limit (issue 91, phase 2, PR C). Callers can supply max_count.
        max_count = cfg.get("max_count", 5)
        if (
            isinstance(max_count, bool)
            or not isinstance(max_count, int)
            or max_count < 0
        ):
            raise ValueError("max_count must be a non-negative integer")
        rows = []
        for entry in cfg["repos"]:
            path = Path(entry["io"])
            if not path.is_absolute():
                path = (
                    Path(
                        cfg["Analysis"].get(
                            "input_folder", cfg["Analysis"]["analysis_root_folder"]
                        )
                    )
                    / path
                )
            with (
                Repo(path, search_parent_directories=True) as repo,
                # Git environment documentation: GIT_OPTIONAL_LOCKS=0 prevents
                # status from refreshing the index as a side effect.
                repo.git.custom_environment(GIT_OPTIONAL_LOCKS="0"),
            ):
                valid = repo.head.is_valid()
                rows.append(
                    {
                        "input": Path(entry["io"]).as_posix(),
                        "current_branch": "DETACHED"
                        if repo.head.is_detached
                        else repo.active_branch.name,
                        "head": repo.head.commit.hexsha if valid else None,
                        "is_dirty": bool(
                            repo.git.status(porcelain=True, untracked_files="normal")
                        ),
                        "recent_commits": [
                            {"sha": commit.hexsha, "subject": commit.summary}
                            for commit in repo.iter_commits(max_count=max_count)
                        ]
                        if valid and max_count
                        else [],
                    }
                )
        report = {
            "repos": rows,
            "write_operations": "skipped: write operations not supported",
        }
        folder = Path(cfg["Analysis"]["result_folder"])
        folder.mkdir(parents=True, exist_ok=True)
        output = folder / "gitpython_report.yml"
        output.write_text(yaml.safe_dump(report), encoding="utf-8", newline="\n")
        cfg["gitpython"] = {**report, "output_file": output.as_posix()}
        return cfg
