"""Portable knowledge vault contract; all examples use synthetic local notes.

Expected counts below are hand inventories, not values from the implementation.
Obsidian Help, "Manage vaults" (accessed 2026-10-20), establishes that an
existing folder of notes can be opened as a vault. The layout and status strings
are this utility's contract, documented in docs/modules/knowledge-management.md.
"""

import stat
from pathlib import Path

import pytest

from assetutilities.common.knowledge_management import (
    capture_note,
    check_setup,
    initialize_vault,
    search_notes,
)


def test_initialize_creates_portable_layout_and_is_idempotent(tmp_path):
    """Hand inventory: Home.md and Templates/Note.md are the only initial files."""
    root = tmp_path / "vault"
    created = initialize_vault(root)
    assert set(created) == {"Home.md", "Templates/Note.md"}
    assert {p.name for p in root.iterdir() if p.is_dir()} == {
        "Inbox",
        "Notes",
        "Templates",
        "Attachments",
    }
    assert not (root / ".obsidian").exists()
    original = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    assert initialize_vault(root) == ()
    assert {p: p.read_bytes() for p in original} == original


def test_initialize_preserves_user_files_and_settings(tmp_path):
    root = tmp_path / "vault"
    initialize_vault(root)
    (root / "Home.md").write_text("# My home\n", encoding="utf-8")
    (root / ".obsidian").mkdir()
    settings = root / ".obsidian" / "app.json"
    settings.write_text('{"user_setting":true}', encoding="utf-8")
    assert initialize_vault(root) == ()
    assert (root / "Home.md").read_text() == "# My home\n"
    assert settings.read_text() == '{"user_setting":true}'


@pytest.mark.parametrize("collision", ["home.md", "inbox"])
def test_initialize_rejects_case_only_layout_conflicts(tmp_path, collision):
    root = tmp_path / "vault"
    root.mkdir()
    (root / collision).write_text("preserve", encoding="utf-8")
    with pytest.raises(ValueError):
        initialize_vault(root)
    assert list(root.iterdir()) == [root / collision]


def test_initialize_repairs_missing_starter_without_replacing_notes(tmp_path):
    root = tmp_path / "vault"
    (root / "Notes").mkdir(parents=True)
    note = root / "Notes" / "existing.md"
    note.write_text("# Existing\n", encoding="utf-8")
    assert set(initialize_vault(root)) == {"Home.md", "Templates/Note.md"}
    assert note.read_text() == "# Existing\n"


@pytest.mark.parametrize("collision", ["Inbox", "Notes", "Templates", "Attachments"])
def test_initialize_preflights_directory_conflicts(tmp_path, collision):
    root = tmp_path / "vault"
    root.mkdir()
    (root / collision).write_text("keep", encoding="utf-8")
    with pytest.raises(ValueError):
        initialize_vault(root)
    assert list(root.iterdir()) == [root / collision]
    assert (root / collision).read_text() == "keep"


@pytest.mark.parametrize("collision", ["Home.md", "Templates/Note.md"])
def test_initialize_preflights_file_conflicts(tmp_path, collision):
    root = tmp_path / "vault"
    target = root / collision
    target.mkdir(parents=True)
    with pytest.raises(ValueError):
        initialize_vault(root)
    assert not (root / "Inbox").exists()


@pytest.mark.parametrize("target", [".", "Inbox", "Templates", "Home.md"])
def test_initialize_rejects_symlinks_without_writing_outside(tmp_path, target):
    outside = tmp_path / "outside"
    outside.mkdir()
    root = tmp_path / "vault"
    if target != ".":
        root.mkdir()
    (root if target == "." else root / target).symlink_to(
        outside, target_is_directory=True
    )
    with pytest.raises(ValueError):
        initialize_vault(root)
    assert list(outside.iterdir()) == []


