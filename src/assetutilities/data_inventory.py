"""Read-only, relative-path inventory for data consolidation planning."""

from __future__ import annotations

import argparse
import errno
import hashlib
import io
import json
import os
import stat
import sys
from collections import defaultdict
from pathlib import Path


def _signature(metadata: os.stat_result) -> tuple:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _sha256(path: Path, metadata: os.stat_result) -> str:
    """Stream SHA-256 using the standard-library I/O buffer size.

    Source: Python 3.11 documentation (2022), hashlib.sha256 and hash.update,
    https://docs.python.org/3.11/library/hashlib.html#hash-algorithms.
    """
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        if _signature(os.fstat(stream.fileno())) != _signature(metadata):
            raise OSError(errno.ESTALE, "file changed before hashing")
        for chunk in iter(lambda: stream.read(io.DEFAULT_BUFFER_SIZE), b""):
            digest.update(chunk)
        if _signature(os.fstat(stream.fileno())) != _signature(metadata):
            raise OSError(errno.ESTALE, "file changed during hashing")
    if _signature(path.lstat()) != _signature(metadata):
        raise OSError(errno.ESTALE, "file replaced during hashing")
    return digest.hexdigest()


def _duplicate_groups(files: list[dict]) -> list[dict]:
    groups = defaultdict(list)
    for item in files:
        groups[(item["size_bytes"], item["sha256"])].append(item["path"])
    return [
        {"size_bytes": size, "sha256": digest, "paths": paths}
        for (size, digest), paths in sorted(groups.items())
        if len(paths) > 1  # A duplicate group requires more than one file path.
    ]


def _error(root: Path, path: Path, exc: OSError) -> dict:
    """Retain relative location and error kind without system path messages."""
    return {
        "path": path.relative_to(root).as_posix(),
        "error": errno.errorcode.get(exc.errno, "IO_ERROR"),
    }


def _regular_files(root: Path, errors: list[dict], skipped: list[dict]):
    def onerror(exc):
        errors.append(_error(root, Path(exc.filename) if exc.filename else root, exc))

    # Python 3.11 os.walk documents onerror and followlinks=False:
    # https://docs.python.org/3.11/library/os.html#os.walk.
    for directory, directories, names in os.walk(
        root, onerror=onerror, followlinks=False
    ):
        for name in sorted(directories + names):
            path = Path(directory) / name
            try:
                metadata = path.lstat()
            except OSError as exc:
                errors.append(_error(root, path, exc))
                if name in directories:
                    directories.remove(name)
                continue
            if stat.S_ISREG(metadata.st_mode):
                yield path, metadata
            elif not stat.S_ISDIR(metadata.st_mode):
                skipped.append(
                    {
                        "path": path.relative_to(root).as_posix(),
                        "reason": (
                            "symlink"
                            if stat.S_ISLNK(metadata.st_mode)
                            else "special_file"
                        ),
                    }
                )
                if name in directories:
                    directories.remove(name)
        directories.sort()


def inventory(root: str | Path, *, hash_contents: bool = False) -> dict:
    """Count regular-file paths and their logical bytes below a directory.

    Byte basis: Python 3.11 documentation (2022), os.stat_result.st_size,
    https://docs.python.org/3.11/library/os.html#os.stat_result.st_size.
    The total is a sum of file lengths, not allocated disk space.
    """
    root = Path(root)
    try:
        valid_root = stat.S_ISDIR(root.lstat().st_mode)
    except OSError:
        valid_root = False
    if not valid_root:
        raise ValueError("input root must be an existing directory, not a symlink")
    files, errors, skipped = [], [], []
    for path, metadata in _regular_files(root, errors, skipped):
        item = {
            "path": path.relative_to(root).as_posix(),
            "size_bytes": metadata.st_size,
        }
        files.append(item)
        if hash_contents:
            try:
                item["sha256"] = _sha256(path, metadata)
            except OSError as exc:
                errors.append(_error(root, path, exc))
    files.sort(key=lambda item: item["path"])
    evaluated = hash_contents and not errors
    return {
        "status": "PARTIAL" if errors else "COMPLETE",
        "file_count": len(files),
        "logical_bytes": sum(item["size_bytes"] for item in files),
        "files": files,
        "duplicate_status": "EVALUATED" if evaluated else "NOT_EVALUATED",
        "duplicate_groups": _duplicate_groups(files) if evaluated else [],
        "errors": sorted(errors, key=lambda item: (item["path"], item["error"])),
        "skipped": sorted(skipped, key=lambda item: item["path"]),
    }


def main(argv: list[str] | None = None) -> int:
    """Emit JSON on stdout; leave report storage to the caller."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="Directory to inventory read-only")
    parser.add_argument("--hash", action="store_true", help="Hash file contents")
    args = parser.parse_args(argv)
    try:
        report = inventory(args.root, hash_contents=args.hash)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2  # Command-line input error convention, not an engineering limit.
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["status"] == "PARTIAL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
