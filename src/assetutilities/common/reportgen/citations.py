"""Document-local citation bindings; no private index access or standard text.

Field names and rendering follow issue #79 and the calc-citation contract.
These helpers validate document bindings, not the cited engineering basis.
"""

from typing import Any

from assetutilities.workflow_api import envelope

from .dom import Section

DISCLOSURE_TEXT = (
    "Citations in this report reference an internal engineering-standards index "
    "by code identifier and revision. The full text of each cited standard is "
    "not included and must be obtained from the respective publisher. This "
    "report does not reproduce copyrighted standard content."
)


def parse_references(config: dict) -> list[dict]:
    """Copy declared bindings, rejecting incomplete or ambiguous metadata."""
    references = config.get("references", [])
    if not isinstance(references, list):
        raise ValueError("references must be a list")
    parsed, seen = [], set()
    for index, entry in enumerate(references):
        label = f"references entry {index}"
        if not isinstance(entry, dict):
            raise ValueError(f"{label} must be a mapping")
        for key in ("code_id", "revision"):
            value = entry.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{label} requires nonempty string {key}")
        for key in ("publisher", "title", "source_sibling"):
            if key in entry and (
                not isinstance(entry[key], str) or not entry[key].strip()
            ):
                raise ValueError(f"{label} requires nonempty string {key}")
        for key in ("code_id", "publisher", "revision"):
            value = entry.get(key, "")
            if value and value.splitlines() != [value]:
                raise ValueError(f"{label} requires single-line {key}")
        if entry["code_id"] in seen:
            raise ValueError(f"Duplicate code_id in {label}")
        seen.add(entry["code_id"])
        parsed.append(
            {**entry, "source_sibling": entry.get("source_sibling", "generic")}
        )
    return parsed


def render_citation(para: dict, references: list[dict]) -> str:
    """Render [code revision §section p.page], requiring a document binding."""
    code_id = para.get("code_id")
    reference = next((r for r in references if r["code_id"] == code_id), None)
    if reference is None:
        raise ValueError("Unbound citation code_id; declare it in references")
    parts = [code_id, reference["revision"]]
    for key, prefix in (("section", "§"), ("page", "p.")):
        value = para.get(key)
        if value is not None and value != "":
            if isinstance(value, bool) or not isinstance(value, (str, int)):
                raise ValueError(f"Citation {key} must be text or an integer")
            parts.append(f"{prefix}{value}")
    return "[" + " ".join(parts) + "]"


def _table_section(name: str, headers: list[str], rows: list[list[Any]]) -> Section:
    def row(values):
        return "| " + " | ".join(str(v).replace("|", "\\|") for v in values) + " |"

    section = Section(name)
    section.paragraphs = [
        {
            "type": "markdown_table",
            "content": "\n".join(
                [row(headers), row(["---"] * len(headers))]
                + [row(values) for values in rows]
            ),
        }
    ]
    return section


def build_references_section(references: list[dict]) -> Section:
    """List public identifiers only; internal routing metadata is not rendered."""
    return _table_section(
        "References",
        ["Code", "Publisher", "Revision"],
        [[r["code_id"], r.get("publisher", ""), r["revision"]] for r in references],
    )


def build_disclosure_section() -> Section:
    section = Section("Disclosure")
    section.paragraphs = [{"type": "text", "content": DISCLOSURE_TEXT}]
    return section


def build_provenance_section(config: dict) -> Section:
    """Consume the shared provenance contract without exposing input paths."""
    version = envelope.code_version("assetutilities")
    return _table_section(
        "Provenance",
        ["Field", "Value"],
        [
            ["Package version", version["package_version"] or "unavailable"],
            ["Git SHA", version["git_sha"] or "unavailable"],
            ["Input sha256", envelope.input_hash(config)],
            ["Generated (UTC)", envelope.utc_now_iso()],
        ],
    )