def test_capture_requires_source_and_preserves_body(tmp_path):
    root = tmp_path / "vault"
    initialize_vault(root)
    path = capture_note(
        root,
        "link-basics",
        title="Link basics",
        body="    example\n",
        source="Local handbook",
    )
    assert path == "Inbox/note-link-basics.md"
    assert (
        root / path
    ).read_text() == "# Link basics\n\nSource: Local handbook\n\n    example\n"
    with pytest.raises(FileExistsError):
        capture_note(root, "link-basics", title="Other", body="other", source="Other")
    assert "other" not in (root / path).read_text()


def test_capture_prefix_makes_reserved_basename_portable(tmp_path):
    root = tmp_path / "vault"
    initialize_vault(root)
    assert (
        capture_note(root, "con", title="Console", body="Text", source="Reference")
        == "Inbox/note-con.md"
    )


@pytest.mark.parametrize(
    "slug",
    [
        "../escape",
        "a/b",
        r"a\b",
        "/absolute",
        "",
        "two words",
        "UPPER",
        ".hidden",
        "x.md",
        "x--y",
    ],
)
def test_capture_rejects_nonportable_slugs(tmp_path, slug):
    root = tmp_path / "vault"
    initialize_vault(root)
    with pytest.raises(ValueError):
        capture_note(root, slug, title="Title", body="Text", source="Reference")
    assert list((root / "Inbox").iterdir()) == []


@pytest.mark.parametrize(
    "field,value",
    [
        ("title", ""),
        ("title", "two\nlines"),
        ("title", "Title\rInjected"),
        ("title", "Title\u2028Injected"),
        ("source", ""),
        ("source", "two\nlines"),
        ("source", "Reference\u0085Injected"),
        ("source", " \t "),
        ("body", " \n "),
    ],
)
def test_capture_rejects_incomplete_note(tmp_path, field, value):
    root = tmp_path / "vault"
    initialize_vault(root)
    arguments = dict(title="Title", body="Text", source="Reference")
    arguments[field] = value
    with pytest.raises(ValueError):
        capture_note(root, "example", **arguments)
    assert list((root / "Inbox").iterdir()) == []


def test_capture_rejects_case_insensitive_collision(tmp_path):
    root = tmp_path / "vault"
    initialize_vault(root)
    existing = root / "Inbox" / "NOTE-EXAMPLE.MD"
    existing.write_text("preserve", encoding="utf-8")
    with pytest.raises(FileExistsError):
        capture_note(root, "example", title="Title", body="Text", source="Reference")
    assert existing.read_text() == "preserve"


def test_capture_rejects_symlink_destination(tmp_path):
    root = tmp_path / "vault"
    initialize_vault(root)
    outside = tmp_path / "outside.md"
    outside.write_text("preserve", encoding="utf-8")
    (root / "Inbox" / "note-example.md").symlink_to(outside)
    with pytest.raises(ValueError):
        capture_note(root, "example", title="Title", body="Text", source="Reference")
    assert outside.read_text() == "preserve"


def test_search_worked_example(tmp_path):
    """Hand calculation: two notes, one mentions 'backlinks'; therefore one match.

    Templates and Home are navigation, not captured knowledge. Matching source
    text also works; no text is passed to the expected-result calculation.
    """
    root = tmp_path / "vault"
    initialize_vault(root)
    capture_note(
        root,
        "link-basics",
        title="Link basics",
        body="Backlinks connect notes.",
        source="Local handbook",
    )
    capture_note(
        root,
        "review",
        title="Review checklist",
        body="Review captured notes.",
        source="Local checklist",
    )
    matches = search_notes(root, "BACKLINKS")
    assert [(n.path, n.title) for n in matches] == [
        ("Inbox/note-link-basics.md", "Link basics")
    ]
    assert [n.path for n in search_notes(root)] == [
        "Inbox/note-link-basics.md",
        "Inbox/note-review.md",
    ]
    assert [n.title for n in search_notes(root, "handbook")] == ["Link basics"]
    assert search_notes(root, "unmatched") == ()


def test_search_includes_nested_notes_unicode_and_filename_fallback(tmp_path):
    root = tmp_path / "vault"
    initialize_vault(root)
    nested = root / "Notes" / "Topic"
    nested.mkdir()
    (nested / "plain.MD").write_text("Straße\n", encoding="utf-8")
    (nested / "table.csv").write_text("not a note", encoding="utf-8")
    assert [(n.path, n.title) for n in search_notes(root, "STRASSE")] == [
        ("Notes/Topic/plain.MD", "plain")
    ]


