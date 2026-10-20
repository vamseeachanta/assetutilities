"""Extract PDF text with PyPDF2; retain optional table-reader entry points."""

import json
import os
from pathlib import Path
import re

import PyPDF2


class ReadPDF:
    def read_pdf(self, cfg, file_index=None):
        files = cfg["files"]["from_pdf"]
        indices = range(len(files)) if file_index is None else [file_index]
        results = []
        used_names = set()
        for index in indices:
            entry = files[index]
            library = entry.get("package") or cfg.get("library", "tabula")
            if library == "PyPDF2":
                label = str(entry.get("label", f"file_{index + 1}"))
                slug = re.sub(r"[^A-Za-z0-9_-]+", "_", label).strip("_") or "file"
                name = slug
                suffix = 1
                while name in used_names:
                    suffix += 1
                    name = f"{slug}_{suffix}"
                used_names.add(name)
                results.append(self.from_pdf_PyPDF2(cfg, index, name))
            elif library in {"tabula", "camelot"}:
                method = (
                    self.from_pdf_tabula
                    if library == "tabula"
                    else self.from_pdf_camelot
                )
                # Table readers return DataFrames; never put these objects in cfg.
                tables = method(cfg, index)
                results.append(
                    {
                        "tables": [
                            json.loads(
                                (table.df if library == "camelot" else table).to_json(
                                    orient="records"
                                )
                            )
                            for table in tables
                        ]
                    }
                )
            else:
                raise KeyError("PDF parsing library not programmed")
        return results

    def from_pdf_tabula(self, cfg, file_index=0):
        import tabula

        return tabula.read_pdf(
            cfg["files"]["from_pdf"][file_index]["io"],
            pages=cfg["files"]["from_pdf"][file_index]["page"],
            multiple_tables=True,
        )

    def from_pdf_camelot(self, cfg, file_index=0):
        import camelot

        return camelot.read_pdf(
            cfg["files"]["from_pdf"][file_index]["io"],
            pages=cfg["files"]["from_pdf"][file_index]["page"],
            suppress_stdout=False,
        )

    def from_pdf_PyPDF2(self, cfg, file_index=0, output_name=None):
        entry = cfg["files"]["from_pdf"][file_index]
        source = Path(entry["io"])
        reader = PyPDF2.PdfReader(source)
        page = entry["page"]
        # Issue #91 implementation plan (2026-07-06): YAML pages are one-based.
        # PyPDF2 3.0.0, "Extract Text from a PDF": pages use zero-based indexing.
        if (
            isinstance(page, bool)
            or not isinstance(page, int)
            or not 1 <= page <= len(reader.pages)
        ):
            raise ValueError("page must be an integer within the PDF page range")
        text = reader.pages[page - 1].extract_text() or ""
        folder = Path(
            cfg.get("Analysis", {}).get("result_folder", source.parent / "results")
        )
        folder.mkdir(parents=True, exist_ok=True)
        label = str(entry.get("label", f"file_{file_index + 1}"))
        if output_name is None:
            output_name = re.sub(r"[^A-Za-z0-9_-]+", "_", label).strip("_") or "file"
        output = folder / f"read_pdf_{output_name}.txt"
        output.write_text(text, encoding="utf-8")
        return {
            "label": label,
            "page": page,
            "output_file": os.path.relpath(output),
            "n_chars": len(text),
        }
