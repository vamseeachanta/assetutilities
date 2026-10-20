"""Local, non-destructive Markdown vault operations.

Basis: Obsidian Help, "Manage vaults" and "Internal links", accessed 2026-10-20:
https://help.obsidian.md/manage-vaults
https://help.obsidian.md/links
The folder layout is a utility convention, not an Obsidian requirement.
"""

from __future__ import annotations

import os
import platform
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

INSTALL_GUIDE = "https://help.obsidian.md/Getting+started/Download+and+install+Obsidian"
_DIRECTORIES = ("Inbox", "Notes", "Templates", "Attachments")
_STARTER_FILES = {
    "Home.md": (
        "# Knowledge vault\n\n"
        "Capture notes in Inbox, then move reviewed notes to Notes.\n"
        "Record a source and connect related notes.\n\n"
        "[Note template](Templates/Note.md)\n"
    ),
    "Templates/Note.md": (
        "# {{title}}\n\nSource: {{source}}\n\n" "## Summary\n\n## Related notes\n"
    ),
}


@dataclass(frozen=True)
class Note:
    """Search metadata with a vault-relative path; note bodies stay local."""

    path: str
    title: str


def _check_path(path: Path, *, directory: bool) -> None:
    if path.is_symlink():
        raise ValueError("Managed vault paths must not be symbolic links")
    if path.exists() and (path.is_dir() if directory else path.is_file()):
        return
    if path.exists():
        raise ValueError("A managed vault path has the wrong file type")


def _check_case_collision(path: Path) -> None:
    if path.parent.is_dir():
        if any(
            item.name != path.name and item.name.casefold() == path.name.casefold()
            for item in path.parent.iterdir()
        ):
            raise ValueError(
                "A managed path differs from an existing name only in case"
            )


def _preflight(root: Path) -> None:
    _check_path(root, directory=True)
    for relative in _DIRECTORIES:
        target = root / relative
        _check_path(target, directory=True)
        _check_case_collision(target)
    for relative in _STARTER_FILES:
        target = root / relative
        _check_path(target, directory=False)
        _check_case_collision(target)


def _require_vault(root: Path) -> None:
    _preflight(root)
    if not root.is_dir() or not all(
        (root / relative).exists() for relative in (*_DIRECTORIES, *_STARTER_FILES)
    ):
        raise ValueError("An initialized vault is required; run init first")


def initialize_vault(vault: str | Path) -> tuple[str, ...]:
    """Create missing starter files, preserving every existing regular file.

    Predictable type/case/symlink conflicts are checked before any write. Files
    use exclusive creation. An I/O failure can leave a partial layout; retrying
    is safe. Use a single writer while initializing or capturing notes.
    """
    root = Path(vault)
    _preflight(root)
    root.mkdir(parents=True, exist_ok=True)
    for relative in _DIRECTORIES:
        (root / relative).mkdir(exist_ok=True)
    created = []
    for relative, content in _STARTER_FILES.items():
        target = root / relative
        if not target.exists():
            with target.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(content)
            created.append(relative)
    return tuple(created)


def _single_line(value: str, field: str) -> str:
    value = value.strip()
    if not value or "\x00" in value or value.splitlines() != [value]:
        raise ValueError(f"{field} must be a nonempty single line")
    return value


def capture_note(
    vault: str | Path,
    slug: str,
    *,
    title: str,
    body: str,
    source: str,
) -> str:
    """Capture a sourced note without overwriting another note.

    Slugs use ASCII lowercase words/digits separated by single hyphens.
    Prefixing filenames with 'note-' avoids reserved device basenames. This
    conservative naming policy is a utility convention, not a standards limit.
    """
    if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug) is None:
        raise ValueError("slug must use lowercase letters, digits and single hyphens")
    title = _single_line(title, "title")
    source = _single_line(source, "source")
    if not body.strip() or "\x00" in body:
        raise ValueError("body must contain nonempty text without null characters")
    root = Path(vault)
    _require_vault(root)
    relative = f"Inbox/note-{slug}.md"
    target = root / relative
    if target.is_symlink():
        raise ValueError("The note destination must not be a symbolic link")
    if any(
        item.name.casefold() == target.name.casefold()
        for item in target.parent.iterdir()
    ):
        raise FileExistsError("The note already exists")
    with target.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(f"# {title}\n\nSource: {source}\n\n{body.rstrip()}\n")
    return relative


def _walk_error(error: OSError) -> None:
    raise error


def search_notes(vault: str | Path, query: str = "") -> tuple[Note, ...]:
    """Search UTF-8 Markdown under Inbox and Notes, ordered by relative path.

    Case-insensitive substring matching includes the body and source. Empty
    queries list all notes. Hidden entries and symlinks are excluded. This is
    plain-text search, not a Markdown, link, frontmatter or attachment parser.
    """
    root = Path(vault)
    _require_vault(root)
    matches = []
    for folder in ("Inbox", "Notes"):
        for directory, directories, files in os.walk(
            root / folder, onerror=_walk_error
        ):
            parent = Path(directory)
            directories[:] = sorted(
                name
                for name in directories
                if not name.startswith(".") and not (parent / name).is_symlink()
            )
            for name in sorted(files):
                path = parent / name
                if (
                    name.startswith(".")
                    or path.suffix.lower() != ".md"
                    or path.is_symlink()
                ):
                    continue
                if not path.is_file():
                    continue
                try:
                    content = path.read_text(encoding="utf-8")
                except UnicodeError as error:
                    raise ValueError("Notes must contain UTF-8 text") from error
                if query.casefold() in content.casefold():
                    title = next(
                        (
                            line.removeprefix("# ").strip()
                            for line in content.splitlines()
                            if line.startswith("# ")
                        ),
                        path.stem,
                    )
                    matches.append(Note(path.relative_to(root).as_posix(), title))
    return tuple(sorted(matches, key=lambda note: note.path))


def check_setup(
    vault: str | Path, *, executable: str | Path | None = None
) -> dict[str, str]:
    """Inspect local setup without launching an app or changing files.

    FOUND means an executable file is present, not that its identity, version,
    dependencies or GUI have been verified. Specify a launcher file explicitly
    for installations not on PATH. Sync and plugins require separate checks.
    """
    root = Path(vault)
    if not root.exists() and not root.is_symlink():
        vault_status = "NOT_FOUND"
    else:
        try:
            _require_vault(root)
        except ValueError:
            vault_status = "INVALID"
        else:
            vault_status = "READY"
    candidate = str(executable) if executable is not None else shutil.which("obsidian")
    found = bool(
        candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK)
    )
    return {
        "platform": platform.system(),
        "architecture": platform.machine(),
        "vault": vault_status,
        "application": "FOUND" if found else "NOT_FOUND",
        "launch": "NOT_EVALUATED",
        "sync": "NOT_EVALUATED",
        "plugins": "NOT_EVALUATED",
        "installation_guide": INSTALL_GUIDE,
    }
