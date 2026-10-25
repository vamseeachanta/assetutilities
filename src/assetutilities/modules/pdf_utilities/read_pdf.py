"""PDF extraction with serializable workflow results."""

import json
from pathlib import Path
import re

import PyPDF2


class ReadPDF:
    def read_pdf(self, cfg, file_index=None):
        entries = cfg["files"]["from_pdf"]
        indices = range(len(entries)) if file_index is None else [file_index]
        results = []
        for index in indices:
            library = entries[index].get("package") or cfg.get("library", "tabula")
            if library == "PyPDF2":
                result = self.from_pdf_PyPDF2(cfg, index)
            elif library == "tabula":
                result = [
                    json.loads(table.to_json(orient="records", date_format="iso"))
                    for table in self.from_pdf_tabula(cfg, index)
                ]
            elif library == "camelot":
                result = [
                    json.loads(table.df.to_json(orient="records", date_format="iso"))
                    for table in self.from_pdf_camelot(cfg, index)
                ]
            else:
                raise KeyError("PDF parsing library not programmed")
            results.append(result)
        return results

    def from_pdf_tabula(self, cfg, file_index=0):
        import tabula

        entry = cfg["files"]["from_pdf"][file_index]
        return tabula.read_pdf(entry["io"], pages=entry["page"], multiple_tables=True)

    def from_pdf_camelot(self, cfg, file_index=0):
        import camelot

        entry = cfg["files"]["from_pdf"][file_index]
        return camelot.read_pdf(entry["io"], pages=entry["page"], suppress_stdout=False)

    def from_pdf_PyPDF2(self, cfg, file_index=0):
        entry = cfg["files"]["from_pdf"][file_index]
        source = Path(entry["io"])
        reader = PyPDF2.PdfReader(source)
        page = entry["page"]
        # PyPDF2 3.0.0, "Extract Text from a PDF": pages uses zero-based indices.
        # YAML page positions remain one-based, as in the legacy PDF workflows.
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
        label = str(entry.get("label", source.stem))
        slug = re.sub(r"[^A-Za-z0-9_-]+", "_", label).strip("_") or "page"
        # Include the entry index so repeated labels cannot overwrite earlier text.
        output = folder / f"read_pdf_{slug}_{file_index}.txt"
        output.write_text(text, encoding="utf-8")
        return {
            "label": label,
            "page": page,
            "output_file": str(output),
            "n_chars": len(text),
        }
