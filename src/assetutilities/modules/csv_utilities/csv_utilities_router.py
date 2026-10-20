"""Standalone CSV normalization, retaining the legacy txt_file input alias."""

from pathlib import Path

import pandas as pd
import yaml


class CSVUtilitiesRouter:
    def router(self, cfg):
        options = cfg["csv_utilities"]
        source = Path(options.get("input_file") or options["txt_file"])
        analysis = cfg["Analysis"]
        if not source.is_absolute():
            source = Path(analysis.get("analysis_root_folder", ".")) / source
        delimiter = options.get("delimiter", ",")
        encoding = options.get("encoding") or "utf-8"
        try:
            frame = pd.read_csv(
                source,
                encoding=encoding,
                delimiter=delimiter,
                nrows=options.get("nrows"),
            )
        except UnicodeDecodeError:
            if options.get("encoding"):
                raise
            # Issue #91 implementation plan (2026-07-06): UTF-8 then Latin-1.
            encoding = "latin-1"
            frame = pd.read_csv(
                source,
                encoding=encoding,
                delimiter=delimiter,
                nrows=options.get("nrows"),
            )
        folder = Path(analysis["result_folder"])
        folder.mkdir(parents=True, exist_ok=True)
        normalized = folder / f"{source.stem}_normalized.csv"
        summary_file = folder / f"{source.stem}_summary.yml"
        frame.to_csv(normalized, index=False, encoding="utf-8")
        summary = {
            "input_file": str(source),
            "encoding_used": encoding,
            "delimiter": delimiter,
            "n_rows": len(frame),
            "n_columns": len(frame.columns),
            "columns": frame.columns.tolist(),
        }
        summary_file.write_text(
            yaml.safe_dump(summary, sort_keys=False), encoding="utf-8"
        )
        options["results"] = {
            "normalized": str(normalized),
            "summary": str(summary_file),
        }
        return cfg
