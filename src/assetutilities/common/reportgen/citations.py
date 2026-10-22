"""Public citation metadata binding; no private content is read or resolved."""

import copy

from assetutilities.workflow_api import envelope

DISCLOSURE_TEXT = (
    "Citations in this report reference an internal engineering-standards index "
    "by code identifier and revision. The full text of each cited standard is "
    "not included and must be obtained from the respective publisher. This "
    "report does not reproduce copyrighted standard content."
)


def parse_references(config):
    """Validate opaque identifiers and editions, rejecting ambiguous bindings."""
    references = config.get("references", [])
    if not isinstance(references, list):
        raise ValueError("references must be a list")
    result, seen = [], set()
    for index, entry in enumerate(references):
        if not isinstance(entry, dict):
            raise ValueError(f"Reference {index} must be an object")
        item = {}
        for key in ("code_id", "revision", "publisher", "title", "source_sibling"):
            value = entry.get(key, "generic" if key == "source_sibling" else "")
            if not isinstance(value, str) or (
                key in ("code_id", "revision", "source_sibling") and not value.strip()
            ):
                raise ValueError(f"Reference {index} requires text for {key}")
            if any(char in value for char in ("\n", "\r", "|")):
                raise ValueError(f"Reference {index} contains a table delimiter")
            item[key] = value.strip()
        item["publisher"] = item["publisher"] or "Not supplied"
        if item["code_id"] in seen:
            raise ValueError(f"Duplicate reference {item['code_id']}")
        seen.add(item["code_id"])
        result.append(item)
    return result


def render_citation(paragraph, references):
    """Bind an inline identifier to exactly one declared revision."""
    identifier = paragraph.get("code_id")
    reference = next((r for r in references if r["code_id"] == identifier), None)
    if reference is None:
        raise ValueError(f"Unbound citation: {identifier}")
    parts = [identifier, reference["revision"]]
    for key, prefix in (("section", "§"), ("page", "p.")):
        if key in paragraph:
            value = paragraph[key]
            if not isinstance(value, (str, int)) or isinstance(value, bool):
                raise ValueError(f"Citation {key} must be text or an integer")
            text = str(value).strip()
            if not text:
                raise ValueError(f"Citation {key} must not be blank")
            if key == "page" and (not text.isdecimal() or int(text) <= 0):
                raise ValueError("Citation page must be a positive integer")
            parts.append(prefix + text)
    return "[" + " ".join(parts) + "]"


def appendix_sections(references, config):
    """Build legacy DOM appendices, reusing workflow provenance helpers."""
    from .dom import Section

    sections = []
    if references:
        section = Section("References")
        rows = ["| Code | Publisher | Revision |", "|---|---|---|"]
        rows += [
            f"| {r['code_id']} | {r['publisher']} | {r['revision']} |"
            for r in references
        ]
        section.paragraphs = [{"type": "markdown_table", "content": "\n".join(rows)}]
        disclosure = Section("Disclosure")
        disclosure.paragraphs = [{"type": "text", "content": DISCLOSURE_TEXT}]
        sections.extend((section, disclosure))
    flag = config.get("provenance")
    if (references and flag is not False) or flag is True:
        version = envelope.code_version("assetutilities")
        values = {
            "Package version": version["package_version"],
            "Git SHA": version["git_sha"],
            "Input sha256": envelope.input_hash(
                {key: value for key, value in config.items() if key != "important_paths"}
            ),
            "Generated (UTC)": envelope.utc_now_iso(),
        }
        section = Section("Provenance")
        table = ["| Field | Value |", "|---|---|"]
        table += [f"| {key} | {value} |" for key, value in values.items()]
        section.paragraphs = [{"type": "markdown_table", "content": "\n".join(table)}]
        sections.append(section)
    return sections


def bind_structured_report(report):
    """Bind structured Word/PDF blocks without changing revision metadata."""
    report = copy.deepcopy(report)
    references = parse_references(report)
    groups = (report.get("sections", []), report.get("appendices", []))
    if any(not isinstance(group, list) for group in groups):
        return report  # Preserve layout errors for the layout validator.
    for section in groups[0] + groups[1]:
        if not isinstance(section, dict):
            continue  # The layout validator reports malformed sections.
        subs = section.get("subsections", [])
        if not isinstance(subs, list):
            continue
        for item in [section, *subs]:
            if isinstance(item, dict) and isinstance(item.get("blocks"), list):
                item["blocks"] = [
                    render_citation(block, references)
                    if isinstance(block, dict) and block.get("type") == "citation"
                    else block
                    for block in item["blocks"]
                ]
    if references:
        section = next(
            (
                s
                for s in report.get("sections", [])
                if isinstance(s, dict) and s.get("name") == "References"
            ),
            None,
        )
        if section is not None and isinstance(section.get("blocks"), list):
            section["blocks"].extend(
                [
                    {
                        "type": "table",
                        "caption": "References used",
                        "columns": ["Code", "Publisher", "Revision"],
                        "rows": [
                            [
                                r["code_id"],
                                r["publisher"],
                                r["revision"],
                            ]
                            for r in references
                        ],
                    },
                    DISCLOSURE_TEXT,
                ]
            )
    return report
