#!/usr/bin/env python3
"""Restore cold files from the content-addressed store using a public manifest."""

import argparse
import csv
import fnmatch
import hashlib
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

RESTORABLE = {"MOVE", "SHRINK-ORIGINAL"}
STORE = "data/assetutilities/blobs/sha256"


def valid_path(value):
    parts = PurePosixPath(value).parts
    if (
        not value
        or "\\" in value
        or value.startswith("/")
        or PureWindowsPath(value).drive
        or any(p in {".", ".."} for p in value.split("/"))
        or any(ord(c) < 32 for c in value)
        or not parts
    ):
        raise ValueError("Manifest contains an unsafe relative path")
    return value


def read_manifest(root):
    manifest = root / "data-manifest" / "MANIFEST.tsv"
    entries = []
    seen = set()
    with manifest.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(
            (line for line in stream if not line.startswith("#")), delimiter="\t"
        )
        if reader.fieldnames != [
            "path",
            "bytes",
            "sha256",
            "disposition",
            "blob",
            "redownloadable",
            "second_copy",
        ]:
            raise ValueError("Manifest columns do not match the fetch contract")
        for row in reader:
            if row["disposition"] not in RESTORABLE:
                continue
            path = valid_path(row["path"])
            if path in seen:
                raise ValueError("Manifest contains a duplicate restore path")
            seen.add(path)
            if not re.fullmatch(r"[0-9a-f]{64}", row["sha256"]):
                raise ValueError("Manifest digest is invalid")
            size = int(row["bytes"])
            if size < 0:
                raise ValueError("Manifest size must be nonnegative")
            if row["blob"] != blob_relative(row).removeprefix("data/assetutilities/"):
                raise ValueError(
                    "Manifest blob location does not match the store layout"
                )
            entries.append(dict(row, bytes=size))
    return entries


def select_entries(entries, patterns, all_files):
    if all_files:
        return entries
    result = []
    for pattern in patterns:
        matches = [row for row in entries if fnmatch.fnmatchcase(row["path"], pattern)]
        if not matches:
            raise ValueError(
                "No restorable manifest entries match the requested pattern"
            )
        for row in matches:
            if row not in result:
                result.append(row)
    return result


def git_environment():
    environment = os.environ.copy()
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE"):
        environment.pop(name, None)
    return environment


def tracked_paths(root):
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        env=git_environment(),
        capture_output=True,
        check=True,
    )
    return set(result.stdout.decode("utf-8").rstrip("\0").split("\0"))


def target_path(root, relative, tracked):
    if relative in tracked:
        raise ValueError("Refusing to overwrite a tracked file")
    target = root / relative
    for part in (target, *target.parents):
        if part == root:
            break
        if part.is_symlink():
            raise ValueError("Refusing a symlink in a restore path")
    if target.exists() and not target.is_file():
        raise ValueError("Restore destination is not a regular file")
    return target


def verify_file(path, row):
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    if size != row["bytes"] or digest.hexdigest() != row["sha256"]:
        raise ValueError("Restored file size or SHA-256 does not match the manifest")


def ssh_command(host, command):
    return ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", host, command]


def storage_route():
    location = os.environ.get("ACE_DATA_ROOT", "")
    if location and Path(location).is_dir() and os.access(location, os.R_OK):
        return "local", location, None
    host = os.environ.get("ACE_DATA_HOST", "")
    if not location or not host:
        return None
    if host.startswith("-") or not re.fullmatch(r"[A-Za-z0-9_.@:~-]+", host):
        raise ValueError("ACE_DATA_HOST is not a valid SSH destination")
    if any(ord(c) < 32 for c in location):
        raise ValueError("ACE_DATA_ROOT contains invalid control characters")
    try:
        result = subprocess.run(
            ssh_command(host, "test -d " + shlex.quote(location)),
            capture_output=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode:
        return None
    return "remote", location, host


def blob_relative(row):
    digest = row["sha256"]
    basename = PurePosixPath(row["path"]).name
    suffix = basename.rsplit(".", 1)[1].lower() if "." in basename[1:] else ""
    name = digest + ("." + suffix if suffix else "")
    return f"{STORE}/{digest[:2]}/{name}"


def copy_blob(route, row, output):
    mode, location, host = route
    relative = blob_relative(row)
    if mode == "local":
        with (Path(location) / relative).open("rb") as source:
            shutil.copyfileobj(source, output)
    else:
        source = str(PurePosixPath(location) / relative)
        result = subprocess.run(
            ssh_command(host, "cat -- " + shlex.quote(source)),
            stdout=output,
            stderr=subprocess.PIPE,
            timeout=120,
        )
        if result.returncode:
            raise ValueError("Remote blob could not be read")


def restore_file(route, row, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=target.parent, prefix=".fetch-", delete=False
        ) as output:
            temporary = Path(output.name)
            copy_blob(route, row, output)
        verify_file(temporary, row)
        os.replace(temporary, target)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("paths", nargs="*", help="Repo-relative paths or quoted globs")
    result.add_argument(
        "--all", action="store_true", help="Select every restorable file"
    )
    result.add_argument(
        "--list", action="store_true", help="List selected manifest entries"
    )
    result.add_argument(
        "--verify",
        action="store_true",
        help="Verify selected local files without restoring",
    )
    return result


def main(argv=None, repo_root=None):
    args = parser().parse_args(argv)
    root = (
        Path(repo_root)
        if repo_root is not None
        else Path(__file__).resolve().parents[1]
    )
    root = root.resolve()
    try:
        entries = read_manifest(root)
        if not args.paths and not (args.all or args.list):
            raise ValueError("Provide paths, --all, or --list")
        selected = select_entries(
            entries, args.paths, args.all or (args.list and not args.paths)
        )
        if args.list:
            for row in selected:
                print(
                    f"{row['path']}\t{row['bytes']}\t{row['sha256']}\t{row['disposition']}"
                )
            return 0
        route = None if args.verify else storage_route()
        if not args.verify and route is None:
            print(
                "Data store unavailable; set ACE_DATA_ROOT or ACE_DATA_HOST with ACE_DATA_ROOT. No files changed."
            )
            return 0
        tracked = tracked_paths(root)
        targets = [(row, target_path(root, row["path"], tracked)) for row in selected]
        if args.verify:
            for row, target in targets:
                verify_file(target, row)
            print(f"Verified {len(targets)} file(s).")
            return 0
        for row, target in targets:
            restore_file(route, row, target)
        print(f"Restored and verified {len(targets)} file(s).")
        return 0
    except (OSError, ValueError, subprocess.SubprocessError, KeyError) as error:
        print(f"Fetch failed: {error.__class__.__name__}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
