# Local knowledge management

The knowledge command creates a portable Markdown vault, captures notes with a
required source, searches note contents and inspects local setup. It provides a
reproducible starting point for issue #38. Application installation, video viewing
and synchronization remain manual follow-up work.

## Revision history

| Revision | Date | Change and reason |
|---|---|---|
| Initial | 2026-10-20 | Add local vault tools and an example to make setup repeatable. |

## Scope and basis

Obsidian Help describes a vault as a local folder and supports opening an existing
folder as a vault in [Manage vaults](https://help.obsidian.md/manage-vaults).
[Internal links](https://help.obsidian.md/links) documents Markdown links and
Wikilinks. The starter uses a Markdown link to its note template. Both sources
were accessed on 2026-10-20; these are living documents without edition numbers.

The folder names, note prefix, required source field and setup statuses below are
utility conventions. No engineering equations, empirical constants, package
version assumptions or numerical acceptance thresholds are used.

The two resources listed in the issue were opened on 2026-10-20:

- [Plugin overview](https://www.youtube.com/watch?v=cBm95iCcX2E): the description
  groups plugins by use, including capture and maintenance.
- [Knowledge organization walkthrough](https://www.youtube.com/watch?v=nJ660t5ku9A):
  the description lists folders, tags, links, templates and maps of content.

Only the public descriptions and chapter outlines were reviewed. Video content
was not viewed or transcribed. Neither resource establishes a required plugin
list or an installation requirement; selecting plugins remains a user decision.

## Commands

Run commands from a checkout with the package's existing dependencies available;
`PYTHONPATH=src` supports an uninstalled checkout. The new modules themselves use
only the standard library, but the existing `common` package initializer also
imports the package's data-validation dependencies.

```bash
PYTHONPATH=src python -m assetutilities.cli.knowledge --help
PYTHONPATH=src python -m assetutilities.cli.knowledge init ./knowledge-vault
PYTHONPATH=src python -m assetutilities.cli.knowledge doctor ./knowledge-vault
```

`init` creates these directories and starter files:

```text
knowledge-vault/
  Home.md
  Inbox/
  Notes/
  Templates/
    Note.md
  Attachments/
```

Existing regular files are preserved byte for byte. Repeating `init` creates only
missing starter files. Wrong file types, case-only name collisions and symlinks
at managed paths are rejected before initialization writes anything. An I/O error
can leave an incomplete layout; rerun after correcting the cause. Use a single
writer during initialization and capture. These local checks do not provide a
security boundary against concurrent filesystem changes.

`capture VAULT SLUG --title TITLE --body-file FILE --source REFERENCE` writes a
new UTF-8 file to `Inbox/note-SLUG.md`. The source can be a URL, publication
citation or other explicit reference; it is recorded, not fetched or verified.
Slugs consist of lowercase ASCII letters/digits separated by single hyphens.
A filename prefix avoids reserved device basenames. Existing names, including
case-only collisions, are never replaced. Title and source must each be a
nonempty single line. Body indentation is preserved; trailing whitespace is
normalized and a final newline is added. Source provenance and correctness
remain the author's responsibility.

`search VAULT [QUERY]` reads UTF-8 `.md` files recursively under `Inbox` and
`Notes`. It matches a case-insensitive substring anywhere in the note, including
its title and source. Results contain the relative path and first line starting
with `# `, falling back to the filename stem. An omitted or empty query lists all
notes. Paths are sorted, use forward slashes and are relative to the vault.
Hidden entries and symlinks are excluded. Home, templates, attachments and
Obsidian configuration are not indexed. Invalid UTF-8 or read errors fail the
search rather than silently returning an incomplete inventory. Markdown syntax,
links, tags and frontmatter are not interpreted.

`doctor VAULT [--executable FILE]` checks the starter layout and whether an
executable file is present, either the supplied file or `obsidian` on `PATH`.
It reports the operating system and architecture to support manual package
selection. It neither runs the file nor verifies its identity or version.

| Field | Status | Meaning |
|---|---|---|
| `vault` | `READY`, `NOT_FOUND`, `INVALID` | Starter layout present, absent or incomplete/unsafe. |
| `application` | `FOUND`, `NOT_FOUND` | Executable file present or absent; GUI functionality is unverified. |
| `launch`, `sync`, `plugins` | `NOT_EVALUATED` | Separate manual checks are required. |

Commands emit JSON. Exit status `0` means the operation completed, including a
completed inspection that reports missing setup. Status `1` means a filesystem
or validation error; argument usage errors use argparse's status `2`. These are
CLI conventions, not setup acceptance criteria. Errors omit absolute paths.
Application executable paths are not emitted by `doctor`.

## Worked example: inputs, method and answer

The synthetic inputs are
[`link-basics.md`](../../examples/workflows/knowledge_management/link-basics.md)
and [`review.md`](../../examples/workflows/knowledge_management/review.md).
Use a new folder for this example. The commands create files there; capture
intentionally refuses to replace a note when repeated.

```bash
PYTHONPATH=src python -m assetutilities.cli.knowledge init ./knowledge-vault
PYTHONPATH=src python -m assetutilities.cli.knowledge capture ./knowledge-vault link-basics --title 'Link basics' --body-file examples/workflows/knowledge_management/link-basics.md --source 'Synthetic example: link basics'
PYTHONPATH=src python -m assetutilities.cli.knowledge capture ./knowledge-vault review --title 'Review checklist' --body-file examples/workflows/knowledge_management/review.md --source 'Synthetic example: review checklist'
PYTHONPATH=src python -m assetutilities.cli.knowledge search ./knowledge-vault backlinks
```

Method: inspect the two input texts. The link-basics input contains “Backlinks”;
the review input, its title and its source do not. Case-insensitive matching
therefore selects only the link-basics note. This is a hand-enumerated result,
not a value calculated by the implementation. The expected answer is committed
as [`expected-search.json`](../../examples/workflows/knowledge_management/expected-search.json):

```json
{
  "notes": [
    {
      "path": "Inbox/note-link-basics.md",
      "title": "Link basics"
    }
  ]
}
```

The CLI integration test runs these captures with the committed input files and
compares the result with the independently written expected answer.

## Setup on each device

Follow the official [installation guide](https://help.obsidian.md/Getting+started/Download+and+install+Obsidian)
and [download page](https://obsidian.md/download) for the actual platform and
architecture. The guide was accessed on 2026-10-20. No installer, package manager,
application, community plugin or network service is invoked by these tools.

| Platform | Manual installation route in the official guide |
|---|---|
| Windows | Use the official installer and follow its prompts. |
| macOS | Use the official installer and place the app in Applications. |
| Linux | Choose the documented distribution format for the platform; check architecture availability on the download page. |
| Android or iOS | Use the platform store linked by the official guide. |

After installation, open the generated folder using Obsidian's **Open folder as
vault** action. Obsidian manages its own configuration. The utility does not
create or modify `.obsidian`. On desktop installations outside `PATH`, pass the
actual launcher file to `doctor --executable`; an application bundle directory
is not an executable file. The Python command is a desktop tool; it does not
run inside the mobile application.

On each device, manually confirm that the vault opens, the template link resolves
and a captured note can be found. Application launch and architecture support
have not been tested by this change. Cross-device installation cannot be claimed
from a local executable-presence check.

## Later slices

- View the complete videos and decide whether any optional plugins are needed.
- Install the application on each intended device and record local acceptance.
- Select and separately verify a synchronization and backup method before
  placing important notes in the vault. No sync or backup behavior is assumed.
- Define the issue's remaining unspecified requirements before expanding scope.

## Validation

Focused tests cover file preservation, initialization retries, type and case
conflicts, symlinks, path traversal, required source fields, literal search,
Unicode, setup status and CLI invocation. Expected file inventories and search
matches are independently enumerated in the test docstrings. Tests use temporary
folders and never launch an application or connect to a service.