def test_search_skips_hidden_files_and_symlinks(tmp_path):
    root = tmp_path / "vault"
    initialize_vault(root)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.md").write_text("not indexed", encoding="utf-8")
    (root / "Notes" / "linked").symlink_to(outside, target_is_directory=True)
    (root / "Notes" / "linked.md").symlink_to(outside / "secret.md")
    (root / "Notes" / ".hidden.md").write_text("not indexed", encoding="utf-8")
    hidden = root / "Notes" / ".hidden"
    hidden.mkdir()
    (hidden / "note.md").write_text("not indexed", encoding="utf-8")
    assert search_notes(root) == ()


def test_search_reports_unreadable_encoding(tmp_path):
    root = tmp_path / "vault"
    initialize_vault(root)
    (root / "Notes" / "invalid.md").write_bytes(b"\xff")
    with pytest.raises(ValueError, match="UTF-8"):
        search_notes(root)


def test_search_fails_on_read_error_instead_of_returning_partial_results(
    tmp_path, monkeypatch
):
    root = tmp_path / "vault"
    initialize_vault(root)
    (root / "Notes" / "readable.md").write_text("# Readable\n", encoding="utf-8")
    blocked = root / "Notes" / "unreadable.md"
    blocked.write_text("# Unreadable\n", encoding="utf-8")
    original = Path.read_text

    def read_text(path, *args, **kwargs):
        if path == blocked:
            raise PermissionError("Read denied")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read_text)
    with pytest.raises(PermissionError):
        search_notes(root)


@pytest.mark.parametrize("operation", ["capture", "search"])
def test_operations_require_initialized_vault(tmp_path, operation):
    root = tmp_path / "missing"
    with pytest.raises(ValueError):
        if operation == "capture":
            capture_note(
                root, "example", title="Title", body="Text", source="Reference"
            )
        else:
            search_notes(root)
    assert not root.exists()


def test_setup_missing_application_is_explicit(tmp_path, monkeypatch):
    root = tmp_path / "vault"
    initialize_vault(root)
    monkeypatch.setattr(
        "assetutilities.common.knowledge_management.shutil.which", lambda _: None
    )
    report = check_setup(root)
    assert report["vault"] == "READY"
    assert report["application"] == "NOT_FOUND"
    assert report["launch"] == "NOT_EVALUATED"
    assert report["sync"] == "NOT_EVALUATED"
    assert report["plugins"] == "NOT_EVALUATED"


def test_setup_only_checks_executable_presence(tmp_path, monkeypatch):
    root = tmp_path / "vault"
    initialize_vault(root)
    executable = tmp_path / "application"
    executable.write_text("Not a real application", encoding="utf-8")
    executable.chmod(executable.stat().st_mode | stat.S_IXUSR)
    report = check_setup(root, executable=executable)
    assert report["application"] == "FOUND"
    assert report["launch"] == "NOT_EVALUATED"
    monkeypatch.setattr(
        "assetutilities.common.knowledge_management.shutil.which",
        lambda _: str(executable),
    )
    assert check_setup(root)["application"] == "FOUND"


def test_setup_is_readonly_for_missing_vault_and_application(tmp_path):
    root = tmp_path / "missing"
    report = check_setup(root, executable=tmp_path / "absent")
    assert report["vault"] == "NOT_FOUND"
    assert report["application"] == "NOT_FOUND"
    assert not root.exists()


def test_setup_does_not_treat_bundle_directory_as_executable(tmp_path):
    root = tmp_path / "vault"
    initialize_vault(root)
    bundle = tmp_path / "application.app"
    bundle.mkdir()
    assert check_setup(root, executable=bundle)["application"] == "NOT_FOUND"


def test_setup_marks_invalid_vault(tmp_path):
    root = tmp_path / "invalid"
    root.mkdir()
    assert check_setup(root)["vault"] == "INVALID"
