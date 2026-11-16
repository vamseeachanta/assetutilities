"""Order-preserving comparison of two lists of text identifiers."""

from pathlib import Path

import yaml


class TextAnalytics:
    def router(self, cfg):
        return self.get_subset_files(cfg)

    def get_subset_files(self, cfg):
        first, second = cfg["data"]["set1"], cfg["data"]["set2"]
        for values in (first, second):
            if not isinstance(values, list) or any(
                not isinstance(v, str) for v in values
            ):
                raise ValueError("each input set must be a list of strings")
        # Python 3.11, Set Types: intersection and difference use set membership.
        # Issue #91 implementation plan (2026-07-06): ordered, unique set results.
        left, right = set(first), set(second)
        report = {
            "common": list(dict.fromkeys(v for v in first if v in right)),
            "only_in_set1": list(dict.fromkeys(v for v in first if v not in right)),
            "only_in_set2": list(dict.fromkeys(v for v in second if v not in left)),
        }
        report["counts"] = {key: len(value) for key, value in report.items()}
        report["input_sizes"] = {"set1": len(first), "set2": len(second)}
        folder = Path(cfg["Analysis"]["result_folder"])
        folder.mkdir(parents=True, exist_ok=True)
        output = folder / "text_analytics_comparison.yml"
        output.write_text(yaml.safe_dump(report, sort_keys=False), encoding="utf-8")
        cfg["text_analytics"] = {**report, "output_file": str(output)}
        return cfg
