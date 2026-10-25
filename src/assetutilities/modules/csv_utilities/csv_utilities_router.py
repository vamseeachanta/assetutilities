"""Standalone path-based CSV normalization; zip helpers remain independent."""

from pathlib import Path

import pandas as pd
import yaml


class CSVUtilitiesRouter:
    def router(self, cfg):
        options = cfg["csv_utilities"]
        source_name = options.get("input_file") or options.get("txt_file")
        if not source_name:
            raise ValueError("csv_utilities requires input_file (or txt_file)")
        source = Path(source_name)
        if not source.is_absolute():
            source = (
                Path(
                    cfg["Analysis"].get(
                        "input_folder", cfg["Analysis"]["analysis_root_folder"]
                    )
                )
                / source
            )
        delimiter = options.get("delimiter", ",")
        encoding = options.get("encoding") or "utf-8"
        kwargs = {"sep": delimiter, "nrows": options.get("nrows")}
        # pandas read_csv API: encoding errors are strict by default; retry only
        # decoding errors, never parse errors or a missing file.
        try:
            frame = pd.read_csv(source, encoding=encoding, **kwargs)
        except UnicodeDecodeError:
            if options.get("encoding"):
                raise
            encoding = "latin1"
            frame = pd.read_csv(source, encoding=encoding, **kwargs)
        folder = Path(cfg["Analysis"]["result_folder"])
        folder.mkdir(parents=True, exist_ok=True)
        normalized = folder / f"{source.stem}_normalized.csv"
        summary_path = folder / f"{source.stem}_summary.yml"
        frame.to_csv(normalized, index=False, encoding="utf-8", lineterminator="\n")
        summary = {
            "input_file": source.as_posix(),
            "encoding_used": encoding,
            "delimiter": delimiter,
            "n_rows": len(frame),
            "n_columns": len(frame.columns),
            "columns": list(frame.columns),
        }
        summary_path.write_text(yaml.safe_dump(summary), encoding="utf-8", newline="\n")
        options["results"] = {
            "normalized_file": normalized.as_posix(),
            "summary_file": summary_path.as_posix(),
        }
        return cfg
